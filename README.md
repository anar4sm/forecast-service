# Forecast Service

A production-ready microservice for managing energy production forecasts across multiple power plants with real-time event streaming.

## Overview

The **Forecast Service** is a RESTful API built with **FastAPI** and **PostgreSQL** that enables:
- Creating and updating hourly forecast estimates for power plants
- Querying historical forecasts by plant or aggregated company-wide
- Publishing position change events to **Kafka** for downstream consumption (real-time dashboards, analytics, etc.)

The service follows a strict **layered architecture** (Controller → Service → Repository → Database) ensuring separation of concerns, testability, and maintainability.

---

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Runtime** | Python | 3.11+ | Application runtime |
| **Web Framework** | FastAPI | Latest | RESTful API framework; async request handling |
| **Database** | PostgreSQL | 15-alpine | Primary data store |
| **ORM / Data Access** | SQLModel | Latest | SQLAlchemy-based models; Pydantic integration |
| **Event Streaming** | Apache Kafka | 7.5.0 (Confluent) | Publish position-change events |
| **Async Driver** | psycopg (async) | 3.x | PostgreSQL async client |
| **Config Management** | python-dotenv | Latest | Environment variable loading |
| **Orchestration** | Docker Compose | 3.8+ | Local multi-container environment |

---

## Layered Architecture

The service is organized into clear layers, each with a single responsibility:

```
┌─────────────────────────────────────────────────────────┐
│           HTTP / REST Layer (FastAPI)                   │
│   app/api/endpoints/forecasts.py                        │
└──────────────────────┬──────────────────────────────────┘
                       │ (request/response)
┌──────────────────────▼──────────────────────────────────┐
│        Service / Business Logic Layer                    │
│   app/services/forecast_service.py                      │
│   • Orchestrates repository & producer calls            │
│   • Emits Kafka events on state changes                 │
└──────────────────────┬──────────────────────────────────┘
                       │ (commands)
┌──────────────────────▼──────────────────────────────────┐
│      Data Access / Repository Layer                      │
│   app/repositories/forecast_repo.py                     │
│   • Encapsulates all SQL queries                        │
│   • Handles upserts, aggregations, filtering            │
└──────────────────────┬──────────────────────────────────┘
                       │ (SQL)
┌──────────────────────▼──────────────────────────────────┐
│         Database & Infrastructure Layer                  │
│   app/db/session.py — SQLModel engine, sessions         │
│   app/models/forecast.py — SQLModel entities            │
│   app/services/kafka_producer.py — Event producer       │
│   app/core/config.py — Environment configuration        │
└──────────────────────┬──────────────────────────────────┘
                       │ (connections)
                ┌──────┴────────┐
                │               │
         ┌──────▼─────┐   ┌────▼──────┐
         │ PostgreSQL │   │   Kafka   │
         └────────────┘   └───────────┘
```

### Layer Responsibilities

- **API / Endpoints** (`app/api/endpoints/forecasts.py`)
  - Handle HTTP requests/responses
  - Validate input schemas via Pydantic
  - Wire dependencies (session, service)
  - Return structured JSON responses

- **Service** (`app/services/forecast_service.py`)
  - Orchestrate repository and producer calls
  - Implement business rules and workflows
  - Emit domain events (Kafka publish)
  - Coordinate multi-step operations

- **Repository** (`app/repositories/forecast_repo.py`)
  - Execute SQL queries and mutations
  - Provide query builders for filtering/aggregation
  - Abstract database schema from service layer

- **Models** (`app/models/forecast.py`)
  - SQLModel ORM classes (map to DB tables)
  - Pydantic schemas for validation
  - Serialization/deserialization logic

- **Config & Infrastructure** (`app/core/config.py`, `app/db/session.py`, `app/services/kafka_producer.py`)
  - Read environment variables
  - Manage database connections and sessions
  - Configure and manage Kafka producer

---

## API Endpoints

### 1. Create or Update Forecast Estimate

```
PUT /forecasts/
Content-Type: application/json

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
  "breakdown_by_location": {
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

### Option 1: Docker Compose (Recommended)

#### 1. Clone and navigate to the project:

```powershell
cd C:\Dev\forecast-service
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
- Seed initial power plants
- Start the Uvicorn server on `http://localhost:8000`

---

## Seeding Test Data

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

### Test API Endpoints (Browser Console)

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

#### Use kcat for quick inspection:

```powershell
docker run --rm edenhill/kcat:1.7.0 -b localhost:9092 -t position_changes -C -o beginning -c 10
```

---

## Project Structure

```
forecast-service/
├── Dockerfile                       # App container image
├── docker-compose.yml               # Multi-container orchestration (app, DB, Kafka)
├── requirements.txt                 # Python dependencies
├── .env.example                     # Example environment variables
├── README.md                        # This file
├── CLASSES.md                       # Class & module reference manual
├── DIAGRAM.md                       # Architecture & sequence diagrams
│
├── app/
│   ├── main.py                      # FastAPI app, startup/shutdown hooks
│   ├── core/
│   │   └── config.py                # Environment configuration
│   ├── db/
│   │   └── session.py               # SQLModel engine, session factory, table creation
│   ├── models/
│   │   └── forecast.py              # ORM models & Pydantic schemas
│   ├── repositories/
│   │   └── forecast_repo.py         # Data access layer (queries, upserts)
│   ├── services/
│   │   ├── forecast_service.py      # Business logic orchestration
│   │   └── kafka_producer.py        # Kafka producer wrapper
│   └── api/
│       └── endpoints/
│           └── forecasts.py         # API route handlers
│
├── scripts/
│   └── seed_forecasts.py            # Helper to populate sample forecasts
│
└── tests/                           # Unit & integration tests (to be expanded)
```

---

## Environment Variables

Configuration is managed via environment variables (loaded by `app/core/config.py`):

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

## Development & Contributing

### Running Tests (WIP)

```powershell
pytest tests/ -v
```

### Code Style & Linting

```powershell
black app/ scripts/
flake8 app/ scripts/
```

### Adding New Endpoints

1. Define request/response schemas in `app/models/forecast.py`
2. Add repository methods in `app/repositories/forecast_repo.py`
3. Add service methods in `app/services/forecast_service.py`
4. Add route handler in `app/api/endpoints/forecasts.py`
5. Wire dependencies via `Depends()`

---

## Additional Documentation

- **Class & Module Reference:** See [`CLASSES.md`](CLASSES.md) for detailed descriptions of each class, variable, and method.
- **Architecture Diagrams:** See [`DIAGRAM.md`](DIAGRAM.md) for Mermaid flowcharts and sequence diagrams.

---

## License

This project is proprietary. All rights reserved.

---

## Support

For questions or issues, contact the development team or refer to the troubleshooting section above.