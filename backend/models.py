from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Any
from datetime import datetime
import enum

class LeadStatus(str, enum.Enum):
    PENDING = "Pending"
    PROCESSING = "Processing"
    DRAFTED = "Drafted"
    FAILED = "Failed"
    EMAIL_SENT = "Email Sent"
    REPLIED = "Replied"
    INTERESTED = "Interested"
    NOT_INTERESTED = "Not Interested"

class ResponseCategory(str, enum.Enum):
    INTERESTED = "Interested"
    NOT_INTERESTED = "Not Interested"
    NEUTRAL = "Neutral"
    NO_RESPONSE = "No Response"

class Lead(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    company_name: Optional[str] = None
    mailing_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    web_address: Optional[str] = None
    email: EmailStr
    revenue: Optional[str] = None
    employees: Optional[str] = None
    industry: Optional[str] = None
    sub_industry: Optional[str] = None
    status: LeadStatus = LeadStatus.PENDING
    response_category: ResponseCategory = ResponseCategory.NO_RESPONSE
    last_contacted_at: Optional[datetime] = None
    draft_subject: Optional[str] = None
    draft_body: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EmailLog(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    lead_id: Optional[str] = None
    lead_email: Optional[str] = None # Added since we won't have quick relational joins
    subject: str
    body: str
    sent_at: datetime = Field(default_factory=datetime.utcnow)

class CampaignConfig(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    key: str
    value: str
