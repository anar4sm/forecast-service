from datetime import datetime
from typing import List, Optional
from sqlmodel import Session, select
from app.models.forecast import ForecastEstimate, ForecastEstimateCreate, PowerPlant

class ForecastRepository:
    def __init__(self, session: Session):
        self.session = session

    async def create_or_update_estimate(self, estimate_data: ForecastEstimateCreate) -> ForecastEstimate:
     
        #Checking for an existing estimate for the specific plant and hour
        stmt = select(ForecastEstimate).where(
            ForecastEstimate.plant_id == estimate_data.plant_id,
            ForecastEstimate.forecast_timestamp == estimate_data.forecast_timestamp
        )
        existing = self.session.exec(stmt).first()

        if existing:
            #TRUE: Update existing estimate
            existing.estimated_production_mwh = estimate_data.estimated_production_mwh
            existing.submission_timestamp = datetime.now()
            self.session.add(existing)
            record = existing
        else:
            #FALSE: Create new estimate
            record = ForecastEstimate.model_validate(estimate_data)
            self.session.add(record)

        self.session.commit()
        self.session.refresh(record)
        return record

    async def get_forecast_by_plant_and_range(
        self, 
        plant_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[ForecastEstimate]:
        statement = select(ForecastEstimate).where(
            ForecastEstimate.plant_id == plant_id,
            ForecastEstimate.forecast_timestamp >= start_date,
            ForecastEstimate.forecast_timestamp < end_date
        ).order_by(ForecastEstimate.forecast_timestamp)
        
        results = self.session.exec(statement).all()
        return results

    async def get_all_forecasts_by_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[ForecastEstimate]:
        statement = select(ForecastEstimate).where(
            ForecastEstimate.forecast_timestamp >= start_date,
            ForecastEstimate.forecast_timestamp < end_date
        ).order_by(ForecastEstimate.forecast_timestamp)

        results = self.session.exec(statement).all()
        return results

    async def get_all_plant_ids(self) -> List[str]:
        statement = select(PowerPlant.plant_id)
        results = self.session.exec(statement).all()
        return results