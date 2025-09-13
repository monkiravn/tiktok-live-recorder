import os
from typing import Optional
from fastapi import APIRouter, Depends, Query

from backend.api.dependencies import api_key_auth
from backend.core.config import get_settings
from backend.models.responses import FilesResponse, FileInfo
from backend.utils.helpers import list_recording_files, paginate, to_fileinfo


router = APIRouter()


@router.get("/files", response_model=FilesResponse)
def list_files(
    api_key: str = Depends(api_key_auth),
    room_id: Optional[str] = Query(default=None),
    url: Optional[str] = Query(default=None),
    from_ts: Optional[float] = Query(default=None, alias="from"),
    to_ts: Optional[float] = Query(default=None, alias="to"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    # Basic listing; filtering by room_id/url depends on naming templates.
    # For now, we filter by simple substring match if provided.
    settings = get_settings()
    all_files = list_recording_files(
        settings.RECORDINGS_DIR, ts_from=from_ts, ts_to=to_ts
    )
    if room_id:
        all_files = [p for p in all_files if room_id in os.path.basename(p)]
    if url:
        # We don't embed URL into filename; ignore or future-enhance with index.
        pass

    all_files.sort(key=lambda p: os.stat(p).st_mtime, reverse=True)
    total = len(all_files)
    page_items = paginate(all_files, page, page_size)
    items = [FileInfo(**to_fileinfo(p)) for p in page_items]
    return FilesResponse(page=page, page_size=page_size, total=total, items=items)
