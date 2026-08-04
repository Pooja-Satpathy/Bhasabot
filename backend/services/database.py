"""
Database Service - SQLite setup, user management, and session tracking
Manages users and their PDF upload sessions in a local SQLite file database.
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "bhashabot.db")


def get_db_connection() -> sqlite3.Connection:
    """
    Establish a connection to the SQLite database.
    Enables foreign keys and Row factory for dictionary-like access.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enforce foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """
    Initialize SQLite tables for users and their document sessions.
    Runs at backend startup. Drops and recreates tables if columns are missing.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the users table already exists and check its columns
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    table_exists = cursor.fetchone()

    if table_exists:
        cursor.execute("PRAGMA table_info(users);")
        columns = [row["name"] for row in cursor.fetchall()]
        # Schema requires both 'username' AND 'email'
        if "username" not in columns or "email" not in columns:
            print("⚠️ Old schema detected. Dropping old tables to recreate...")
            cursor.execute("DROP TABLE IF EXISTS user_sessions;")
            cursor.execute("DROP TABLE IF EXISTS users;")
            conn.commit()

    # Create users table (using unique username and unique email)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create user_sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            chunks_stored INTEGER NOT NULL,
            file_hash TEXT,
            document_version INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    cursor.execute("PRAGMA table_info(user_sessions);")
    session_columns = [row["name"] for row in cursor.fetchall()]
    if "file_hash" not in session_columns:
        cursor.execute("ALTER TABLE user_sessions ADD COLUMN file_hash TEXT;")
    if "document_version" not in session_columns:
        cursor.execute(
            "ALTER TABLE user_sessions ADD COLUMN document_version INTEGER NOT NULL DEFAULT 1;"
        )

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_hash ON user_sessions (user_id, file_hash);"
    )

    conn.commit()
    conn.close()
    print("Database tables initialized successfully.")


def create_user(username: str, email: str, password_hash: str) -> int:
    """
    Insert a new user into the database, validating uniqueness.

    Args:
        username: The unique username
        email: The unique email address
        password_hash: Hashed password string

    Returns:
        The ID of the newly created user
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    clean_username = username.strip().lower()
    clean_email = email.strip().lower()

    # Check for duplicate username using a normalized, case-insensitive comparison
    cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?", (clean_username,))
    if cursor.fetchone():
        conn.close()
        raise ValueError("Username already exists")

    # Check for duplicate email
    cursor.execute("SELECT id FROM users WHERE email = ?", (clean_email,))
    if cursor.fetchone():
        conn.close()
        raise ValueError("Email already exists")

    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (clean_username, clean_email, password_hash),
        )
        conn.commit()
        user_id = cursor.lastrowid
        return user_id
    finally:
        conn.close()


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a user record by username.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    normalized_username = username.strip().lower()
    cursor.execute(
        "SELECT id, username, email, password_hash, created_at FROM users WHERE LOWER(username) = ?",
        (normalized_username,),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a user record by email.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, email, password_hash, created_at FROM users WHERE email = ?",
        (email.strip().lower(),),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a user record by primary key ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, email, created_at FROM users WHERE id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def save_user_session(
    session_id: str,
    user_id: int,
    filename: str,
    chunks_stored: int,
    file_hash: Optional[str] = None,
    document_version: int = 1,
) -> None:
    """
    Save or update a document upload session and link it to a user.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO user_sessions
            (session_id, user_id, filename, chunks_stored, file_hash, document_version)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            user_id,
            filename,
            chunks_stored,
            file_hash,
            document_version,
        ),
    )
    conn.commit()
    conn.close()


def get_legacy_session_by_filename(
    user_id: int, filename: str
) -> Optional[Dict[str, Any]]:
    """Find an old pre-hash session with the same filename."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT session_id, user_id, filename, chunks_stored,
               document_version, created_at
        FROM user_sessions
        WHERE user_id = ? AND filename = ? AND file_hash IS NULL
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (user_id, filename),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_session_by_hash(user_id: int, file_hash: str) -> Optional[Dict[str, Any]]:
    """Return the newest existing session for identical document bytes."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT session_id, user_id, filename, chunks_stored,
               document_version, created_at
        FROM user_sessions
        WHERE user_id = ? AND file_hash = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (user_id, file_hash),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_next_document_version(
    user_id: int, file_hash: str, filename: str
) -> int:
    """Return the next processing version for this document."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT COALESCE(MAX(document_version), 0) AS max_version
        FROM user_sessions
        WHERE user_id = ?
          AND (file_hash = ? OR (file_hash IS NULL AND filename = ?))
        """,
        (user_id, file_hash, filename),
    )
    row = cursor.fetchone()
    conn.close()
    return int(row["max_version"]) + 1


def get_user_sessions(user_id: int) -> List[Dict[str, Any]]:
    """
    Get all active sessions/uploads for a specific user, sorted from newest to oldest.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT session_id, filename, chunks_stored, document_version, created_at 
        FROM user_sessions 
        WHERE user_id = ? 
        ORDER BY created_at DESC
        """,
        (user_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_session_by_id(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve details of a session by ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT session_id, user_id, filename, chunks_stored, created_at FROM user_sessions WHERE session_id = ?",
        (session_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_user_session(session_id: str, user_id: int) -> bool:
    """
    Delete a document session belonging to a specific user.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM user_sessions WHERE session_id = ? AND user_id = ?",
        (session_id, user_id),
    )
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected
