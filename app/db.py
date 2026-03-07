import sqlite3
from contextlib import closing
from pathlib import Path

DB_PATH = Path("/app/data/bot.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

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
        con.execute("""
        CREATE TABLE IF NOT EXISTS balance_replenishments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prev_balance REAL NOT NULL,
            new_balance REAL NOT NULL,
            threshold REAL NOT NULL,
            currency TEXT,
            monthly_rent REAL NOT NULL,
            user_count INTEGER NOT NULL,
            recommended_topup REAL NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
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


def get_users_count() -> int:
    with closing(sqlite3.connect(DB_PATH)) as con:
        cur = con.execute("SELECT COUNT(*) FROM users")
        row = cur.fetchone()
        return int(row[0] if row else 0)

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


def save_balance_replenishment(
    *,
    prev_balance: float,
    new_balance: float,
    threshold: float,
    currency: str,
    monthly_rent: float,
    user_count: int,
    recommended_topup: float,
) -> None:
    with closing(sqlite3.connect(DB_PATH)) as con:
        con.execute(
            """
            INSERT INTO balance_replenishments(
                prev_balance, new_balance, threshold, currency,
                monthly_rent, user_count, recommended_topup
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                prev_balance,
                new_balance,
                threshold,
                currency,
                monthly_rent,
                user_count,
                recommended_topup,
            ),
        )
        con.commit()
