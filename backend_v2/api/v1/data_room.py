from fastapi import APIRouter

from application.services.data_room import DataRoomService
from domain.schemas.data_room import DataRoomOverviewResponse

router = APIRouter(prefix="/data-room", tags=["data_room"])
service = DataRoomService()


@router.get("/overview", response_model=DataRoomOverviewResponse)
def get_data_room_overview() -> DataRoomOverviewResponse:
    return service.get_overview()
