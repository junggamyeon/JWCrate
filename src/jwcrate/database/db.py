import sqlite3
from pathlib import Path
from typing import Dict

class DatabaseManager:
    def __init__(self, data_folder: Path):
        data_folder.mkdir(parents=True, exist_ok=True)
        self.db_path = data_folder / "database.db"
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS user_keys (
                    player_name TEXT,
                    key_id TEXT,
                    amount INTEGER,
                    PRIMARY KEY (player_name, key_id)
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS user_cooldowns (
                    player_name TEXT,
                    crate_id TEXT,
                    cooldown_until REAL,
                    PRIMARY KEY (player_name, crate_id)
                )
            """)

    def get_key_balance(self, player_name: str, key_id: str) -> int:
        cur = self.conn.execute("SELECT amount FROM user_keys WHERE player_name = ? AND key_id = ?", (player_name.lower(), key_id))
        row = cur.fetchone()
        return row["amount"] if row else 0

    def add_key_balance(self, player_name: str, key_id: str, amount: int):
        current = self.get_key_balance(player_name, key_id)
        new_amount = current + amount
        with self.conn:
            self.conn.execute("""
                INSERT INTO user_keys (player_name, key_id, amount) 
                VALUES (?, ?, ?) 
                ON CONFLICT(player_name, key_id) DO UPDATE SET amount = ?
            """, (player_name.lower(), key_id, new_amount, new_amount))

    def remove_key_balance(self, player_name: str, key_id: str, amount: int) -> bool:
        current = self.get_key_balance(player_name, key_id)
        if current < amount:
            return False
        new_amount = current - amount
        with self.conn:
            self.conn.execute("""
                UPDATE user_keys SET amount = ? WHERE player_name = ? AND key_id = ?
            """, (new_amount, player_name.lower(), key_id))
        return True
        
    def get_cooldown(self, player_name: str, crate_id: str) -> float:
        cur = self.conn.execute("SELECT cooldown_until FROM user_cooldowns WHERE player_name = ? AND crate_id = ?", (player_name.lower(), crate_id))
        row = cur.fetchone()
        return row["cooldown_until"] if row else 0.0

    def set_cooldown(self, player_name: str, crate_id: str, cooldown_until: float):
        with self.conn:
            self.conn.execute("""
                INSERT INTO user_cooldowns (player_name, crate_id, cooldown_until)
                VALUES (?, ?, ?)
                ON CONFLICT(player_name, crate_id) DO UPDATE SET cooldown_until = ?
            """, (player_name.lower(), crate_id, cooldown_until, cooldown_until))
