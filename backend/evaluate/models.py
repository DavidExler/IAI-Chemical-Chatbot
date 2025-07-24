from dataclasses import dataclass
from datetime import datetime, timedelta

from pydantic import BaseModel, Field
from requests import Request
from requests.auth import AuthBase


@dataclass
class BearerAuth(AuthBase):
    token: str

    def __call__(self, r: Request):
        r.headers["Authorization"] = "Bearer " + self.token
        return r


class ChatMessage(BaseModel):
    content: str
    chain: str = "rag"
    document_filenames: list[str] = Field(default_factory=list)
    prompt: str = "Default"
    tool_names: list[str] = Field(default_factory=list)
    expected_answer: str | None = None
    expect_wrong: bool = False


class Chat(BaseModel):
    name: str
    messages: list[ChatMessage]


class MessageEvaluation(BaseModel):
    message: ChatMessage
    response: str
    feedback: str | None = None
    score: float | None = None
    error: str | None = None
    duration: timedelta | None = None


class ChatEvaluation(BaseModel):
    chat_name: str
    message_evaluations: list[MessageEvaluation] = Field(default_factory=list)


class ChatEvaluations(BaseModel):
    created_at: datetime
    chat_evaluations: list[ChatEvaluation] = Field(default_factory=list)
