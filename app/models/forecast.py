from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class PowerPlant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plant_id: str = Field(index=True, unique=True)
    name: str
    location: str
    capacity_mwh: float

class ForecastEstimate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plant_id: str = Field(index=True)
    forecast_timestamp: datetime = Field(index=True)
    estimated_production_mwh: float
    submission_timestamp: datetime = Field(default_factory=datetime.now)

class ForecastEstimateCreate(SQLModel):
    plant_id: str
    forecast_timestamp: datetime
    estimated_production_mwh: float

class ForecastEstimateRead(ForecastEstimate):
    pass