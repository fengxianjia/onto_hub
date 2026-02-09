import os
import time
import psutil
import shutil
import sys

# Windows console encoding fix
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = os.path.join("backend", "data","ontohub.db")
STORAGE_PATH = os.path.join("backend", "data", "ontohub_storage")

def kill_process_on_port(port):
    found = False
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conn in proc.connections(kind='inet'):
                if conn.laddr.port == port:
                    print(f"Killing process {proc.info['name']} (PID: {proc.info['pid']}) on port {port}")
                    proc.kill()
                    found = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return found

def cleanup():
    print("Stopping server on port 8003...")
    killed = kill_process_on_port(8003)
    if killed:
        print("Waiting for process to exit...")
        time.sleep(2)
    else:
        print("No process found on port 8003.")

    if os.path.exists(DB_PATH):
        print(f"Deleting {DB_PATH}...")
        try:
            os.remove(DB_PATH)
            print("Deleted database.")
        except Exception as e:
            print(f"Error deleting database: {e}")
    else:
        print("Database file not found.")

    if os.path.exists(STORAGE_PATH):
        print(f"Deleting {STORAGE_PATH}...")
        try:
            shutil.rmtree(STORAGE_PATH)
            print("Deleted storage directory.")
        except Exception as e:
            print(f"Error deleting storage: {e}")
    else:
        print("Storage directory not found.")

if __name__ == "__main__":
    cleanup()
