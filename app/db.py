import sqlite3
from contextlib import closing
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bot.db"

def init_db() -> None:
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            role TEXT NOT NULL CHECK(role IN ('admin','user')),
            added_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """)
        con.execute("""
        CREATE TABLE IF NOT EXISTS invites (
            token TEXT PRIMARY KEY,
            created_by INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','user')),
            expires_at INTEGER NOT NULL,
            used_by INTEGER,
            used_at TEXT
        )
        """)
        con.commit()

def add_user(chat_id: int, role: str) -> None:
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.execute("INSERT OR REPLACE INTO users(chat_id, role) VALUES(?, ?)", (chat_id, role))
        con.commit()

def get_user(chat_id: int) -> dict | None:
    with closing(sqlite3.connect(DB_PATH)) as con:
        cur = con.execute("SELECT chat_id, role FROM users WHERE chat_id=?", (chat_id,))
        row = cur.fetchone()
        if not row:
            return None
        return {"chat_id": row[0], "role": row[1]}

def list_users() -> list[dict]:
    with closing(sqlite3.connect(DB_PATH)) as con:
        cur = con.execute("SELECT chat_id, role, added_at FROM users ORDER BY added_at DESC")
        return [{"chat_id": r[0], "role": r[1], "added_at": r[2]} for r in cur.fetchall()]

def remove_user(chat_id: int) -> None:
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.execute("DELETE FROM users WHERE chat_id=?", (chat_id,))
        con.commit()

def create_invite(token: str, created_by: int, role: str, expires_at: int) -> None:
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.execute(
            "INSERT INTO invites(token, created_by, role, expires_at) VALUES(?, ?, ?, ?)",
            (token, created_by, role, expires_at),
        )
        con.commit()

def use_invite(token: str, used_by: int, now_ts: int) -> dict | None:
    """
    Atomically marks invite as used (if valid). Returns invite row (role) if success.
    """
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.isolation_level = None
        con.execute("BEGIN IMMEDIATE")

        cur = con.execute(
            "SELECT token, role, expires_at, used_by FROM invites WHERE token=?",
            (token,),
        )
        row = cur.fetchone()
        if not row:
            con.execute("ROLLBACK")
            return None

        _token, role, expires_at, already_used_by = row
        if already_used_by is not None or now_ts > int(expires_at):
            con.execute("ROLLBACK")
            return None

        con.execute(
            "UPDATE invites SET used_by=?, used_at=datetime('now') WHERE token=?",
            (used_by, token),
        )
        con.execute("COMMIT")
        return {"token": _token, "role": role, "expires_at": int(expires_at)}