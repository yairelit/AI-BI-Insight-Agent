import os
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

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
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self.insight_model = insight_model or self.model
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI()
        return self._client

    def _chat(self, system: str, user: str, model: str) -> str:
        r = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        return (r.choices[0].message.content or "").strip()

    def generate_sql(self, question: str) -> str:
        schema = self.db.get_schema()
        system = SYSTEM_PROMPT.format(schema=schema)
        return self._chat(system, question, self.model)

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
            self.insight_model,
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
