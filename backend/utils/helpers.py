from __future__ import annotations

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple

from backend.core.config import get_settings


def ensure_tlr_on_path():
    settings = get_settings()
    if settings.TLR_ROOT not in sys.path:
        sys.path.insert(0, settings.TLR_ROOT)


def now_ts() -> float:
    return time.time()


def list_recording_files(
    base_dir: str, ts_from: Optional[float] = None, ts_to: Optional[float] = None
) -> List[str]:
    paths: List[str] = []
    for root, _dirs, files in os.walk(base_dir):
        for f in files:
            p = os.path.join(root, f)
            try:
                st = os.stat(p)
            except FileNotFoundError:
                continue
            if ts_from is not None and st.st_mtime < ts_from:
                continue
            if ts_to is not None and st.st_mtime > ts_to:
                continue
            paths.append(p)
    return paths


def resolve_user_room(
    url: Optional[str],
    room_id: Optional[str],
    proxy: Optional[str],
    cookies: Optional[dict],
) -> Tuple[str, str]:
    """Resolve (user, room_id) using upstream TikTokAPI.

    Falls back between url and room_id if needed.
    """
    ensure_tlr_on_path()
    from core.tiktok_api import TikTokAPI

    api = TikTokAPI(proxy=proxy, cookies=cookies)
    user: Optional[str] = None
    rid: Optional[str] = room_id

    if url:
        user, rid = api.get_room_and_user_from_url(url)
    if not rid and user:
        rid = api.get_room_id_from_user(user)
    if not user and rid:
        user = api.get_user_from_room_id(rid)
    if not user or not rid:
        raise ValueError("Unable to resolve user/room_id from inputs")
    return user, rid


def load_cookies_from_path(path: Optional[str]) -> Optional[dict]:
    if not path:
        return None
    with open(path, "r") as f:
        return json.load(f)


def run_recording(
    url: Optional[str],
    room_id: Optional[str],
    duration: Optional[int],
    output_dir: str,
    proxy: Optional[str],
    cookies: Optional[dict],
    use_telegram: bool = False,
) -> Tuple[int, List[str]]:
    """Run a single recording session using upstream TikTokRecorder.

    Returns (returncode, files_created)
    """
    ensure_tlr_on_path()
    from core.tiktok_recorder import TikTokRecorder
    from utils.enums import Mode
    from backend.services.process_manager import ProcessManager
    from backend.utils.logging import get_logger

    logger = get_logger(__name__)

    # Determine resolved identifiers and measure files before/after
    start_ts = now_ts() - 1
    files_before = set(list_recording_files(output_dir))

    # Build a recorder; we pass url/room_id and let it resolve user/room
    rec = TikTokRecorder(
        url=url,
        user=None,
        room_id=room_id,
        mode=Mode.MANUAL,
        automatic_interval=60,
        cookies=cookies,
        proxy=proxy,
        output=output_dir,
        duration=duration,
        use_telegram=use_telegram,
    )

    rc = 0
    try:
        # Use ProcessManager for safer execution
        process_manager = ProcessManager(
            timeout=duration + 300 if duration else 3600
        )  # Add 5min buffer or 1h default

        # For now, we still call rec.run() directly since it's the existing interface
        # TODO: Could be refactored to use subprocess directly for better control
        rec.run()

    except Exception as e:
        logger.exception(
            "Recording failed",
            extra={
                "url": url,
                "room_id": room_id,
                "duration": duration,
                "error": str(e),
            },
        )
        rc = 1

    end_ts = now_ts() + 1
    files_after = set(list_recording_files(output_dir, ts_from=start_ts, ts_to=end_ts))
    created = sorted(list(files_after - files_before))

    logger.info(
        "Recording completed",
        extra={"returncode": rc, "files_created": len(created), "files": created},
    )

    return rc, created


def paginate(items: List[str], page: int, page_size: int) -> List[str]:
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end]


def to_fileinfo(path: str) -> Dict:
    st = os.stat(path)
    return {
        "name": os.path.basename(path),
        "size": st.st_size,
        "mtime": st.st_mtime,
        "path": path,
    }
