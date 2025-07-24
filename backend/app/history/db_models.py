from app.models.chain import APIConversation, APIDocument
from sqlalchemy import (
    ARRAY,
    JSON,
    TIMESTAMP,
    UUID,
    Column,
    ForeignKey,
    String,
    Text,
    text,
)
from sqlalchemy.orm import declarative_base

DEFAULT_TITLE = "New Conversation"

base = declarative_base()


class Conversation(base):
    __tablename__ = "conversations"
    __table_args__ = {"schema": "public"}

    uuid = Column(
        UUID, server_default=text("gen_random_uuid()"), nullable=False, primary_key=True
    )
    user_uuid = Column(UUID, nullable=False)
    title = Column(
        String(40), nullable=False, server_default=text(f"'{DEFAULT_TITLE}'")
    )
    chain = Column(String(255), nullable=False, server_default=text("'rag'"))
    prompt = Column(String(255), nullable=False, server_default=text("'Default'"))
    tools = Column(
        ARRAY(String), nullable=False, server_default=text("ARRAY[]::varchar[]")
    )
    documents = Column(
        ARRAY(UUID), nullable=False, server_default=text("ARRAY[]::UUID[]")
    )
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("now()"))

    def to_api(self) -> APIConversation:
        return APIConversation(
            uuid=self.uuid,
            user_uuid=self.user_uuid,
            title=self.title,
            chain=self.chain,
            prompt=self.prompt,
            tools=self.tools,
            documents=self.documents,
            created_at=self.created_at,
        )


class Message(base):
    __tablename__ = "messages"
    __table_args__ = {"schema": "public"}

    uuid = Column(
        UUID, server_default=text("gen_random_uuid()"), nullable=False, primary_key=True
    )
    conversation_uuid = Column(UUID, ForeignKey(Conversation.uuid), nullable=False)
    message = Column(JSON, nullable=False)
    intermediate_steps = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("now()"))

    @property
    def session_id(self):
        return self.uuid

    def as_dict(self):
        return {
            "uuid": self.uuid,
            "conversation_uuid": self.conversation_uuid,
            "message": self.message,
            "intermediate_steps": self.intermediate_steps,
            "created_at": self.created_at,
        }


class Document(base):
    __tablename__ = "documents"
    __table_args__ = {"schema": "public"}

    uuid = Column(
        UUID, server_default=text("gen_random_uuid()"), nullable=False, primary_key=True
    )
    conversation_uuid = Column(UUID, ForeignKey(Conversation.uuid), nullable=False)
    title = Column(String, nullable=True)
    type = Column(String, nullable=False)
    filepath = Column(Text, nullable=False, unique=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("now()"))

    def to_api(self) -> APIDocument:
        return APIDocument(
            uuid=self.uuid,
            conversation_uuid=self.conversation_uuid,
            title=self.title,
            type=self.type,
            filepath=self.filepath,
            created_at=self.created_at,
        )
