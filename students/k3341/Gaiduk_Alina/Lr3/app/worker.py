from __future__ import annotations

from celery import Celery
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.parser import ParseRequest
from app.services.parser_client import ParserServiceError, call_parser_service


celery_app = Celery(
    "time_manager",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    beat_schedule={
        "parse-configured-url": {
            "task": "parse_periodic_url",
            "schedule": settings.periodic_parse_interval_seconds,
        },
    },
)


@celery_app.task(
    name="parse_url",
    autoretry_for=(ParserServiceError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def parse_url_task(url: str) -> dict[str, object]:
    try:
        payload = ParseRequest(url=url)
    except ValidationError as error:
        raise ParserServiceError(status_code=400, detail="Invalid URL for parsing task") from error
    return call_parser_service(payload)


@celery_app.task(
    name="parse_periodic_url",
    autoretry_for=(ParserServiceError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def parse_periodic_url_task() -> dict[str, object]:
    try:
        payload = ParseRequest(url=settings.periodic_parse_url)
    except ValidationError as error:
        raise ParserServiceError(status_code=400, detail="Invalid PERIODIC_PARSE_URL configuration") from error
    return call_parser_service(payload)
