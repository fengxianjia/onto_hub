import sys
import os
import shutil
import sqlite3
from pathlib import Path

# Add backend to sys.path to allow importing from app
sys.path.append(str(Path(__file__).parent / "backend"))

from app.config import settings

def cleanup():
    # Parse file path from URL (e.g., sqlite:///path/to/db -> path/to/db)
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    storage_dir = settings.STORAGE_DIR
    
    # 1. Database Cleanup
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            
            # Check if tables exist before querying
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ontology_series'")
            if not c.fetchone():
                print("Table 'ontology_series' does not exist. Database might be empty or uninitialized.")
                conn.close()
            else:
                # Find all series codes that look like test data
                c.execute("SELECT code FROM ontology_series WHERE code LIKE '%_test_%' OR code LIKE '%_uni_%' OR code LIKE 'del-%' OR code LIKE 'upd-%' OR code LIKE 'list-%'")
                codes = [row[0] for row in c.fetchall()]
                
                if codes:
                    # Delete packages first (foreign key constraint might be present)
                    for code in codes:
                        c.execute("DELETE FROM ontology_packages WHERE series_code=?", (code,))
                        c.execute("DELETE FROM ontology_series WHERE code=?", (code,))
                    
                    conn.commit()
                    print(f"Deleted {len(codes)} test series from database.")
                else:
                    print("No test series found in database.")
                
                conn.close()
        except Exception as e:
            print(f"Error during database cleanup: {e}")
    else:
        print(f"Database {db_path} not found.")

    # 2. Storage Cleanup
    if os.path.exists(storage_dir):
        count = 0
        for d in os.listdir(storage_dir):
            # Delete directories that look like test IDs (UUID-like or matching test patterns)
            # Most production IDs are likely UUIDs, but test ones often have prefixes or timestamps
            if any(x in d for x in ['_test_', '_uni_', 'del-', 'upd-', 'list-']) or len(d) > 30:
                shutil.rmtree(os.path.join(storage_dir, d), ignore_errors=True)
                count += 1
        print(f"Deleted {count} test directories from storage.")
    else:
        print(f"Storage directory {storage_dir} not found.")

if __name__ == "__main__":
    cleanup()
