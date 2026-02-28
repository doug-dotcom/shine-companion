import sqlite3

conn = sqlite3.connect('memory.db')
c = conn.cursor()

# USER MEMORY (long term)
c.execute('''
CREATE TABLE IF NOT EXISTS user_memory(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id TEXT,
key TEXT,
value TEXT,
created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# SESSION MEMORY
c.execute('''
CREATE TABLE IF NOT EXISTS session_memory(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id TEXT,
message TEXT,
response TEXT,
created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# KNOWLEDGE MEMORY
c.execute('''
CREATE TABLE IF NOT EXISTS knowledge_memory(
id INTEGER PRIMARY KEY AUTOINCREMENT,
topic TEXT,
content TEXT,
created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()

print("Memory system ready")
