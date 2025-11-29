"""
Inspect Raw Database
"""
import sqlite3
import os

DB_PATH = 'data/database.db.raw'

def inspect():
    if not os.path.exists(DB_PATH):
        print(f"File not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # List tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tables:", [t[0] for t in tables])
    
    for table in tables:
        tname = table[0]
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tname}")
            count = cursor.fetchone()[0]
            print(f"Table '{tname}': {count} rows")
        except Exception as e:
            print(f"Error reading {tname}: {e}")
            
    conn.close()

if __name__ == "__main__":
    inspect()
