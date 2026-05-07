from __future__ import annotations

from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl


DEFAULT_TIMEOUT_SECONDS = 10

app = FastAPI(title="Parser Service", version="0.1.0")


class ParseRequest(BaseModel):
    url: HttpUrl


class ParseResponse(BaseModel):
    url: str
    title: str


class TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._inside_title = False
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self._inside_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._inside_title = False

    def handle_data(self, data: str) -> None:
        if self._inside_title:
            self._parts.append(data)

    @property
    def title(self) -> str | None:
        title = " ".join(part.strip() for part in self._parts if part.strip())
        return " ".join(title.split()) or None


def fetch_html(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; LR3Parser/1.0)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )

    try:
        with urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            body = response.read()
    except HTTPError as error:
        raise HTTPException(status_code=502, detail=f"HTTP error {error.code}") from error
    except (TimeoutError, URLError) as error:
        raise HTTPException(status_code=502, detail=f"Failed to load URL: {error}") from error

    return body.decode(charset, errors="replace")


def extract_title(html: str) -> str:
    parser = TitleParser()
    parser.feed(html)

    if parser.title is None:
        raise HTTPException(status_code=422, detail="HTML page does not contain a title")

    return parser.title


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/parse", response_model=ParseResponse, tags=["parser"])
def parse_page(payload: ParseRequest) -> ParseResponse:
    url = str(payload.url)
    html = fetch_html(url)
    return ParseResponse(url=url, title=extract_title(html))
