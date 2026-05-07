from pydantic import BaseModel, HttpUrl


class ParseRequest(BaseModel):
    url: HttpUrl


class ParseResponse(BaseModel):
    url: str
    title: str


class ParseTaskCreated(BaseModel):
    task_id: str
    status: str


class ParseTaskStatus(BaseModel):
    task_id: str
    status: str
    result: ParseResponse | None = None
    error: str | None = None
