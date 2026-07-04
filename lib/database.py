import sqlite3
import os
import json


class Database:
    def __init__(self, db_path: str = "data/tg777.db"):
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init()

    def _init(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            session_path TEXT NOT NULL,
            twofa_password TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            last_name TEXT DEFAULT '',
            status TEXT DEFAULT 'active',
            metadata TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        self.conn.commit()

    def add_account(self, name: str, phone: str, session_path: str,
                    twofa_password: str = "", metadata: dict = None) -> int:
        cur = self.conn.execute(
            """INSERT INTO accounts (name, phone, session_path, twofa_password, metadata)
               VALUES (?,?,?,?,?)""",
            (name, phone, session_path, twofa_password, json.dumps(metadata or {}, ensure_ascii=False))
        )
        self.conn.commit()
        return cur.lastrowid

    def get_account(self, account_id: int) -> dict:
        row = self.conn.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
        return dict(row) if row else None

    def list_accounts(self) -> list[dict]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM accounts ORDER BY id").fetchall()]

    def update_account(self, account_id: int, **kwargs):
        if not kwargs:
            return
        sets = ", ".join(f"{k}=?" for k in kwargs)
        vals = list(kwargs.values()) + [account_id]
        self.conn.execute(f"UPDATE accounts SET {sets}, updated_at=CURRENT_TIMESTAMP WHERE id=?", vals)
        self.conn.commit()

    def delete_account(self, account_id: int):
        self.conn.execute("DELETE FROM accounts WHERE id=?", (account_id,))
        self.conn.commit()

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) as c FROM accounts").fetchone()["c"]
