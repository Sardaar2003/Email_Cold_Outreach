import os
from openai import OpenAI
from dotenv import load_dotenv
from .models import Lead

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_outreach_email(lead: Lead, product_description: str):
    """
    Generates a personalized sales email using OpenAI.
    """
    try:
        prompt = f"""
        You are a highly skilled Sales Development Representative (SDR).
        Generate a professional, personalized outreach email for the following lead:
        
        Lead Name: {lead.first_name} {lead.last_name}
        Title: {lead.title}
        Company: {lead.company_name}
        Industry: {lead.industry}
        Product description: {product_description}
        
        Guidelines:
        - Professional yet conversational tone.
        - Personalized introduction referencing their role or industry.
        - Clear value proposition based on the product description.
        - Strong call to action (direct but not pushy).
        - Keep it concise.
        
        Output format:
        Subject: [Compelling Subject Line]
        [Email Body]
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a world-class sales copywriter."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        
        # Split subject and body
        lines = content.split('\n')
        subject = "AI Outreach"
        body = content
        
        for line in lines:
            if line.lower().startswith("subject:"):
                subject = line.replace("Subject:", "").strip()
                body = "\n".join(lines[lines.index(line)+1:]).strip()
                break
                
        return subject, body
        
    except Exception as e:
        print(f"Error generating email: {str(e)}")
        # Fallback template if AI fails
        subject = f"AI Solution for {lead.company_name}"
        body = f"Hi {lead.first_name},\n\nI noticed your work at {lead.company_name}. We help {lead.industry} companies like yours with our solutions. Would you be open to a quick chat?\n\nBest regards,\nSales Team"
        return subject, body
