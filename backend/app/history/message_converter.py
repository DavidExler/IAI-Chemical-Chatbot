from typing import Any

from app.history.db_models import Message
from langchain_community.chat_message_histories.sql import BaseMessageConverter
from langchain_core.messages import BaseMessage, message_to_dict, messages_from_dict


class MessageConverter(BaseMessageConverter):
    def from_sql_model(self, sql_message: Message) -> BaseMessage:
        msg = messages_from_dict([sql_message.message])[0]
        msg.id = sql_message.uuid
        return msg

    def to_sql_model(self, message: BaseMessage, session_id: str) -> Any:
        return Message(
            conversation_uuid=session_id,
            message=message_to_dict(message),
        )

    def get_sql_model_class(self) -> Any:
        return Message
