from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

from app.schemas.parser import ParseRequest, ParseResponse, ParseTaskCreated, ParseTaskStatus
from app.services.parser_client import ParserServiceError, call_parser_service
from app.worker import celery_app, parse_url_task


router = APIRouter(prefix="/parser", tags=["parser"])


def _validate_parse_response(data: object) -> ParseResponse:
    try:
        return ParseResponse.model_validate(data)
    except ValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Parser service returned unexpected response format",
        ) from error


@router.post("/parse", response_model=ParseResponse)
def parse_url(payload: ParseRequest) -> ParseResponse:
    try:
        data = call_parser_service(payload)
    except ParserServiceError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error

    return _validate_parse_response(data)


@router.post("/parse/async", response_model=ParseTaskCreated, status_code=status.HTTP_202_ACCEPTED)
def parse_url_async(payload: ParseRequest) -> ParseTaskCreated:
    task = parse_url_task.delay(str(payload.url))
    return ParseTaskCreated(task_id=task.id, status=task.status)


@router.get("/parse/async/{task_id}", response_model=ParseTaskStatus)
def get_parse_task(task_id: str) -> ParseTaskStatus:
    task = AsyncResult(task_id, app=celery_app)

    if task.successful():
        return ParseTaskStatus(
            task_id=task_id,
            status=task.status,
            result=_validate_parse_response(task.result),
        )

    if task.failed():
        return ParseTaskStatus(task_id=task_id, status=task.status, error=str(task.result))

    return ParseTaskStatus(task_id=task_id, status=task.status)
