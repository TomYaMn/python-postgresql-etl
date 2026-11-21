# Personal Finance Live Tracker & AI Extractor

A Python-based Streamlit application and background automation suite for managing personal financial data through interactive bank statement editing, automated email alert ingestion, AI-powered transaction extraction, and real-time Telegram alerts.

The application allows users to upload and live-edit bank statements, automatically capture bank alert emails, leverage **Google Gemini** to extract and categorize financial transactions, and persist the structured data into **PostgreSQL / TimescaleDB**.

The stored financial data can then be connected to **Apache Superset** for interactive dashboards, financial analytics, spending trends, and personal finance insights.

---

## Architecture

The application consists of six primary components:

| Component | Technology | Responsibility |
|---|---|---|
| Frontend & Application | Python / Streamlit | Interactive live DB CRUD editor, PDF upload, and AI comparison view |
| Background Worker | Python (`imaplib` / `BeautifulSoup4`) | Polls email inbox for unread bank alerts and automates ingestion |
| AI Extraction | Google Gemini API (`google-genai`) | Transaction extraction, interpretation, and 3-tier income/expense categorization |
| Notifications | Telegram Bot API (`notifier.py`) | Real-time error reporting (both containers) and daily/monthly spending limit alerts |
| Database | PostgreSQL / TimescaleDB | Time-partitioned financial transaction storage |
| Visualization | Apache Superset | Financial dashboards and spending analytics |

### Data Flow

```text
   Bank Statements (PDF/TXT)          Bank Alert Emails (IMAP)
              |                                  |
              v                                  v
    Streamlit Application              Email Listener Worker
              \                                  /
               \                                /
                v                              v
                   AI Extraction (Google Gemini)
                                |
                                v
                     Transaction Processing
                                |
                 +--------------+--------------+
                 |                             |
                 v                             v
            TimescaleDB                  Telegram Bot
                 |                   (Limit & Error Alerts)
                 v
          Apache Superset
                 |
                 v
        Financial Dashboards
```

---

## Core Features

### 1. Interactive Bank Statement Management & Comparison
- Live CRUD editor for viewing, adding, editing, and deleting database records with dropdown validation for `transaction_type`, `category`, and `subcategory`.
- Upload and process bank statements (PDF or TXT).
- Review and edit AI-extracted records before database ingestion.
- **Comparison View:** Compare existing database records against newly extracted AI records by Date, Amount, Category, and Subcategory to spot missing or duplicate transactions.

### 2. AI-Powered Transaction Extraction
- Uses **Google Gemini** to interpret unstructured bank statements and alert emails.
- Categorizes transactions into standard expense categories and a 3-tier income structure (Earned, Investment, and Passive Income).

### 3. Automated Email Listener
- Runs as a dedicated background Docker container (`finance_email_listener`).
- Checks your inbox every 60 seconds for unread (`UNSEEN`) emails from your configured bank sender.
- Uses `BODY.PEEK[]` so emails are only marked as read *after* successful AI extraction and database insertion.

### 4. Real-Time Telegram Alerts
- **Error Monitoring:** Automatically forwards `ERROR`-level logs from both the Streamlit app and Email Listener to your Telegram chat.
- **Spending Limits:** Checks TimescaleDB in real time after every save/injection and alerts you when your daily spending limit or monthly allowance is reached.

### 5. Financial Data Storage & Visualization
- Persists processed transactions into PostgreSQL / TimescaleDB with timezone-aware (`TZ`) handling.
- Connects seamlessly to Apache Superset for custom SQL queries and interactive dashboards.

---

# Setup & Installation

## 1. Prerequisites

Ensure the following dependencies are installed:

- Python 3.11+
- pip
- PostgreSQL / TimescaleDB
- Google Gemini API Key
- Email account with IMAP enabled and an App Password (for automated email ingestion)
- Telegram account (for bot alerts)
- Docker Engine and Docker Compose (for containerized deployment)

## 2. Local Development Setup

### Create a Virtual Environment

```bash
python -m venv venv
```

### Activate the Virtual Environment

**Linux / macOS:**
```bash
source venv/bin/activate
```

**Windows:**
```cmd
venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Application

```bash
streamlit run app.py
```

The application will be accessible at:
```text
http://localhost:8501
```

---

## 3. Telegram Bot Setup & Testing

Follow these steps to create your bot, get your Chat ID, and verify that alerts work.

### Step 1: Create a Telegram Bot
1. Open Telegram and search for **@BotFather** (verified account with a blue checkmark).
2. Send `/newbot`.
3. Follow the prompts to choose a **display name** (e.g., `My Finance Tracker`) and a **username** ending in `bot` (e.g., `my_finance_alerts_bot`).
4. Copy the **HTTP API Token** provided by BotFather. This is your `TELEGRAM_BOT_TOKEN`.

### Step 2: Activate the Bot
1. Click the link to your new bot in BotFather's message (or search for its username in Telegram).
2. Click **Start** (or send `/start`).
   > **Important:** Telegram bots cannot message you first. You must send `/start` at least once before it can deliver alerts.

### Step 3: Get Your Chat ID
1. Search for **@userinfobot** in Telegram.
2. Click **Start** (or send `/start`).
3. The bot will reply with your account details. Copy the numeric value next to **Id** (e.g., `987654321`). This is your `TELEGRAM_CHAT_ID`.

### Step 4: Configure `.env`
Add your token, chat ID, and spending thresholds to your `.env` file:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321
DAILY_SPENDING_LIMIT=50.00
MONTHLY_ALLOWANCE_LIMIT=1500.00
```

### Step 5: Test the Bot
**If running in Docker:**
```bash
docker exec finance_email_listener python -c "from notifier import send_telegram_alert; send_telegram_alert('✅ Finance tracker Telegram alerts are live!')"
```

**If running locally (with virtual environment activated):**
```bash
python -c "from dotenv import load_dotenv; load_dotenv(); from notifier import send_telegram_alert; send_telegram_alert('✅ Finance tracker Telegram alerts are live!')"
```

If configured correctly, you will immediately receive the confirmation message in Telegram.

---

## 4. Environment Variables (`.env`)

Create a `.env` file in the root directory of the project. This file is required for both local development and Docker deployment.

```env
# Database connection string
DATABASE_URL=postgresql+psycopg2://<user>:<password>@<ip-addr>:<port>/<database_name>?sslmode=disable

# Google Gemini API Key
API_KEY=your_gemini_api_key_here

# Timezone configuration for logging and DB localization
TZ=Asia/Kuala_Lumpur

# Deployment Environment: 'local' for python virtual environment, 'docker' in compose
APP_ENV=local

# Email Listener Config (IMAP)
EMAIL_IMAP_SERVER=imap.gmail.com
EMAIL_ACCOUNT=your_email@gmail.com
EMAIL_APP_PASSWORD=your_16_char_app_password
BANK_EMAIL_SENDER=ibanking.alert@dbs.com

# Telegram Alerts & Spending Limits
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_numeric_chat_id
DAILY_SPENDING_LIMIT=50.00
MONTHLY_ALLOWANCE_LIMIT=1500.00
```

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL / TimescaleDB connection string |
| `API_KEY` | Google Gemini API key used by the AI extraction agent |
| `TZ` | Timezone configuration (e.g., `Asia/Kuala_Lumpur`) |
| `APP_ENV` | Environment label (`local` or `docker`) |
| `EMAIL_IMAP_SERVER` | IMAP server address (e.g., `imap.gmail.com`) |
| `EMAIL_ACCOUNT` | Email address to monitor for bank alerts |
| `EMAIL_APP_PASSWORD` | 16-character App Password (without spaces) |
| `BANK_EMAIL_SENDER` | Exact sender email address of bank transaction alerts |
| `TELEGRAM_BOT_TOKEN` | HTTP API token from `@BotFather` |
| `TELEGRAM_CHAT_ID` | Your numeric Telegram user ID from `@userinfobot` |
| `DAILY_SPENDING_LIMIT` | Daily expense threshold that triggers a Telegram alert (`0` to disable) |
| `MONTHLY_ALLOWANCE_LIMIT` | Monthly expense threshold that triggers a Telegram alert (`0` to disable) |

**Security considerations:**
- Never commit `.env` files, API keys, or App Passwords to Git.
- Ensure `.env` is listed in both `.gitignore` and `.dockerignore`.
- Rotate credentials immediately if they are ever exposed.

---

# Docker Network Prerequisite (Superset Integration)

If the Personal Finance Tracker and Apache Superset are deployed using separate Docker Compose projects, both projects must share an external Docker network to communicate.

## 1. Create Shared Docker Network

```bash
docker network create superset-network
```

Verify that the network was created:
```bash
docker network ls
```

## 2. Configure Docker Compose

Add the following network declaration to the bottom of both Compose files:

```yaml
networks:
  superset-network:
    external: true
```

Attach each relevant service (`finance-app`, `email-listener`, `superset`, `superset_db`) to the network:

```yaml
networks:
  - superset-network
```

## 3. Configure Database Connection

Containers on the same Docker network communicate using Docker service DNS names:

```env
DATABASE_URL=postgresql+psycopg2://han:your_password@timescaledb:5432/personal_finance_data
```

If TimescaleDB is hosted directly on the VM rather than in Docker, use the VM's reachable IP address and ensure PostgreSQL accepts connections from the Docker network.

## 4. Build & Deploy

Build the Docker image and start both the web app and email listener containers:

```bash
docker build -t python-superset-etl:latest .
docker compose up -d
```

## 5. Verify Network & Logs

Inspect the shared Docker network:
```bash
docker network inspect superset-network
```

Check the background email listener logs:
```bash
docker logs -f finance_email_listener
```

---

# Application Usage

## 1. Start the Application

For local development:
```bash
streamlit run app.py
```

For Docker deployment:
```bash
docker compose up -d
```

## 2. Access the Streamlit Interface

Open the application in your browser:
```text
http://localhost:8501
```

If hosted on a remote VM, replace `localhost` with your VM's IP address:
```text
http://YOUR_VM_IP:8501
```