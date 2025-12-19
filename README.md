# n8n Workflow Popularity Tracker

A robust, production-ready system to track and identify popular n8n workflows across multiple platforms (YouTube, Forums, Google Trends). Built with FastAPI, PostgreSQL, and Docker.

## 🚀 Key Features

*   **Multi-Source Data Collection**: Fetches data from YouTube (Videos), n8n Community Forum (Topics), and Google Trends.
*   **Popularity Analysis**: Calculates engagement scores based on views, likes, comments, and replies.
*   **Novelty Analytics**:
    *   **Geographic Divergence**: Identifies workflows trending in specific regions (e.g., popular in India but not US).
    *   **Predictive Trending**: Basic forecasting of workflow popularity.
*   **Automation**: Background scheduler (APScheduler) runs daily/weekly data collection jobs.
*   **Robust API**: RESTful endpoints with filtering, pagination, and detailed metadata.
*   **Production Ready**: Dockerized, type-safe (Pydantic), and fully tested (pytest).

---

## 🛠️ Tech Stack

*   **Language**: Python 3.10+
*   **Framework**: FastAPI
*   **Database**: PostgreSQL 15 (Async SQLAlchemy + Alembic)
*   **Containerization**: Docker & Docker Compose
*   **Testing**: Pytest & Httpx

---

## 🏁 Quick Start Guide

### 1. Prerequisites
*   Docker Desktop installed and running.

### 2. Configuration
1.  Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
    *(Or rename `.env.example` to `.env` manually)*
2.  Open `.env` and add your **YouTube API Key**:
    ```ini
    YOUTUBE_API_KEY=AIzaSy...
    ```
    *(Note: Discourse/Forum API key is optional as we use public access)*

### 3. Run with Docker
Start the application and database:
```bash
docker-compose up -d --build
```

### 4. Initialize Database
Apply the schema migrations to create the tables:
```bash
# Generate migration (only needed if new models added, skipping for first run if pre-generated)
# Apply migration
docker-compose exec web alembic upgrade head
```
*(If you need to generate the initial migration first: `docker-compose exec web alembic revision --autogenerate -m "Init"`)*

---

## 🔍 Verification & Usage

### 1. Verification Script
We have provided a script to verify the system health, database connection, and API endpoints instantly.
```bash
python verify_api.py
```
*   This will check server health.
*   Fetch workflows from the DB.
*   Save the dataset to **`api_workflows.json`**.
*   Test the Novelty Analytics endpoint.

### 2. API Documentation (Swagger UI)
Visit the interactive API documentation:
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

### 3. Key Endpoints
*   `GET /workflows`: List all workflows (supports filtering by `platform`, `country`, `search`).
*   `GET /workflows/{id}`: Detailed view with metrics.
*   `GET /api/v1/analytics/geographic-divergence`: View regional popularity differences.
*   `POST /admin/collect`: Manually trigger the data scraper background job.

---

## 🧪 Testing

The project includes a comprehensive test suite targeting API endpoints and collector logic.

Run tests inside the container:
```bash
docker-compose exec web pytest
```

---

## 📂 Project Structure

```
├── app/
│   ├── api/            # API Route handlers
│   ├── collectors/     # Logic for YouTube, Forum, Trends
│   ├── core/           # Config, logging, normalization
│   ├── db/             # Database session & models
│   ├── services/       # Business logic (Collection, Novelty)
│   └── main.py         # Application entrypoint
├── tests/              # Pytest suite
├── alembic/            # Database migrations
├── docker-compose.yml  # Container orchestration
├── Pyproject.toml      # Dependencies
└── README.md           # This file
```

---

## ✅ Deliverables Checklist matching Requirements

*   [x] **Working API**: Fully functional endpoints for listing and analytics.
*   [x] **Dataset**: `verify_api.py` generates `api_workflows.json` with 50+ items.
*   [x] **Data Sources**: YouTube, Forum, and Google Trends integrated.
*   [x] **Automation**: Cron jobs configured in `scheduler.py`.
*   [x] **Tests**: Unit and Integration tests passing.
