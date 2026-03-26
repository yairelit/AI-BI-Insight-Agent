import os
import sys
import tempfile
import unittest
from pathlib import Path


# Ensure `src` is importable when running `python -m unittest`.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.agent import BIAgent
from src.database import DatabaseManager
from src.utils import ensure_sample_database, is_safe_select, strip_sql_response, first_statement


class BasicBIETest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp_dir.name) / "test.db")
        ensure_sample_database(self.db_path)
        self.db = DatabaseManager(self.db_path)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_utils_sql_sanitization(self) -> None:
        raw = "```sql\nSELECT * FROM sales;\n```"
        cleaned = strip_sql_response(raw)
        self.assertTrue(cleaned.upper().startswith("SELECT"))

        first = first_statement(cleaned)
        self.assertEqual(first, "SELECT * FROM sales")
        self.assertTrue(is_safe_select(first))

    def test_database_schema_contains_sales(self) -> None:
        schema = self.db.get_schema()
        self.assertIn("Table: sales", schema)
        self.assertIn("Columns:", schema)
        # A known column from the demo schema.
        self.assertIn("amount", schema.lower())

    def test_agent_ask_success_without_insight(self) -> None:
        agent = BIAgent(self.db_path, model="test-model")

        def fake_chat(system: str, user: str, model: str) -> str:
            # Return a single SELECT query only.
            return (
                "SELECT region, SUM(amount) AS total_amount "
                "FROM sales GROUP BY region ORDER BY total_amount DESC"
            )

        agent._chat = fake_chat  # type: ignore[method-assign]

        out = agent.ask("What are total sales by region?", with_insight=False)
        self.assertTrue(out["ok"])
        self.assertIsNotNone(out["sql"])
        self.assertIn("region", out["columns"])
        self.assertIn("total_amount", out["columns"])
        self.assertIsInstance(out["rows"], list)
        self.assertGreater(len(out["rows"]), 0)

    def test_agent_ask_unsafe_sql_is_rejected(self) -> None:
        agent = BIAgent(self.db_path, model="test-model")

        def fake_chat(system: str, user: str, model: str) -> str:
            return "DROP TABLE sales;"

        agent._chat = fake_chat  # type: ignore[method-assign]

        out = agent.ask("Delete the sales table.", with_insight=False)
        self.assertFalse(out["ok"])
        self.assertIn("DROP", (out.get("sql") or "").upper())
        self.assertIsNotNone(out.get("error"))

    def test_agent_ask_insufficient_information(self) -> None:
        agent = BIAgent(self.db_path, model="test-model")

        def fake_chat(system: str, user: str, model: str) -> str:
            return "I don't have enough information."

        agent._chat = fake_chat  # type: ignore[method-assign]

        out = agent.ask("Ask something not answerable.", with_insight=False)
        self.assertTrue(out["ok"])
        self.assertIsNone(out["sql"])
        self.assertIsNone(out["rows"])
        self.assertIsNotNone(out["insight"])
        self.assertIn("enough information", out["insight"].lower())


if __name__ == "__main__":
    unittest.main()