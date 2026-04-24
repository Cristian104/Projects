import sqlite3
import os

# Path to your database
DB_PATH = 'instance/db.sqlite'

def export():
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    print("--- BEGIN DATA DUMP ---")
    
    # 1. Export Users
    print("USERS:")
    try:
        users = c.execute("SELECT * FROM user").fetchall()
        for u in users:
            # Convert row to dict for easy reading
            print(dict(u))
    except Exception as e:
        print(f"Error reading users: {e}")

    # 2. Export Tasks
    print("\nTASKS:")
    try:
        tasks = c.execute("SELECT * FROM task").fetchall()
        for t in tasks:
            print(dict(t))
    except Exception as e:
        print(f"Error reading tasks: {e}")

    # 3. Export History
    print("\nHISTORY:")
    try:
        history = c.execute("SELECT * FROM task_history").fetchall()
        for h in history:
            print(dict(h))
    except Exception as e:
        print(f"Error reading history: {e}")

    print("--- END DATA DUMP ---")
    conn.close()

if __name__ == '__main__':
    export()
