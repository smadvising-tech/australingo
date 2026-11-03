import json
import os
import sqlite3
from pathlib import Path

class SQLiteBackedDict(dict):
    def __init__(self, key, defaults):
        self.key = key
        default_path = '/kaggle/working/australingo-demo.sqlite3' if Path('/kaggle/working').exists() else '/tmp/australingo-demo.sqlite3'
        self.path = os.environ.get('DEMO_DB_PATH', default_path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS demo_state (key TEXT PRIMARY KEY, data TEXT NOT NULL)')
            row = db.execute('SELECT data FROM demo_state WHERE key=?', (key,)).fetchone()
            if row is None:
                db.execute('INSERT INTO demo_state VALUES (?, ?)', (key, json.dumps(defaults)))
        super().__init__(json.loads(row[0]) if row else defaults)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        with sqlite3.connect(self.path) as db:
            db.execute('UPDATE demo_state SET data=? WHERE key=?', (json.dumps(dict(self)), self.key))
