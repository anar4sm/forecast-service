# Forecast Service

A test microservice for managing energy production forecasts across multiple power plants with real-time event streaming.

## Overview

The **Forecast Service** is a RESTful API built with **FastAPI** and **PostgreSQL** that enables:
- Creating and updating hourly forecast estimates for power plants
- Querying historical forecasts by plant or aggregated company-wide
- Publishing position change events to **Kafka** for downstream consumption (real-time dashboards, analytics, etc.)

The service follows a **layered architecture** (Controller → Service → Repository).

## Documentation

- **System Architecture:** See [`FS_System_Architecture_v1-0_Anar_Mehdiyev.pdf`](FS_System_Architecture_v1-0_Anar_Mehdiyev.pdf) for Diagrams, API Specifications, Decision Log and Instructions.

---

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Runtime** | Python | 3.11+ |
| **Web Framework** | FastAPI | RESTful API framework; async request handling |
| **Database** | PostgreSQL | 15-alpine | Primary data store |
| **Event Streaming** | Apache Kafka | 7.5.0 |
| **Orchestration** | Docker Compose | 3.8+ |

---

## API Endpoints

### 1. Create or Update Forecast Estimate

```
PUT /forecasts/
Content-Type: application/json

Request body
{
  "plant_id": "TR_001",
  "forecast_timestamp": "2025-11-15T14:00:00Z",
  "estimated_production_mwh": 42.5
}

Response (201/200):
{
  "id": 123,
  "plant_id": "TR_001",
  "forecast_timestamp": "2025-11-15T14:00:00Z",
  "estimated_production_mwh": 42.5,
  "submission_timestamp": "2025-11-15T10:30:15.123456"
}
```

**Behavior:**
- If a forecast for the same plant and timestamp exists, it is updated.
- If not, a new record is created.
- On success, a `position_changed` event is published to Kafka.

---

### 2. Get Forecasts for a Plant

```
GET /forecasts/{plant_id}?start_date=2025-11-15T00:00:00Z&end_date=2025-11-16T00:00:00Z

Response (200):
[
  {
    "id": 123,
    "plant_id": "TR_001",
    "forecast_timestamp": "2025-11-15T14:00:00Z",
    "estimated_production_mwh": 42.5,
    "submission_timestamp": "2025-11-15T10:30:15.123456"
  },
  ...
]
```

**Query Parameters:**
- `start_date` (required): Inclusive start time (ISO 8601)
- `end_date` (required): Exclusive end time (ISO 8601)

---

### 3. Get Company Position (Aggregated)

```
GET /forecasts/company/position?start_date=2025-11-15T00:00:00Z&end_date=2025-11-16T00:00:00Z

Response (200):
{
  "start_date": "2025-11-15T00:00:00+01:00",
  "end_date": "2025-11-16T00:00:00+01:00",
  "total_forecast_mwh": 1250.75,
  "by_location": {
    "Turkey": 450.25,
    "Bulgaria": 380.5,
    "Spain": 420.0
  }
}
```

**Query Parameters:**
- `start_date` (required): Inclusive start time (ISO 8601)
- `end_date` (required): Exclusive end time (ISO 8601)

**Returns:**
- Total forecasted production (MWh) across all plants in the time range.
- Breakdown by plant location for analysis.

---

## Setup & Execution

### Prerequisites

- **Docker** and **Docker Compose** (for containerized stack)
  - OR **Python 3.11+** and **PostgreSQL** (for local development)
- **Git** (to clone the repository)

### Option 1: Docker Compose

#### 1. Clone and navigate to the project:

```powershell
cd <repo-folder>\forecast-service
```

#### 2. Build and start all services:

```powershell
docker compose up --build -d
```

This command:
- Builds the app image from `Dockerfile`
- Starts four containers:
  - **forecast-service** on `http://localhost:8000`
  - **postgres_db** on `localhost:5432`
  - **zookeeper** on `localhost:2181`
  - **kafka** on `localhost:9092` (internal) and `localhost:29092` (external)
- Creates network and volumes automatically

#### 3. Verify services are running:

```powershell
docker compose ps
```

Expected output:
```
NAME                  STATUS          PORTS
forecast-service      Up              0.0.0.0:8000->8000/tcp
postgres_db           Up              5432/tcp
zookeeper             Up              2181/tcp
kafka                 Up              9092/tcp, 0.0.0.0:29092->29092/tcp
```

#### 4. Access API documentation:

Open your browser and navigate to:

```
http://localhost:8000/docs
```

This opens an interactive **Swagger UI** where you can test all endpoints.

#### 5. View application logs:

```powershell
docker compose logs -f forecast-service
```

---

### Option 2: Local Development (Python + PostgreSQL)

#### 1. Install Python dependencies:

```powershell
pip install -r requirements.txt
```

#### 2. Set up environment variables:

Create a `.env` file in the project root:

```
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=forecastdb
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=position_changes
```

#### 3. Ensure PostgreSQL and Kafka are running:

- PostgreSQL: Start the service on `localhost:5432`
- Kafka: Start Zookeeper and Kafka broker on their default ports, or use Docker for them:

```powershell
docker compose up postgres_db zookeeper kafka -d
```

#### 4. Run the application:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The app will:
- Create database tables on startup
- Load initial power plants
- Start the server on `http://localhost:8000`

---

## Loading Test Data

A helper script `scripts/seed_forecasts.py` populates the database with sample forecasts.

#### Run inside the Docker container:

```powershell
docker compose exec forecast-service pip install requests --quiet
docker compose exec forecast-service python scripts/seed_forecasts.py
```

**Output:**
```
OK: TR_001 2025-11-15T00:00:00Z -> 1
OK: BG_001 2025-11-15T00:00:00Z -> 2
OK: ES_001 2025-11-15T00:00:00Z -> 3
...
Done. (72 forecasts seeded)
```

#### Run locally (if using Option 2):

```powershell
python scripts/seed_forecasts.py
```

Ensure the API is running locally on `http://localhost:8000` before running the script.

---

## Testing & Verification

### Test API Endpoints

#### Option 1. Swagger UI

Open your browser and navigate to:
```
http://localhost:8000/docs
```
This opens an interactive **Swagger UI** where you can test all endpoints.

#### Option 2. Browser Console

Open your browser and press `F12` to open Developer Tools, then paste:

#### 1. Create a forecast:

```javascript
fetch('http://localhost:8000/forecasts/', {
  method: 'PUT',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    plant_id: 'TR_001',
    forecast_timestamp: '2025-11-15T15:00:00Z',
    estimated_production_mwh: 50.0
  })
}).then(r => r.json()).then(console.log)
```

#### 2. Get plant forecasts:

```javascript
fetch('http://localhost:8000/forecasts/TR_001?start_date=2025-11-15T00:00:00Z&end_date=2025-11-16T00:00:00Z')
  .then(r => r.json()).then(console.log)
```

#### 3. Get company position:

```javascript
fetch('http://localhost:8000/forecasts/company/position?start_date=2025-11-15T00:00:00Z&end_date=2025-11-16T00:00:00Z')
  .then(r => r.json()).then(console.log)
```

### Verify Kafka Events

The app publishes position-change events to topic `position_changes` whenever forecasts are created/updated.

#### List topics:

```powershell
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

#### Consume messages (latest 10):

```powershell
docker compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic position_changes --from-beginning --max-messages 10
```

## Project Structure

```
forecast-service/
├── Dockerfile                       # App container image
├── docker-compose.yml               # Multi-container orchestration (app, DB, Kafka)
├── requirements.txt                 # Python dependencies
├── .env.example                     # Example environment variables
├── README.md                        # This file
│
├── app/
│   ├── main.py                      # FastAPI app, startup/shutdown hooks
│   ├── core/
│   │   └── config.py                # Environment configuration
│   ├── db/
│   │   └── session.py               # SQLModel engine, session factory, table creation
│   ├── models/
│   │   └── forecast.py              # Models
│   ├── repositories/
│   │   └── forecast_repo.py         # Repository layer (queries)
│   ├── services/
│   │   ├── forecast_service.py      # Business logic orchestration
│   │   └── kafka_producer.py        # Kafka producer
│   └── api/
│       └── endpoints/
│           └── forecasts.py         # API router
│
├── scripts/
│   └── seed_forecasts.py            # Helper to populate sample data
│
└── tests/                           # Unit & integration tests (to be added)
```

---

## Environment Variables

Configuration is managed via environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `POSTGRES_USER` | `user` | PostgreSQL login user |
| `POSTGRES_PASSWORD` | `password` | PostgreSQL login password |
| `POSTGRES_HOST` | `db` | PostgreSQL hostname (container DNS or `localhost`) |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DB` | `forecastdb` | PostgreSQL database name |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | Kafka bootstrap servers (container DNS or `localhost:9092`) |
| `KAFKA_TOPIC` | `position_changes` | Kafka topic for position-change events |

---

## Troubleshooting

### Services fail to start

**Issue:** Docker containers exit immediately after starting.

**Solution:**
1. Check logs: `docker compose logs forecast-service`
2. Ensure ports 8000, 5432, 2181, 9092 are not in use.
3. Rebuild images: `docker compose down && docker compose up --build -d`

### Database connection errors

**Issue:** "could not connect to server: Connection refused"

**Solution:**
1. Verify PostgreSQL is running: `docker compose ps postgres_db`
2. Check database URL in `app/core/config.py` matches container network name (`db` for Docker Compose).

### Kafka producer failures

**Issue:** Forecasts created but Kafka events not published.

**Solution:**
1. Verify Kafka is running: `docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list`
2. Check app logs for producer errors: `docker compose logs forecast-service | grep -i kafka`
3. Ensure `KAFKA_BOOTSTRAP_SERVERS` is correctly set (e.g., `kafka:9092` inside container).

### API returns 422 Unprocessable Entity

**Issue:** Request validation error.

**Solution:**
1. Check request body matches schema (see API Endpoints section above).
2. Ensure timestamps are ISO 8601 format: `2025-11-15T10:30:00Z`
3. Verify numeric fields (MWh) are numbers, not strings.

---

## License/Disclaimer

This project is for testing purpose only. The author is not responsible for any consequences within usage or implementation of the solution/code.

---
