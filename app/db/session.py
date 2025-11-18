from typing import Generator
from sqlmodel import create_engine, SQLModel, Session, select
from app.models.forecast import ForecastEstimate, PowerPlant
from datetime import datetime, timedelta

DATABASE_URL = "postgresql+psycopg://user:password@db:5432/forecastdb" 

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

def seed_initial_data(session: Session) -> None:
    if session.exec(select(PowerPlant)).first():
        return

    plants = [
        PowerPlant(plant_id="TR_001", name="Turkey Plant", location="Turkey", capacity_mwh=100.0),
        PowerPlant(plant_id="BG_001", name="Bulgaria Plant", location="Bulgaria", capacity_mwh=80.0),
        PowerPlant(plant_id="ES_001", name="Spain Plant", location="Spain", capacity_mwh=120.0),
    ]

    session.add_all(plants)
    session.commit()

def seed_initial_forecasts(session: Session) -> None:
    if session.exec(select(ForecastEstimate)).first():
        return
    
    start = datetime(datetime.now().year, datetime.now().month, datetime.now().day, 0, 0)
    
    payloads = []
    
    for hour in range(24):
        ts = (start + timedelta(hours=hour)).isoformat() + "Z"
        payloads.extend(
            [
                ForecastEstimate(plant_id="TR_001", forecast_timestamp=ts, estimated_production_mwh=50 + hour * 0.5),
                ForecastEstimate(plant_id="BG_001", forecast_timestamp=ts, estimated_production_mwh=30 + hour * 0.3),
                ForecastEstimate(plant_id="ES_001", forecast_timestamp=ts, estimated_production_mwh=20 + hour * 0.2)
            ]
        )
    
    session.add_all(payloads)
    session.commit()

    print("Done. Test data loaded.")
