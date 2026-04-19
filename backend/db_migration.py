import sqlite3
import os

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'outreach.db')
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist yet. No migration needed.")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if draft_subject exists
    cursor.execute("PRAGMA table_info(leads)")
    columns = [info[1] for info in cursor.fetchall()]
    
    try:
        if 'draft_subject' not in columns:
            cursor.execute("ALTER TABLE leads ADD COLUMN draft_subject TEXT")
            print("Added draft_subject column")
        
        if 'draft_body' not in columns:
            cursor.execute("ALTER TABLE leads ADD COLUMN draft_body TEXT")
            print("Added draft_body column")
            
        conn.commit()
        print("Migration successful.")
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
