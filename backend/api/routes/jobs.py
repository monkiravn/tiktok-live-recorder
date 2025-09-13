from fastapi import APIRouter, Depends

from backend.api.dependencies import api_key_auth
from backend.core.celery_app import celery
from backend.models.responses import JobStatusResponse, JobResult


router = APIRouter()


@router.get("/jobs/{task_id}", response_model=JobStatusResponse)
def job_status(task_id: str, api_key: str = Depends(api_key_auth)):
    res = celery.AsyncResult(task_id)
    status = res.status
    payload = None
    if res.ready():
        r = res.result
        if isinstance(r, dict):
            payload = JobResult(**r)
    return JobStatusResponse(task_id=task_id, status=status, result=payload)
