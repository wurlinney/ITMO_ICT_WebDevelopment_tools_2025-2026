from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings
from app.schemas.parser import ParseRequest


class ParserServiceError(RuntimeError):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _extract_error_detail(raw_detail: str) -> str:
    if not raw_detail:
        return "Parser service error"

    try:
        payload = json.loads(raw_detail)
    except json.JSONDecodeError:
        return raw_detail

    detail = payload.get("detail") if isinstance(payload, dict) else None
    if isinstance(detail, str):
        return detail

    return raw_detail


def call_parser_service(payload: ParseRequest) -> dict[str, object]:
    url = f"{settings.parser_service_url.rstrip('/')}/parse"
    body = payload.model_dump_json().encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=15) as response:
            response_body = response.read().decode("utf-8")
    except HTTPError as error:
        detail = _extract_error_detail(error.read().decode("utf-8", errors="replace"))
        raise ParserServiceError(status_code=error.code, detail=detail) from error
    except (TimeoutError, URLError) as error:
        raise ParserServiceError(status_code=503, detail=f"Parser service is unavailable: {error}") from error

    try:
        data = json.loads(response_body)
    except json.JSONDecodeError as error:
        raise ParserServiceError(status_code=502, detail="Parser service returned invalid JSON") from error

    if not isinstance(data, dict):
        raise ParserServiceError(status_code=502, detail="Parser service returned invalid response")

    return data
