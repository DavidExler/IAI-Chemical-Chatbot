import datetime
from uuid import UUID

from pydantic import BaseModel


class APIChain(BaseModel):
    name: str
    description: str
    path: str
    supports_documents: bool
    tool_names: list[str]
    prompt_names: list[str]


class APIConversation(BaseModel):
    uuid: UUID
    user_uuid: UUID
    title: str
    chain: str
    prompt: str
    tools: list[str]
    documents: list[UUID]
    created_at: datetime.datetime


class APIDocument(BaseModel):
    uuid: UUID
    conversation_uuid: UUID
    title: str
    type: str
    filepath: str
    created_at: datetime.datetime
