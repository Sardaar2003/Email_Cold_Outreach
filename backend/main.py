import os
import datetime
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import shutil

from .database import get_db
from .models import LeadStatus
from .lead_processor import process_leads_excel
from .email_service import send_email, get_sent_count_this_week
from .ai_email_generator import generate_outreach_email
from .response_checker import check_for_replies
from .scheduler import send_daily_summary

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager

def get_db_instance():
    # Helper to get the database outside of FastAPI requests
    return next(get_db())

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(run_daily_tasks, CronTrigger(hour=23), id="daily_check")
    scheduler.start()
    yield
    if scheduler.running:
        scheduler.shutdown()

app = FastAPI(title="AI Sales Outreach API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler = BackgroundScheduler()

def run_daily_tasks():
    db = get_db_instance()
    check_for_replies(db)
    send_daily_summary(db)

def process_campaign_step():
    db = get_db_instance()
    
    # 1. Draft Generation
    pending_lead = db.leads.find_one({"status": LeadStatus.PENDING.value})
    if pending_lead:
        # Prevent simultaneous processing
        db.leads.update_one({"_id": pending_lead["_id"]}, {"$set": {"status": LeadStatus.PROCESSING.value}})
        
        try:
            config = db.campaign_configs.find_one({"key": "product_description"})
            desc = config["value"] if config else os.getenv("PRODUCT_DESCRIPTION", "")
            
            # Reconstruct Pydantic or pass dict. ai_email_generator uses `lead.first_name` etc.
            # Convert pending_lead to simple object-like struct for the generator if needed.
            # Assuming generate_outreach_email expects dict or handles it: 
            class AttrDict(dict):
                def __init__(self, *args, **kwargs):
                    super(AttrDict, self).__init__(*args, **kwargs)
                    self.__dict__ = self
            lead_obj = AttrDict(pending_lead)
            
            subject, body = generate_outreach_email(lead_obj, desc)
            
            db.leads.update_one(
                {"_id": pending_lead["_id"]},
                {"$set": {
                    "draft_subject": subject,
                    "draft_body": body,
                    "status": LeadStatus.DRAFTED.value
                }}
            )
        except Exception as e:
            import logging
            logging.error(f"Failed to generate draft: {str(e)}")
            db.leads.update_one({"_id": pending_lead["_id"]}, {"$set": {"status": LeadStatus.PENDING.value}})

    # 2. Sending
    drafted_lead = db.leads.find_one({"status": LeadStatus.DRAFTED.value})
    if drafted_lead:
        send_email(db, drafted_lead, drafted_lead.get("draft_subject"), drafted_lead.get("draft_body"))

@app.post("/upload-leads")
async def upload_leads(file: UploadFile = File(...), db = Depends(get_db)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload an Excel file.")
    
    temp_path = f"data/{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    result = process_leads_excel(temp_path, db)
    return result

@app.post("/start-campaign")
async def start_campaign():
    if not scheduler.get_job("campaign_job"):
        scheduler.add_job(
            process_campaign_step, 
            "interval", 
            hours=4, 
            id="campaign_job",
            next_run_time=datetime.datetime.now()
        )
    return {"status": "Campaign started"}

@app.post("/stop-campaign")
async def stop_campaign():
    if scheduler.get_job("campaign_job"):
        scheduler.remove_job("campaign_job")
    return {"status": "Campaign stopped"}

@app.get("/leads")
async def get_leads(db = Depends(get_db)):
    # Convert ObjectIds to strings for JSON serialization
    leads = list(db.leads.find())
    for lead in leads:
        lead["id"] = str(lead.pop("_id"))
        if "last_contacted_at" in lead and lead["last_contacted_at"]:
            lead["last_contacted_at"] = lead["last_contacted_at"].isoformat()
        if "created_at" in lead and lead["created_at"]:
            lead["created_at"] = lead["created_at"].isoformat()
    return leads

@app.get("/analytics")
async def get_analytics(db = Depends(get_db)):
    return {
        "total_leads": db.leads.count_documents({}),
        "sent": db.leads.count_documents({"status": LeadStatus.EMAIL_SENT.value}),
        "replied": db.leads.count_documents({"status": LeadStatus.REPLIED.value}),
        "pending": db.leads.count_documents({"status": LeadStatus.PENDING.value}),
        "sent_this_week": get_sent_count_this_week(db)
    }

@app.get("/campaign-status")
async def get_campaign_status(db = Depends(get_db)):
    job = scheduler.get_job("campaign_job")
    is_running = job is not None
    next_run_time = job.next_run_time.isoformat() if job and job.next_run_time else None
    
    last_email = db.email_logs.find_one({}, sort=[("sent_at", -1)])
    last_email_sent_to = last_email.get("lead_email") if last_email else None
    last_email_sent_at = last_email.get("sent_at").isoformat() if last_email and last_email.get("sent_at") else None
    
    return {
        "is_running": is_running,
        "next_run_time": next_run_time,
        "last_email_sent_to": last_email_sent_to,
        "last_email_sent_at": last_email_sent_at
    }

@app.post("/configure")
async def configure(key: str, value: str, db = Depends(get_db)):
    db.campaign_configs.update_one(
        {"key": key},
        {"$set": {"value": value, "key": key}},
        upsert=True
    )
    return {"status": "Configuration updated"}

@app.get("/configs")
async def get_configs(db = Depends(get_db)):
    configs = list(db.campaign_configs.find())
    return {c["key"]: c["value"] for c in configs}

@app.post("/reset-campaign")
async def reset_campaign(db = Depends(get_db)):
    db.email_logs.delete_many({})
    db.leads.update_many(
        {},
        {"$set": {
            "status": LeadStatus.PENDING.value,
            "response_category": "No Response",
            "last_contacted_at": None
        }}
    )
    if scheduler.get_job("campaign_job"):
        scheduler.remove_job("campaign_job")
    return {"status": "Campaign reset successfully"}

@app.post("/sync-replies")
async def sync_replies(db = Depends(get_db)):
    success = check_for_replies(db)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to sync replies. Check IMAP settings or credentials.")
    return {"status": "Successfully synced latest email replies"}

@app.post("/test-report")
async def test_report(db = Depends(get_db)):
    success = send_daily_summary(db)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send report. Check SMTP settings and report receiver email.")
    return {"status": "Test report sent successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
