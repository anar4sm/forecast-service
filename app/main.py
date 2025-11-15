from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.session import create_db_and_tables, engine, seed_initial_data, Session
from app.api.endpoints import forecasts

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Startup: Creating DB tables and loading test data")
    create_db_and_tables()
    
    # Seed initial plants (Turkey, Bulgaria, Spain)
    with Session(engine) as session:
        seed_initial_data(session)
        
    yield
    print("Shutdown: Cleanup completed.")

app = FastAPI(
    title="Forecast Service API",
    version="1.0.0",
    description="Microservice for managing forecasts."
)

app.include_router(forecasts.router, prefix="/api/v1")

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Forecast Service API"}