import pytest
import pandas as pd
import os
from sqlalchemy import create_mock_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import Lead, LeadStatus
from backend.lead_processor import process_leads_excel
from sqlalchemy import create_engine

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_process_leads_excel(db, tmp_path):
    # Create a dummy excel file
    df = pd.DataFrame({
        'First Name': ['Test'],
        'Last Name': ['User'],
        'Email': ['test@example.com'],
        'Company Name': ['Test Co']
    })
    file_path = tmp_path / "test_leads.xlsx"
    df.to_excel(file_path, index=False)
    
    result = process_leads_excel(str(file_path), db)
    
    assert result["added"] == 1
    assert result["skipped"] == 0
    
    lead = db.query(Lead).filter(Lead.email == "test@example.com").first()
    assert lead is not None
    assert lead.first_name == "Test"
    assert lead.company_name == "Test Co"

def test_process_leads_duplicate(db, tmp_path):
    # Setup: Add an existing lead
    db.add(Lead(first_name="Existing", email="test@example.com"))
    db.commit()
    
    df = pd.DataFrame({
        'First Name': ['Duplicate'],
        'Email': ['test@example.com']
    })
    file_path = tmp_path / "dup_leads.xlsx"
    df.to_excel(file_path, index=False)
    
    result = process_leads_excel(str(file_path), db)
    assert result["added"] == 0
    assert result["skipped"] == 1

def test_process_leads_invalid_email(db, tmp_path):
    df = pd.DataFrame({
        'First Name': ['NoEmail'],
        'Email': [float('nan')]
    })
    file_path = tmp_path / "no_email.xlsx"
    df.to_excel(file_path, index=False)
    
    result = process_leads_excel(str(file_path), db)
    assert result["added"] == 0
    assert result["skipped"] == 1
