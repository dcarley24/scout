import sqlite3

conn = sqlite3.connect('scout.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    industry TEXT,
    size TEXT,
    region TEXT,
    tags TEXT,
    nudge TEXT,
    summary TEXT,
    discovery TEXT,
    pushed_to_hubspot INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()

print("✅ scout.db initialized with pushed_to_hubspot flag.")
