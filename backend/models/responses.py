from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class JobRef(BaseModel):
    task_id: str
    status: str


class JobResult(BaseModel):
    returncode: int
    files: List[str] = []
    s3: List[dict] = []
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class JobStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[JobResult] = None


class OkResponse(BaseModel):
    ok: bool


class FileInfo(BaseModel):
    name: str
    size: int
    mtime: float
    path: str


class FilesResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: List[FileInfo]
