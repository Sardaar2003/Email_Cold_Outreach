import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
from .models import LeadStatus, ResponseCategory
from jinja2 import Template
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REPORT_TEMPLATE = """
<h2>Daily Sales Outreach Summary - {{ date }}</h2>

<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse;">
    <thead>
        <tr style="background-color: #f2f2f2;">
            <th>Name</th>
            <th>Company</th>
            <th>Email</th>
            <th>Status</th>
            <th>AI Response Classification</th>
        </tr>
    </thead>
    <tbody>
        {% for lead in leads %}
        <tr>
            <td>{{ lead.get('first_name', '') }} {{ lead.get('last_name', '') }}</td>
            <td>{{ lead.get('company_name', '') }}</td>
            <td>{{ lead.get('email', '') }}</td>
            <td>{{ lead.get('status', '') }}</td>
            <td>{{ lead.get('response_category', '') }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<br>
<h3>Summary Metrics:</h3>
<ul>
    <li>Total Emails Sent Today: {{ metrics.sent_today }}</li>
    <li>Interested Leads: {{ metrics.interested }}</li>
    <li>Not Interested: {{ metrics.not_interested }}</li>
    <li>No Response / Neutral: {{ metrics.neutral }}</li>
</ul>

<p>Best Regards,<br>AI SDR System</p>
"""

def send_daily_summary(db):
    """
    Generates and sends a daily summary report to the configured receiver.
    """
    today = datetime.datetime.utcnow().date()
    start_of_today = datetime.datetime.combine(today, datetime.time.min)
    yesterday = start_of_today - datetime.timedelta(days=1)
    
    # Get leads contacted today or who replied today
    leads = list(db.leads.find({
        "$or": [
            {"last_contacted_at": {"$gte": start_of_today}},
            {"status": LeadStatus.REPLIED.value, "last_contacted_at": {"$gte": yesterday}}
        ]
    }))
    
    metrics = {
        "sent_today": db.leads.count_documents({"last_contacted_at": {"$gte": start_of_today}}),
        "interested": db.leads.count_documents({"response_category": ResponseCategory.INTERESTED.value}),
        "not_interested": db.leads.count_documents({"response_category": ResponseCategory.NOT_INTERESTED.value}),
        "neutral": db.leads.count_documents({"response_category": ResponseCategory.NEUTRAL.value})
    }
    
    template = Template(REPORT_TEMPLATE)
    html_content = template.render(date=today.strftime("%Y-%m-%d"), leads=leads, metrics=metrics)
    
    config = db.campaign_configs.find_one({"key": "REPORT_RECEIVER_EMAIL"})
    receiver_email = config["value"] if config and "value" in config else os.getenv("REPORT_RECEIVER_EMAIL")
    
    if not receiver_email:
        logger.error("No REPORT_RECEIVER_EMAIL configured. Cannot send report.")
        return False

    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = receiver_email
        msg['Subject'] = f"Daily Sales Outreach Report - {today}"
        msg.attach(MIMEText(html_content, 'html'))
        
        with smtplib.SMTP(os.getenv("SMTP_SERVER", "smtp.gmail.com"), int(os.getenv("SMTP_PORT", 587))) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            
        logger.info(f"Daily summary report sent to {receiver_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send summary report: {str(e)}")
        return False
