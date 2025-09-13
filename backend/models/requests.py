from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class RecordingOptions(BaseModel):
    upload_s3: bool = False
    proxy: Optional[str] = None
    cookies: Optional[str] = None  # path to cookies.json (optional)


class CreateRecordingRequest(BaseModel):
    room_id: Optional[str] = None
    url: Optional[str] = None
    duration: Optional[int] = Field(default=None, ge=1)
    output_template: Optional[str] = None
    options: RecordingOptions = Field(default_factory=RecordingOptions)

    @field_validator("url")
    @classmethod
    def strip_url(cls, v):
        if v is None:
            return v
        v2 = v.strip()
        return v2 if v2 else None


class CreateWatcherRequest(BaseModel):
    room_id: Optional[str] = None
    url: Optional[str] = None
    poll_interval: int = Field(default=60, ge=10, le=3600)
    options: RecordingOptions = Field(default_factory=RecordingOptions)


class FilesQuery(BaseModel):
    room_id: Optional[str] = None
    url: Optional[str] = None
    from_ts: Optional[float] = Field(default=None, ge=0)
    to_ts: Optional[float] = Field(default=None, ge=0)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
