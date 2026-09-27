"""
DecryptTrace – Immutable Decryption Provenance System
Database initialization and schema (SQLite)
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'decrypttrace.db')


def get_db():
    """Return a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize all database tables."""
    conn = get_db()
    cur = conn.cursor()

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL UNIQUE,
            email       TEXT    NOT NULL UNIQUE,
            password_hash TEXT  NOT NULL,
            role        TEXT    NOT NULL DEFAULT 'user',
            public_key  TEXT,
            private_key_enc TEXT,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Files table  – stores encrypted file metadata
    cur.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            filename        TEXT    NOT NULL,
            original_name   TEXT    NOT NULL,
            file_hash       TEXT    NOT NULL,
            encrypted_path  TEXT    NOT NULL,
            uploaded_by     INTEGER NOT NULL REFERENCES users(id),
            uploaded_at     TEXT    NOT NULL DEFAULT (datetime('now')),
            is_deleted      INTEGER NOT NULL DEFAULT 0
        )
    """)

    # Decryption events / Provenance records
    cur.execute("""
        CREATE TABLE IF NOT EXISTS provenance_records (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id         INTEGER NOT NULL REFERENCES files(id),
            decrypted_by    INTEGER NOT NULL REFERENCES users(id),
            decrypted_at    TEXT    NOT NULL DEFAULT (datetime('now')),
            file_hash       TEXT    NOT NULL,
            event_hash      TEXT    NOT NULL,
            signature       TEXT    NOT NULL,
            ledger_index    INTEGER,
            success         INTEGER NOT NULL DEFAULT 1,
            notes           TEXT
        )
    """)

    # Access log – every attempt (authorized or not)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS access_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER REFERENCES users(id),
            action      TEXT    NOT NULL,
            file_id     INTEGER REFERENCES files(id),
            ip_address  TEXT,
            timestamp   TEXT    NOT NULL DEFAULT (datetime('now')),
            success     INTEGER NOT NULL DEFAULT 1,
            details     TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Database initialized successfully.")


if __name__ == '__main__':
    init_db()
