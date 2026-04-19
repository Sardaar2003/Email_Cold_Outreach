import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import io
import pandas as pd

from backend.main import app
from backend.database import Base, get_db
from backend.models import Lead, LeadStatus, CampaignConfig

# Setup test database
TEST_DATABASE_URL = "sqlite:///./test_outreach.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def db_init():
    if os.path.exists("./test_outreach.db"):
        try:
            os.remove("./test_outreach.db")
        except:
            pass
    Base.metadata.create_all(bind=engine)
    yield
    # No drop_all/remove here to avoid locking issues on Windows

def test_get_leads_empty():
    response = client.get("/leads")
    assert response.status_code == 200
    assert response.json() == []

def test_upload_leads():
    # Create a real excel in memory
    df = pd.DataFrame({
        'First Name': ['API'],
        'Email': ['api@example.com']
    })
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    
    response = client.post(
        "/upload-leads",
        files={"file": ("test.xlsx", output, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    assert response.status_code == 200
    assert response.json()["added"] == 1

def test_analytics():
    response = client.get("/analytics")
    assert response.status_code == 200
    data = response.json()
    assert data["total_leads"] >= 1
    assert "sent" in data

def test_configure():
    response = client.post("/configure", params={"key": "test_key", "value": "test_val"})
    assert response.status_code == 200
    assert response.json() == {"status": "Configuration updated"}

def test_campaign_start_stop():
    response = client.post("/start-campaign")
    assert response.status_code == 200
    assert response.json() == {"status": "Campaign started"}
    
    response = client.post("/stop-campaign")
    assert response.status_code == 200
    assert response.json() == {"status": "Campaign stopped"}
