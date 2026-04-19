import pytest
import datetime
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import Lead, EmailLog, LeadStatus
from backend.email_service import send_email, get_sent_count_this_week

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

@pytest.fixture
def mock_lead():
    return Lead(first_name="Test", last_name="User", email="test@example.com")

@patch("smtplib.SMTP")
def test_send_email_success(mock_smtp, db, mock_lead):
    # Setup
    db.add(mock_lead)
    db.commit()
    
    instance = mock_smtp.return_value.__enter__.return_value
    
    result = send_email(db, mock_lead, "Subject", "Body")
    
    assert result is True
    assert mock_lead.status == LeadStatus.EMAIL_SENT
    assert db.query(EmailLog).count() == 1
    assert instance.send_message.called

@patch("smtplib.SMTP")
def test_send_email_rate_limit(mock_smtp, db, mock_lead):
    # Setup: Add 20 emails this week
    db.add(mock_lead)
    db.commit()
    for _ in range(20):
        log = EmailLog(lead_id=mock_lead.id, sent_at=datetime.datetime.utcnow())
        db.add(log)
    db.commit()
    
    # Overriding env or setting it high enough to trigger limit in test
    # The default in code is 20 if not set.
    
    result = send_email(db, mock_lead, "Subject", "Body")
    
    assert result is False
    assert mock_lead.status != LeadStatus.EMAIL_SENT
