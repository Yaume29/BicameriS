import json
import sqlite3
from datetime import datetime
from pathlib import Path


class Memory:
    def __init__(self, base_path="./memory"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        self.db_path = self.base_path / "memories.db"
        self.json_path = self.base_path / "memories.json"
        self.init_db()

    def init_db(self):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    type TEXT,
                    content TEXT,
                    tags TEXT
                )
            """)
            conn.commit()
        except sqlite3.Error as e:
            print(f"[MEMORY] Erreur init_db: {e}")
        finally:
            if conn:
                conn.close()

    def store(self, type_, content, tags=""):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO memories (timestamp, type, content, tags) VALUES (?, ?, ?, ?)",
                (datetime.now().isoformat(), type_, content, tags),
            )
            conn.commit()
        except sqlite3.Error as e:
            print(f"[MEMORY] Erreur store: {e}")
        finally:
            if conn:
                conn.close()

        self.append_json(type_, content, tags)

    def append_json(self, type_, content, tags):
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = []
        except json.JSONDecodeError:
            data = []

        data.append(
            {
                "timestamp": datetime.now().isoformat(),
                "type": type_,
                "content": content,
                "tags": tags,
            }
        )

        try:
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"[MEMORY] Erreur append_json: {e}")

    def recall(self, limit=10):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT timestamp, type, content FROM memories ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            results = cursor.fetchall()
            return results
        except sqlite3.Error as e:
            print(f"[MEMORY] Erreur recall: {e}")
            return []
        finally:
            if conn:
                conn.close()
