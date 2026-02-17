"""
Telemetry exporter for the Steering Assistant v02.

This module provides the TelemetryExporter class for exporting file-based
telemetry data to a database format (SQLite/PostgreSQL) for advanced analytics.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class TelemetryExporter:
    """Exports file-based telemetry data to a database."""

    def __init__(
        self,
        telemetry_dir: Path = Path(".kiro/.telemetry"),
        db_path: Optional[Path] = None,
    ):
        """
        Initialize the TelemetryExporter.

        Args:
            telemetry_dir: Directory containing file-based telemetry data
            db_path: Path to the database file (default: telemetry_dir / telemetry.db)
        """
        self.telemetry_dir = telemetry_dir
        self.db_path = db_path or self.telemetry_dir / "telemetry.db"
        self._connection: Optional[sqlite3.Connection] = None

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(str(self.db_path))
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def close(self) -> None:
        """Close the database connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> "TelemetryExporter":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

    def migrate_schema(self) -> None:
        """
        Create or migrate the database schema.

        Creates the following tables:
        - sessions: Main session data
        - confidence_scores: Per-file confidence scores
        - validation_results: Validation results per file
        - token_usage: Token usage per file
        - errors: Error records
        - user_interactions: User interaction records
        - durations: Operation durations
        - summary: Aggregated summary statistics
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                timestamp TEXT NOT NULL,
                workflow_type TEXT NOT NULL,
                project_root TEXT,
                files_count INTEGER DEFAULT 0,
                files_processed INTEGER DEFAULT 0,
                files_failed INTEGER DEFAULT 0,
                total_token_usage INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create confidence_scores table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS confidence_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                file_name TEXT NOT NULL,
                scores TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        # Create validation_results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS validation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                file_name TEXT NOT NULL,
                results TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        # Create token_usage table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                file_name TEXT NOT NULL,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        # Create errors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TEXT,
                error_type TEXT,
                message TEXT,
                file_name TEXT,
                context TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        # Create user_interactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TEXT,
                interaction_type TEXT,
                details TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        # Create durations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS durations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                operation TEXT,
                duration_ms REAL,
                file_name TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        # Create summary table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_sessions INTEGER DEFAULT 0,
                total_files_processed INTEGER DEFAULT 0,
                total_files_failed INTEGER DEFAULT 0,
                total_token_usage INTEGER DEFAULT 0,
                autonomous_sessions INTEGER DEFAULT 0,
                fallback_sessions INTEGER DEFAULT 0,
                last_updated TEXT
            )
        """)

        conn.commit()

    def export_to_database(self, clear_existing: bool = False) -> Dict[str, Any]:
        """
        Export file-based telemetry data to the database.

        Args:
            clear_existing: If True, clear existing data before exporting

        Returns:
            Dictionary with export statistics
        """
        self.migrate_schema()

        conn = self._get_connection()
        cursor = conn.cursor()

        if clear_existing:
            cursor.execute("DELETE FROM confidence_scores")
            cursor.execute("DELETE FROM validation_results")
            cursor.execute("DELETE FROM token_usage")
            cursor.execute("DELETE FROM errors")
            cursor.execute("DELETE FROM user_interactions")
            cursor.execute("DELETE FROM durations")
            cursor.execute("DELETE FROM sessions")
            cursor.execute("DELETE FROM summary")
            conn.commit()

        sessions_dir = self.telemetry_dir / "sessions"
        summary_path = self.telemetry_dir / "summary.json"

        stats = {
            "sessions_exported": 0,
            "confidence_scores_exported": 0,
            "validation_results_exported": 0,
            "token_usage_exported": 0,
            "errors_exported": 0,
            "user_interactions_exported": 0,
            "durations_exported": 0,
        }

        # Export session files
        if sessions_dir.exists():
            for session_file in sorted(sessions_dir.glob("*.json")):
                try:
                    with open(session_file, "r") as f:
                        session_data = json.load(f)

                    self._insert_session(cursor, session_data)
                    stats["sessions_exported"] += 1
                    stats["confidence_scores_exported"] += len(
                        session_data.get("confidence_scores", [])
                    )
                    stats["validation_results_exported"] += len(
                        session_data.get("validation_results", [])
                    )
                    stats["token_usage_exported"] += len(
                        session_data.get("token_usage", {}).get("per_file", [])
                    )
                    stats["errors_exported"] += len(session_data.get("errors", []))
                    stats["user_interactions_exported"] += len(
                        session_data.get("user_interactions", [])
                    )
                    stats["durations_exported"] += len(
                        session_data.get("durations_ms", [])
                    )
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Warning: Failed to export session {session_file}: {e}")

        # Export summary file
        if summary_path.exists():
            try:
                with open(summary_path, "r") as f:
                    summary_data = json.load(f)
                self._insert_summary(cursor, summary_data)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Failed to export summary: {e}")

        conn.commit()
        return stats

    def _insert_session(self, cursor: sqlite3.Cursor, session_data: Dict[str, Any]) -> None:
        """Insert a session record into the database."""
        cursor.execute(
            """
            INSERT OR REPLACE INTO sessions (
                session_id, timestamp, workflow_type, project_root,
                files_count, files_processed, files_failed, total_token_usage
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_data.get("session_id"),
                session_data.get("timestamp"),
                session_data.get("workflow_type"),
                session_data.get("project_root"),
                session_data.get("files_count", 0),
                session_data.get("files_processed", 0),
                session_data.get("files_failed", 0),
                session_data.get("token_usage", {}).get("total", 0),
            ),
        )

        session_id = session_data.get("session_id")

        # Insert confidence scores
        for cs in session_data.get("confidence_scores", []):
            cursor.execute(
                """
                INSERT INTO confidence_scores (session_id, file_name, scores)
                VALUES (?, ?, ?)
                """,
                (session_id, cs.get("file"), json.dumps(cs.get("scores", []))),
            )

        # Insert validation results
        for vr in session_data.get("validation_results", []):
            cursor.execute(
                """
                INSERT INTO validation_results (session_id, file_name, results)
                VALUES (?, ?, ?)
                """,
                (session_id, vr.get("file"), json.dumps(vr.get("results", {}))),
            )

        # Insert token usage
        for tu in session_data.get("token_usage", {}).get("per_file", []):
            cursor.execute(
                """
                INSERT INTO token_usage (
                    session_id, file_name, prompt_tokens, completion_tokens, total_tokens
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    tu.get("file"),
                    tu.get("prompt_tokens", 0),
                    tu.get("completion_tokens", 0),
                    tu.get("total_tokens", 0),
                ),
            )

        # Insert errors
        for err in session_data.get("errors", []):
            cursor.execute(
                """
                INSERT INTO errors (
                    session_id, timestamp, error_type, message, file_name, context
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    err.get("timestamp"),
                    err.get("error_type"),
                    err.get("message"),
                    err.get("file"),
                    json.dumps(err.get("context", {})),
                ),
            )

        # Insert user interactions
        for ui in session_data.get("user_interactions", []):
            cursor.execute(
                """
                INSERT INTO user_interactions (
                    session_id, timestamp, interaction_type, details
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    session_id,
                    ui.get("timestamp"),
                    ui.get("interaction_type"),
                    json.dumps(ui.get("details", {})),
                ),
            )

        # Insert durations
        for dur in session_data.get("durations_ms", []):
            cursor.execute(
                """
                INSERT INTO durations (session_id, operation, duration_ms, file_name)
                VALUES (?, ?, ?, ?)
                """,
                (
                    session_id,
                    dur.get("operation"),
                    dur.get("duration_ms", 0),
                    dur.get("file"),
                ),
            )

    def _insert_summary(self, cursor: sqlite3.Cursor, summary_data: Dict[str, Any]) -> None:
        """Insert or update the summary record."""
        cursor.execute(
            """
            INSERT OR REPLACE INTO summary (
                id, total_sessions, total_files_processed, total_files_failed,
                total_token_usage, autonomous_sessions, fallback_sessions, last_updated
            ) VALUES (1, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                summary_data.get("total_sessions", 0),
                summary_data.get("total_files_processed", 0),
                summary_data.get("total_files_failed", 0),
                summary_data.get("total_token_usage", 0),
                summary_data.get("autonomous_sessions", 0),
                summary_data.get("fallback_sessions", 0),
                datetime.now().isoformat(),
            ),
        )

    def query_sessions(
        self,
        workflow_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Query sessions from the database.

        Args:
            workflow_type: Filter by workflow type (AUTONOMOUS or FALLBACK)
            limit: Maximum number of results

        Returns:
            List of session records
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM sessions"
        params = []

        if workflow_type:
            query += " WHERE workflow_type = ?"
            params.append(workflow_type)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get aggregated statistics from the database.

        Returns:
            Dictionary with aggregated statistics
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {}

        cursor.execute("SELECT COUNT(*) FROM sessions")
        stats["total_sessions"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM sessions WHERE workflow_type = 'AUTONOMOUS'")
        stats["autonomous_sessions"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM sessions WHERE workflow_type = 'FALLBACK'")
        stats["fallback_sessions"] = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(total_token_usage) FROM sessions")
        stats["total_token_usage"] = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(files_processed) FROM sessions")
        stats["total_files_processed"] = cursor.fetchone()[0] or 0

        cursor.execute("SELECT AVG(total_token_usage) FROM sessions WHERE total_token_usage > 0")
        stats["avg_token_usage"] = cursor.fetchone()[0] or 0

        return stats

    def export_to_postgres_format(self) -> Dict[str, str]:
        """
        Get SQL statements for PostgreSQL export.

        Returns:
            Dictionary with CREATE TABLE and INSERT statements for PostgreSQL
        """
        sql_statements = {
            "sessions": """
                CREATE TABLE sessions (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT UNIQUE NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    workflow_type TEXT NOT NULL,
                    project_root TEXT,
                    files_count INTEGER DEFAULT 0,
                    files_processed INTEGER DEFAULT 0,
                    files_failed INTEGER DEFAULT 0,
                    total_token_usage INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "confidence_scores": """
                CREATE TABLE confidence_scores (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES sessions(session_id),
                    file_name TEXT NOT NULL,
                    scores JSONB
                )
            """,
            "validation_results": """
                CREATE TABLE validation_results (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES sessions(session_id),
                    file_name TEXT NOT NULL,
                    results JSONB
                )
            """,
            "token_usage": """
                CREATE TABLE token_usage (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES sessions(session_id),
                    file_name TEXT NOT NULL,
                    prompt_tokens INTEGER DEFAULT 0,
                    completion_tokens INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0
                )
            """,
            "errors": """
                CREATE TABLE errors (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES sessions(session_id),
                    timestamp TIMESTAMP,
                    error_type TEXT,
                    message TEXT,
                    file_name TEXT,
                    context JSONB
                )
            """,
            "user_interactions": """
                CREATE TABLE user_interactions (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES sessions(session_id),
                    timestamp TIMESTAMP,
                    interaction_type TEXT,
                    details JSONB
                )
            """,
            "durations": """
                CREATE TABLE durations (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES sessions(session_id),
                    operation TEXT,
                    duration_ms REAL,
                    file_name TEXT
                )
            """,
            "summary": """
                CREATE TABLE summary (
                    id SERIAL PRIMARY KEY,
                    total_sessions INTEGER DEFAULT 0,
                    total_files_processed INTEGER DEFAULT 0,
                    total_files_failed INTEGER DEFAULT 0,
                    total_token_usage INTEGER DEFAULT 0,
                    autonomous_sessions INTEGER DEFAULT 0,
                    fallback_sessions INTEGER DEFAULT 0,
                    last_updated TIMESTAMP
                )
            """,
        }

        return sql_statements