import os
import sys
from dotenv import load_dotenv
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.scheduler import send_daily_summary
from backend.models import Lead

load_dotenv()

def run_report_test():
    db = SessionLocal()
    try:
        print("--- Checking Database State ---")
        total_leads = db.query(Lead).count()
        print(f"Total leads in database: {total_leads}")
        
        if total_leads == 0:
            print("WARNING: No leads found. Please upload leads via the Dashboard first.")
            return

        print("\n--- Sending Daily Summary Report ---")
        print("This will use the SMTP settings in your .env file.")
        
        success = send_daily_summary(db)

        if success:
            print("\n✅ SUCCESS: Report sent successfully!")
            print(f"Check the inbox for: {os.getenv('REPORT_RECEIVER_EMAIL')}")
        else:
            print("\n❌ FAILED: SMTP sending failed. Check your SMTP_PASSWORD (App Password) or SMTP_SERVER settings.")
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    run_report_test()
