import os
import re
import sqlite3
from pathlib import Path

_SQL_FENCE = re.compile(r"^\s*```(?:sql)?\s*", re.IGNORECASE)
_SQL_FENCE_END = re.compile(r"\s*```\s*$", re.IGNORECASE)

_DANGEROUS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|ATTACH|DETACH|CREATE|REPLACE|PRAGMA|VACUUM|TRUNCATE)\b",
    re.IGNORECASE,
)


def strip_sql_response(text: str) -> str:
    """Remove common markdown fences and surrounding whitespace from model output."""
    if not text:
        return ""
    s = text.strip()
    s = _SQL_FENCE.sub("", s)
    s = _SQL_FENCE_END.sub("", s)
    return s.strip()


def first_statement(sql: str) -> str:
    """Use only the first statement if the model returned multiple."""
    s = sql.strip()
    if ";" in s:
        s = s.split(";", 1)[0].strip()
    return s


def is_safe_select(sql: str) -> bool:
    """Allow a single SELECT-only query for read-only BI use."""
    q = first_statement(sql).strip()
    if not q:
        return False
    if not q.upper().startswith("SELECT"):
        return False
    if _DANGEROUS.search(q):
        return False
    return True


def ensure_sample_database(db_path: str) -> None:
    """Create a tiny SQLite DB with demo sales data if the file does not exist."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(
            """
            CREATE TABLE sales (
                id INTEGER PRIMARY KEY,
                region TEXT NOT NULL,
                product TEXT NOT NULL,
                sale_date TEXT NOT NULL,
                amount REAL NOT NULL
            );
            INSERT INTO sales (region, product, sale_date, amount) VALUES
                ('North', 'Widget A', '2024-01-15', 1200.0),
                ('North', 'Widget B', '2024-02-10', 800.5),
                ('South', 'Widget A', '2024-01-20', 950.0),
                ('South', 'Widget C', '2024-03-01', 2100.75),
                ('East', 'Widget B', '2024-02-28', 640.0),
                ('West', 'Widget A', '2024-03-15', 1100.0);
            """
        )
        conn.commit()
    finally:
        conn.close()


def default_db_path() -> str:
    return os.environ.get("BI_DB_PATH", str(Path(__file__).resolve().parents[1] / "data" / "sample.db"))
