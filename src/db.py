from __future__ import annotations

import sqlite3
from pathlib import Path
import pandas as pd

from .schema import load_schema
from .data_loader import numeric_keys

DB_PATH = Path(__file__).resolve().parent.parent / "student_data.db"


def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Initialize database and ensure table exists according to schema."""
    schema = load_schema()
    conn = sqlite3.connect(db_path)
    columns = []
    for field in schema.get("canonical_fields", []):
        key = field["key"]
        sql_type = "REAL" if key in numeric_keys else "TEXT"
        columns.append(f"{key} {sql_type}")
    cols_sql = ", ".join(["id INTEGER PRIMARY KEY AUTOINCREMENT"] + columns)
    conn.execute(f"CREATE TABLE IF NOT EXISTS records ({cols_sql});")
    conn.commit()
    return conn


def insert_dataframe(df: pd.DataFrame, conn: sqlite3.Connection) -> None:
    """Append a normalized DataFrame into the records table."""
    df.to_sql("records", conn, if_exists="append", index=False)


def load_records(conn: sqlite3.Connection, student_name: str | None = None) -> pd.DataFrame:
    """Load records from the database, optionally filtered by student name."""
    query = "SELECT * FROM records"
    params: tuple = ()
    if student_name:
        query += " WHERE student_name = ?"
        params = (student_name,)
    return pd.read_sql_query(query, conn, params=params)
