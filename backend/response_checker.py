import os
import imaplib
import email
from email.header import decode_header
from .models import LeadStatus, ResponseCategory
from openai import OpenAI
from dotenv import load_dotenv
import logging

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def classify_response(response_text: str):
    """
    Uses AI to classify the lead's response.
    """
    try:
        prompt = f"""
        Classify the following email response from a sales lead into one of these categories:
        1. Interested
        2. Not Interested
        3. Neutral
        
        Response Text:
        ---
        {response_text}
        ---
        
        Output only the category name.
        """
        
        reply = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        category = reply.choices[0].message.content.strip()
        if "Interested" in category and "Not" not in category:
            return ResponseCategory.INTERESTED.value
        elif "Not Interested" in category:
            return ResponseCategory.NOT_INTERESTED.value
        else:
            return ResponseCategory.NEUTRAL.value
            
    except Exception as e:
        logger.error(f"Error classifying response: {str(e)}")
        return ResponseCategory.NEUTRAL.value

def check_for_replies(db):
    """
    Checks the configured inbox for replies and updates lead status.
    """
    try:
        imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")
        username = os.getenv("SMTP_USERNAME")
        password = os.getenv("SMTP_PASSWORD")

        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(username, password)
        mail.select("inbox")

        # Search for all emails
        _, messages = mail.search(None, "ALL")
        
        if messages[0]:
            for num in messages[0].split():
                _, data = mail.fetch(num, "(RFC822)")
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                from_ = msg.get("From")
                subject = msg.get("Subject")
                
                # Extract email address
                import re
                email_match = re.search(r'[\w\.-]+@[\w\.-]+', from_)
                if not email_match:
                    continue
                    
                sender_email = email_match.group(0)
                
                # Check if this email matches one of our leads
                lead = db.leads.find_one({"email": sender_email})
                if lead:
                    # Extract body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                break
                    else:
                        body = msg.get_payload(decode=True).decode()
                    
                    # Classify and update
                    category = classify_response(body)
                    db.leads.update_one(
                        {"_id": lead["_id"]},
                        {"$set": {
                            "response_category": category,
                            "status": LeadStatus.REPLIED.value
                        }}
                    )
                    
                    logger.info(f"Updated lead {sender_email} status to REPLIED with category {category}")
        
        mail.close()
        mail.logout()
        return True

    except Exception as e:
        logger.error(f"Error checking replies: {str(e)}")
        return False
