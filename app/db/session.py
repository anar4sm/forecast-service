from typing import Generator
from sqlmodel import create_engine, SQLModel, Session, select
from app.models.forecast import ForecastEstimate, PowerPlant

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
