import sqlite3
import os

DB_PATH = "ontohub.db"

def clear_data():
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table_name in tables:
            t = table_name[0]
            if t != "sqlite_sequence": # Don't delete sequence data if you want to keep IDs? Actually better to delete.
                print(f"Clearing table {t}...")
                cursor.execute(f"DELETE FROM {t}")
        
        conn.commit()
        print("Database cleared.")
        
        # Optional: Vacuum to reclaim space
        cursor.execute("VACUUM")
        conn.close()
        
    except Exception as e:
        print(f"Error clearing database: {e}")

if __name__ == "__main__":
    clear_data()
