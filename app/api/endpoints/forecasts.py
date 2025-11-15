from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime
from typing import List, Dict, Any
from sqlmodel import Session

from app.db.session import get_session
from app.models.forecast import ForecastEstimateCreate, ForecastEstimateRead
from app.services.forecast_service import ForecastService
from app.services.kafka_producer import KafkaProducerService

router = APIRouter(prefix="/forecasts", tags=["Forecast Management"])

KAFKA_PRODUCER_INSTANCE = KafkaProducerService() 

def get_forecast_service(session: Session = Depends(get_session),) -> ForecastService:
    return ForecastService(session=session, kafka_producer=KAFKA_PRODUCER_INSTANCE)


@router.put(
    "/", 
    response_model=ForecastEstimateRead, 
    status_code=200, 
    summary="Create/Update an hourly forecast estimate"
)
async def create_or_update_forecast(
    estimate_data: ForecastEstimateCreate,
    service: ForecastService = Depends(get_forecast_service)
):
    try:
        new_estimate = await service.create_or_update_forecast(estimate_data)
        return new_estimate
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed. Error details: {e}")


@router.get(
    "/{plant_id}", 
    response_model=List[ForecastEstimateRead], 
    summary="Get forecasts for a Plant"
)
async def get_forecast(
    plant_id: str,
    start_date: datetime = Query(..., description="Start date"),
    end_date: datetime = Query(..., description="End date"),
    service: ForecastService = Depends(get_forecast_service)
):
    return await service.get_forecast(plant_id, start_date, end_date)


@router.get(
    "/company/position", 
    response_model=Dict[str, Any], 
    summary="Get company forecast position"
)
async def get_company_position(
    start_date: datetime = Query(..., description="Start date"),
    end_date: datetime = Query(..., description="End date"),
    service: ForecastService = Depends(get_forecast_service)
):
    return await service.get_company_position(start_date, end_date)