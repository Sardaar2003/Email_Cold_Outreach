import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
from .models import LeadStatus
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def get_sent_count_this_week(db):
    one_week_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    return db.email_logs.count_documents({"sent_at": {"$gte": one_week_ago}})

def send_email(db, lead_dict: dict, subject: str, body: str):
    """
    Sends an email and logs the activity. Respects weekly rate limits.
    """
    # Fetch dynamic limit from database
    config = db.campaign_configs.find_one({"key": "weekly_email_limit"})
    limit = int(config["value"]) if config else int(os.getenv("WEEKLY_EMAIL_LIMIT", 20))

    if get_sent_count_this_week(db) >= limit:
        logger.warning(f"Weekly email limit ({limit}) reached. Email queued.")
        return False

    email_address = lead_dict.get("email")
    lead_id = lead_dict.get("_id")

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = email_address
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        # Log to database
        db.email_logs.insert_one({
            "lead_id": str(lead_id),
            "lead_email": email_address,
            "subject": subject,
            "body": body,
            "sent_at": datetime.datetime.utcnow()
        })
        
        # Update lead status
        db.leads.update_one(
            {"_id": lead_id},
            {"$set": {
                "status": LeadStatus.EMAIL_SENT.value,
                "last_contacted_at": datetime.datetime.utcnow()
            }}
        )
        logger.info(f"Email sent successfully to {email_address}")
        return True

    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"Hard bounce: Recipient refused {email_address}: {str(e)}")
        db.leads.update_one({"_id": lead_id}, {"$set": {"status": LeadStatus.FAILED.value}})
        return False
    except smtplib.SMTPException as e:
        logger.error(f"Soft bounce: SMTP error for {email_address}: {str(e)}")
        db.leads.update_one({"_id": lead_id}, {"$set": {"status": LeadStatus.DRAFTED.value}})
        return False
    except Exception as e:
        logger.error(f"Failed to send email to {email_address}: {str(e)}")
        db.leads.update_one({"_id": lead_id}, {"$set": {"status": LeadStatus.FAILED.value}})
        return False
