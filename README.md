# AI SDR Multi-Agent Outreach System

A production-grade, AI-powered sales development representative (SDR) system that automates lead ingestion, personalized email generation, response monitoring, and daily reporting.

## 🚀 Features

- **Lead Processor**: Automatically ingest and validate leads from Excel files.
- **AI Email Generator**: Personalized emails generated via GPT-4o based on company, industry, and role.
- **Rate-Limited Emailer**: Sends exactly 20 emails per week to maintain high deliverability and avoid spam filters.
- **Response Monitor**: Automatically checks the inbox for replies and classifies them as "Interested", "Neutral", or "Not Interested" using AI.
- **Daily Reporting**: Sends a summary of outreach activities and lead responses to a configured administrator email.
- **Professional Dashboard**: React + Tailwind CSS frontend to control the campaign, view analytics, and manage leads.

## 🛠 Tech Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite, APScheduler, OpenAI GPT-4o.
- **Frontend**: Vite, React, Tailwind CSS, Lucide Icons, Axios.
- **Data**: Pandas for high-speed Excel processing.

## 📦 Getting Started

### 1. Prerequisite
- Python 3.8+
- Node.js & npm

### 2. Backend Setup
1. Navigate to the backend directory (or root):
   ```bash
   pip install -r requirements.txt
   ```
2. Create a `.env` file based on `.env.example` and fill in your OpenAI key and SMTP credentials.
3. Start the server:
   ```bash
   python -m backend.main
   ```

### 3. Frontend Setup
1. Navigate to the `frontend` directory:
   ```bash
   npm install
   ```
2. Start the development server:
   ```bash
   npm run dev
   ```

## 📊 Deployment

### AWS EC2 Instructions
1. Launch an Ubuntu EC2 instance.
2. Install Docker & Docker Compose.
3. Clone this repository.
4. Run `docker-compose up --build`.

## 📂 Project Structure

```
ai_sales_agent/
├── backend/
│   ├── main.py (FastAPI App)
│   ├── lead_processor.py (Excel Agent)
│   ├── ai_email_generator.py (OpenAI Agent)
│   ├── email_service.py (SMTP Service)
│   ├── response_checker.py (Inbox Agent)
│   ├── models.py (DB Schema)
│   └── scheduler.py (Task Management)
├── frontend/
│   └── src/ (React Components)
├── data/
│   └── leads_sample.xlsx (Test Data)
└── README.md
```

## 📋 Data Format
The system expects an Excel file with the following columns:
`First Name`, `Last Name`, `Title`, `Company Name`, `Email`, `Industry`, `Revenue`, `Employee`, etc.

---
Built with 🚀 for automated sales excellence.
