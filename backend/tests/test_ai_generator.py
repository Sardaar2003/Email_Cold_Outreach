import pytest
from unittest.mock import MagicMock, patch
from backend.models import Lead
from backend.ai_email_generator import generate_outreach_email

@pytest.fixture
def mock_lead():
    return Lead(
        first_name="John",
        last_name="Doe",
        title="CEO",
        company_name="TechFlow",
        industry="Software"
    )

@patch("backend.ai_email_generator.client")
def test_generate_outreach_email_success(mock_client, mock_lead):
    # Mocking OpenAI response
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Subject: Hello TechFlow\n\nHi John, nice company!"
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    
    subject, body = generate_outreach_email(mock_lead, "Our tool helps SaaS")
    
    assert subject == "Hello TechFlow"
    assert "Hi John" in body
    assert mock_client.chat.completions.create.called

@patch("backend.ai_email_generator.client")
def test_generate_outreach_email_fallback(mock_client, mock_lead):
    # Simulate API error
    mock_client.chat.completions.create.side_effect = Exception("API Error")
    
    subject, body = generate_outreach_email(mock_lead, "Our tool")
    
    assert "AI Solution" in subject
    assert "Hi John" in body
    assert "fallback" not in body # It should use the fallback template
