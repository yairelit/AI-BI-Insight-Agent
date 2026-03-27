import os
from typing import Any

import pandas as pd
from dotenv import load_dotenv
# מעבר ל-SDK החדש
from google import genai
from google.genai import types

from .database import DatabaseManager
from .prompts import INSIGHT_PROMPT, SYSTEM_PROMPT
from .utils import first_statement, is_safe_select, strip_sql_response

load_dotenv()

class BIAgent:
    """Loads schema, asks the model for SQL, runs it read-only, optionally summarizes results."""

    def __init__(
        self,
        db_path: str,
        model: str | None = None,
        insight_model: str | None = None,
    ):
        self.db = DatabaseManager(db_path)
        
        # Update to Gemini 2.0 Flash by default (removed the models/ prefix because the new Client adds it)
        default_model = os.environ.get("GOOGLE_MODEL", "gemini-2.0-flash")
        self.model_name = model or default_model
        self.insight_model_name = insight_model or self.model_name
        
        api_key = os.environ.get("GOOGLE_API_KEY")
        # יצירת ה-Client החדש במקום genai.configure
        self.client = genai.Client(api_key=api_key) if api_key else None

    def _chat(self, system: str, user: str, model_name: str) -> str:
        if not self.client:
            return "Error: API key not configured."

        # The new structure of sending a message with system instructions
        response = self.client.models.generate_content(
            model=model_name,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=0.2,
            )
        )
        return (response.text or "").strip()

    def generate_sql(self, question: str) -> str:
        schema = self.db.get_schema()
        system = SYSTEM_PROMPT.format(schema=schema)
        return self._chat(system, question, self.model_name)

    def summarize(
        self,
        question: str,
        sql: str,
        df: pd.DataFrame,
        max_rows: int = 15,
        max_chars: int = 6000,
    ) -> str:
        preview_df = df.head(max_rows)
        preview = preview_df.to_json(orient="records", date_format="iso")
        if len(preview) > max_chars:
            preview = preview[:max_chars] + "…"
        
        user = INSIGHT_PROMPT.format(
            question=question,
            sql=sql,
            max_rows=max_rows,
            preview=preview or "[]",
        )
        return self._chat(
            "You turn query results into concise business insights.",
            user,
            self.insight_model_name,
        )

    def ask(self, question: str, with_insight: bool = True) -> dict[str, Any]:
        raw = self.generate_sql(question)
        cleaned = strip_sql_response(raw)
        sql = first_statement(cleaned)

        if "don't have enough information" in cleaned.lower():
            return {
                "ok": True,
                "sql": None,
                "rows": None,
                "columns": None,
                "insight": cleaned,
                "error": None,
            }

        if not is_safe_select(sql):
            return {
                "ok": False,
                "sql": sql,
                "rows": None,
                "columns": None,
                "insight": None,
                "error": "Generated SQL did not pass read-only SELECT checks.",
            }

        result = self.db.execute_query(sql)
        if isinstance(result, str):
            return {
                "ok": False,
                "sql": sql,
                "rows": None,
                "columns": None,
                "insight": None,
                "error": result,
            }

        df = result
        payload: dict[str, Any] = {
            "ok": True,
            "sql": sql,
            "rows": df.to_dict(orient="records"),
            "columns": list(df.columns),
            "insight": None,
            "error": None,
        }
        if with_insight and not df.empty:
            payload["insight"] = self.summarize(question, sql, df)
        elif with_insight and df.empty:
            payload["insight"] = "The query returned no rows."
        return payload