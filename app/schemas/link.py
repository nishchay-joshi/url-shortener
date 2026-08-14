from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class CreateLinkRequest(BaseModel):
    original_url: HttpUrl
    expires_at: datetime | None = None


class LinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    short_code: str
    short_url: HttpUrl
    original_url: HttpUrl
    expires_at: datetime | None
    created_at: datetime
    is_active: bool