import re
import sqlite3

import pandas as pd

_VALID_TABLE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def execute_query(self, query: str):
        """Executes a SQL query and returns a Pandas DataFrame."""
        try:
            conn = sqlite3.connect(self.db_path)
            try:
                return pd.read_sql_query(query, conn)
            finally:
                conn.close()
        except Exception as e:
            return f"Error executing query: {e}"

    def get_schema(self):
        """Retrieves the schema (table names and columns) for the AI context."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
            tables = cursor.fetchall()

            schema_text = "Database Schema:\n"
            for table in tables:
                table_name = table[0]
                if not _VALID_TABLE.match(table_name):
                    continue
                schema_text += f"- Table: {table_name}\n  Columns: "
                cursor.execute(f'PRAGMA table_info("{table_name}");')
                columns = [col[1] for col in cursor.fetchall()]
                schema_text += ", ".join(columns) + "\n"

            return schema_text
        finally:
            conn.close()
