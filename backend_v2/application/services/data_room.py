from domain.schemas.common import ResponseMeta
from domain.schemas.data_room import DataRoomOverviewResponse


class DataRoomService:
    def get_overview(self) -> DataRoomOverviewResponse:
        return DataRoomOverviewResponse(
            sections=[],
            meta=ResponseMeta(page="data_room.overview"),
        )
