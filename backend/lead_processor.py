import pandas as pd
from .models import Lead, LeadStatus
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_leads_excel(file_path: str, db):
    try:
        df = pd.read_excel(file_path)
        
        # Mapping Excel columns to Lead model fields
        mapping = {
            'First Name': 'first_name',
            'Middle Name': 'middle_name',
            'Last Name': 'last_name',
            'Title': 'title',
            'Company Name': 'company_name',
            'Mailing Address': 'mailing_address',
            'Primary City': 'city',
            'Primary State': 'state',
            'ZIP Code': 'zip_code',
            'Country': 'country',
            'Phone': 'phone',
            'Web Address': 'web_address',
            'Email': 'email',
            'Revenue': 'revenue',
            'Employee': 'employees',
            'Industry': 'industry',
            'Sub Industry': 'sub_industry'
        }
        
        added_count = 0
        skipped_count = 0
        
        email_pattern = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
        
        for _, row in df.iterrows():
            email = str(row.get('Email', '')).strip()
            if not email or email == 'nan' or not email_pattern.match(email):
                skipped_count += 1
                continue
                
            # Check if lead already exists
            existing_lead = db.leads.find_one({"email": email})
            if existing_lead:
                skipped_count += 1
                continue
            
            lead_data = {}
            for excel_col, model_attr in mapping.items():
                val = row.get(excel_col)
                lead_data[model_attr] = str(val) if pd.notna(val) else None
            
            # Validate with Pydantic model
            new_lead = Lead(**lead_data)
            
            # Insert dict into MongoDB collection
            db.leads.insert_one(new_lead.model_dump(by_alias=True, exclude={"id"}, exclude_none=True))
            added_count += 1
            
        logger.info(f"Imported {added_count} leads, skipped {skipped_count} (duplicates or invalid email)")
        return {"added": added_count, "skipped": skipped_count}
        
    except Exception as e:
        logger.error(f"Error processing leads: {str(e)}")
        raise e
