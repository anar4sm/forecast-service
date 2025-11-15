from datetime import datetime
from typing import List, Dict, Any
from app.repositories.forecast_repo import ForecastRepository
from app.models.forecast import ForecastEstimate, ForecastEstimateCreate, ForecastEstimateRead, PowerPlant
from app.services.kafka_producer import KafkaProducerService
from sqlmodel import Session, select

class ForecastService:

    def __init__(self, session: Session, kafka_producer: KafkaProducerService):
        self.repository = ForecastRepository(session)
        self.kafka_producer = kafka_producer

    async def create_or_update_forecast(self, estimate_data: ForecastEstimateCreate) -> ForecastEstimate:
        estimate = await self.repository.create_or_update_estimate(estimate_data)

        event_payload = {
            "type": "PositionChanged",
            "timestamp": datetime.now().isoformat(),
            "plant_id": estimate.plant_id,
            "forecast_hour": estimate.forecast_timestamp.isoformat(),
            "new_estimate_mwh": estimate.estimated_production_mwh
        }
        self.kafka_producer.produce_position_changed_event(event_payload)
        
        return estimate

    async def get_forecast(
        self, 
        plant_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[ForecastEstimate]:

        return await self.repository.get_forecast_by_plant_and_range(
            plant_id, start_date, end_date
        )

    async def get_company_position(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:

        all_estimates = await self.repository.get_all_forecasts_by_range(
            start_date, end_date
        )
        
        total_mwh = 0.0
        position_by_location = {loc: 0.0 for loc in ["Turkey", "Bulgaria", "Spain"]}
        
        plant_locations = {
            p.plant_id: p.location for p in self.repository.session.exec(select(PowerPlant)).all()
        }

        for estimate in all_estimates:
            production = estimate.estimated_production_mwh
            total_mwh += production
            
            location = plant_locations.get(estimate.plant_id)
            if location in position_by_location:
                position_by_location[location] += production

        response = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_forecast_mwh": round(total_mwh, 2),
            "by_location": position_by_location
        }
        return response