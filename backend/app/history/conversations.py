import logging
import os
import warnings

from app.history.chat_history import SQLChatHistory
from app.history.db_models import Conversation, Document, Message
from app.history.documents import delete_document
from app.history.message_converter import MessageConverter
from app.models.chain import APIConversation
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

LOGGER = logging.getLogger(__name__)

CHAT_HISTORY_DB_CONNECTION = os.environ.get("CHAT_HISTORY_DB", "sqlite:///sqlite.db")


class ConversationSettings(BaseModel):
    selected_chain: str | None = None
    selected_prompt: str | None = None
    selected_tools: list[str] | None = None
    selected_documents: list[str] | None = None


def create_conversation(user_id: str) -> APIConversation:
    LOGGER.debug(f"Creating conversation for user {user_id}")
    engine = create_engine(CHAT_HISTORY_DB_CONNECTION, echo=False)
    with Session(engine) as session:
        model = Conversation(user_uuid=user_id)
        session.add(model)
        session.commit()
        return model.to_api()


def get_conversations(user_id: str) -> list[Conversation]:
    LOGGER.debug(f"Getting conversations for user {user_id}")
    engine = create_engine(CHAT_HISTORY_DB_CONNECTION, echo=False)
    with Session(engine) as session:
        conversations = (
            session.query(Conversation)
            .where(Conversation.user_uuid == user_id)
            .order_by(Conversation.created_at.desc())
        )
        return [c for c in conversations]


def get_conversation(conversation_id: str) -> Conversation | None:
    LOGGER.debug(f"Getting conversations {conversation_id}")
    engine = create_engine(CHAT_HISTORY_DB_CONNECTION, echo=False)
    with Session(engine) as session:
        conversations = session.query(Conversation).where(
            Conversation.uuid == conversation_id
        )
        return next(iter(conversations), None)


def get_message(message_id: str) -> Message | None:
    LOGGER.debug(f"Getting message {message_id}")
    engine = create_engine(CHAT_HISTORY_DB_CONNECTION, echo=False)
    with Session(engine) as session:
        messages = session.query(Message).where(Message.uuid == message_id)
        return next(iter(messages), None)


def set_conversation_name(conversation_id: str, conversation_name: str):
    LOGGER.debug(
        f"Setting conversation name for {conversation_id} to {conversation_name}"
    )
    engine = create_engine(CHAT_HISTORY_DB_CONNECTION, echo=False)
    with Session(engine) as session:
        conversation = session.query(Conversation).where(
            Conversation.uuid == conversation_id
        )
        conversation.update({"title": conversation_name})
        session.commit()


def set_conversation_settings(conversation_id: str, settings: ConversationSettings):
    LOGGER.debug(f"Set conversation settings for {conversation_id} to {settings}")
    engine = create_engine(CHAT_HISTORY_DB_CONNECTION, echo=False)
    with Session(engine) as session:
        conversation = session.query(Conversation).where(
            Conversation.uuid == conversation_id
        )
        conversation.update(
            {
                **(
                    {"chain": settings.selected_chain}
                    if settings.selected_chain is not None
                    else {}
                ),
                **(
                    {"prompt": settings.selected_prompt}
                    if settings.selected_prompt is not None
                    else {}
                ),
                **(
                    {"tools": settings.selected_tools}
                    if settings.selected_tools is not None
                    else {}
                ),
                **(
                    {"documents": settings.selected_documents}
                    if settings.selected_documents is not None
                    else {}
                ),
            }
        )
        session.commit()


def get_conversation_history(conversation_id: str) -> SQLChatHistory:
    LOGGER.debug(f"Getting conversation history for conversation {conversation_id}")
    return SQLChatHistory(
        session_id=conversation_id,
        session_id_field_name="conversation_uuid",
        connection_string=CHAT_HISTORY_DB_CONNECTION,
        custom_message_converter=MessageConverter(),
        async_mode=True,
    )


def delete_conversation(user_id: str, conversation_id: str):
    LOGGER.debug(f"Deleting conversation {conversation_id} for user {user_id}")
    engine = create_engine(CHAT_HISTORY_DB_CONNECTION, echo=False)
    with Session(engine) as session:
        conversation = session.query(Conversation).where(
            Conversation.user_uuid == user_id,
            Conversation.uuid == conversation_id,
        )
        documents = session.query(Document).where(
            Document.conversation_uuid == conversation_id,
        )
        for document in documents:
            try:
                delete_document(document)
            except OSError:
                warnings.warn(f"Failed to delete document {document.filepath}")

        conversation.delete()
        session.commit()
