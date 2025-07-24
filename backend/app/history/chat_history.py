import logging

from app.history.db_models import Message
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.messages import BaseMessage
from sqlalchemy import select

LOGGER = logging.getLogger(__name__)


class SQLChatHistory(SQLChatMessageHistory):
    @property
    def messages(self) -> list[BaseMessage]:
        with self._make_sync_session() as session:
            result = (
                session.query(Message)
                .where(Message.conversation_uuid == self.session_id)
                .order_by(Message.created_at.asc())
            )
            return [self.converter.from_sql_model(r) for r in result]

    async def aget_messages(self) -> list[BaseMessage]:
        """Retrieve all messages from db"""
        await self._acreate_table_if_not_exists()
        async with self._make_async_session() as session:
            stmt = (
                select(Message)
                .where(Message.conversation_uuid == self.session_id)
                .order_by(Message.created_at.asc())
            )
            result = await session.execute(stmt)
            messages = []
            for record in result.scalars():
                messages.append(self.converter.from_sql_model(record))
            return messages
