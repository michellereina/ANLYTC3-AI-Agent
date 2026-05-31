import sqlite3
from datetime import datetime
from pathlib import Path


DB_NAME = "testpilot.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS test_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT NOT NULL,
                agent_output TEXT NOT NULL,
                selected_files TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def save_report(user_input, agent_output, selected_files=""):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO test_reports (
                user_input,
                agent_output,
                selected_files,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (user_input, agent_output, selected_files, datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()


def get_reports():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, user_input, agent_output, selected_files, created_at
            FROM test_reports
            ORDER BY id DESC
            """
        )
        return cursor.fetchall()


def reset_generated_artifacts():
    for folder in ("generated_tests", "uploaded_projects"):
        path = Path(folder)
        path.mkdir(exist_ok=True)
