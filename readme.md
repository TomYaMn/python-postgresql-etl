# Personal Finance Live Tracker & AI Extractor

A Python-based Streamlit application for managing personal financial data through interactive bank statement editing and AI-powered transaction extraction.

The application allows users to upload and live-edit bank statements, leverage an AI agent to extract and categorize financial transactions, and persist the structured data into **PostgreSQL / TimescaleDB**.

The stored financial data can then be connected to **Apache Superset** for interactive dashboards, financial analytics, spending trends, and personal finance insights.

## Architecture

The application consists of three primary components:

| Component | Technology | Responsibility |
|---|---|---|
| Frontend & Application | Python / Streamlit | Interactive bank statement management and editing |
| AI Extraction | OpenAI API | Transaction extraction, interpretation, and categorization |
| Database | PostgreSQL / TimescaleDB | Structured financial transaction storage |
| Visualization | Apache Superset | Financial dashboards and spending analytics |

### Data Flow

```text
             Bank Statements
                    |
                    v
          Streamlit Application
                    |
                    v
             AI Extraction
              (OpenAI API)
                    |
                    v
          Transaction Processing
                    |
                    v
              TimescaleDB
                    |
                    v
             Apache Superset
                    |
                    v
          Financial Dashboards
```

## Core Features

### 1. Interactive Bank Statement Management

- Upload and process bank statements.
- Live-edit extracted transaction information.
- Review and correct transaction details before database ingestion.
- Manage structured financial records through the Streamlit interface.

### 2. AI-Powered Transaction Extraction

- Uses an AI agent to interpret bank statement content.
- Extracts transaction descriptions, dates, amounts, and relevant information.
- Categorizes spending based on transaction context.
- Converts unstructured financial information into structured records.

### 3. Financial Data Storage

- Persists processed transactions into PostgreSQL / TimescaleDB.
- Supports structured financial data management.
- Provides a centralized data source for financial analysis.
- Enables integration with Apache Superset.

### 4. Financial Analytics & Visualization

- Connects TimescaleDB to Apache Superset.
- Enables spending analysis and financial trend monitoring.
- Supports custom SQL queries and interactive dashboards.
- Provides a foundation for future personal finance analytics.

---

# Setup & Installation

## 1. Prerequisites

Ensure the following dependencies are installed:

- Python 3.x
- pip
- PostgreSQL / TimescaleDB
- OpenAI API key
- Docker Engine and Docker Compose (for containerized deployment)

## 2. Local Development Setup

To run or develop the application locally without Docker, create a Python virtual environment and install the required dependencies.

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

The application should be accessible at:

```text
http://localhost:8501
```

---

## Environment Variables (`.env`)

Create a `.env` file in the root directory of the project. This file is required for both local development and Docker deployment.

```env
# Database connection string
DATABASE_URL=postgresql+psycopg2://<user>:<password>@<ip-addr>:<port>/<data_table>?sslmode=disable

# OpenAI API Key 
OPENAI_API_KEY=your_api_key_here

# Timezone configuration for logging
TZ=Asia/Kuala_Lumpur

# Deployment Environment: 'local' for python virtual environment, 'docker' in compose
APP_ENV=local
```

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL / TimescaleDB connection string |
| `OPENAI_API_KEY` | API key used by the AI extraction agent |
| `TZ` | Timezone configuration for application logging and processing |

**Security considerations:**

- Never commit `.env` files or API keys to Git.
- Add `.env` to `.gitignore`.
- Use environment variables or Docker secrets to manage production credentials.
- Avoid hardcoding database credentials in application source code.

---

# Docker Network Prerequisite (Superset Integration)

If the Personal Finance Tracker and Apache Superset are deployed using separate Docker Compose projects, both projects must share a Docker network to communicate with each other.

Create a shared external Docker network before starting either Compose project.

## 1. Create Shared Docker Network

```bash
docker network create superset-network
```

Verify that the network was created:

```bash
docker network ls
```

## 2. Configure Docker Compose

Add the following network configuration to both Docker Compose files.

**For the Superset `docker-compose.yml`:**

Attach both the `superset` and `superset_db` services to the shared network.

**For the Finance App `docker-compose.yml`:**

Attach the application service (and your TimescaleDB service, if hosted together) to the same shared network.

Add the following network declaration to the bottom of both Compose files:

```yaml
networks:
  superset-network:
    external: true
```

Each relevant service must also include:

```yaml
networks:
  - superset-network
```

## 3. Configure Database Connection

Containers connected to the same Docker network can communicate using Docker's service DNS names.

For example, if the Finance App connects to the Superset PostgreSQL database, the `.env` configuration would look like this:

```env
DATABASE_URL=postgresql://superset:superset_pass@superset_db:5432/superset
```

**Important:** Replace `localhost` with the appropriate Docker service name when connecting to another container.

If the Finance App writes to a separate TimescaleDB instance, configure `DATABASE_URL` using that database's hostname and port instead.

For example:

```env
DATABASE_URL=postgresql+psycopg2://han:your_password@timescaledb:5432/personal_finance_data
```

If TimescaleDB is hosted directly on the VM rather than in Docker, use the VM's reachable IP address and ensure PostgreSQL accepts connections from the Docker network.

## 4. Deploy Independent Compose Projects

Start the Superset stack:

```bash
cd /u02/docker/superset

docker compose up -d --build
```

Start the Finance App stack:

```bash
cd /path/to/finance-app

docker compose up -d --build
```

Each Compose project can now be managed independently without affecting the other.

## 5. Verify Network Connectivity

Inspect the shared Docker network:

```bash
docker network inspect superset-network
```

Verify that both Compose projects' containers are connected to the network.

Test database hostname resolution from the Finance App container:

```bash
docker exec finance_tracker getent hosts superset_db
```

A successful DNS lookup should return the PostgreSQL container's internal Docker IP address.

**Note:** The external network must exist before deploying either Compose project. It is created once and can be reused across subsequent deployments.

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

If the application is hosted inside a VM, replace `localhost` with the VM's IP address:

```text
http://YOUR_VM_IP: