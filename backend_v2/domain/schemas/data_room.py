from pydantic import BaseModel, Field

from domain.schemas.common import ResponseMeta


class DataRoomOverviewResponse(BaseModel):
    sections: list[dict[str, str | int | float | bool | None]] = Field(default_factory=list)
    meta: ResponseMeta
