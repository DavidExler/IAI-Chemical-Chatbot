import logging
import os
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from app.chains.chain import Chain
from app.history.conversations import (
    get_conversation,
    get_conversation_history,
    set_conversation_name,
)
from app.prompts.conversation_name import get_prompt
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.language_models import BaseLLM
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from langchain_openai import OpenAI

LOGGER = logging.getLogger(__name__)

ENDPOINT_URL = os.environ.get("LLM_INTERFACE_URL", "http://localhost:6666/")
MODEL_ID = os.environ.get("LLM_MODEL_ID", "meta-llama/Llama-3.3-70B-Instruct")


class ConversationNameChain(Chain):
    @property
    def model_id(self) -> str:
        #return "meta-llama/Meta-Llama-3.1-70B-Instruct"
        return MODEL_ID

    @property
    def name(self) -> str:
        return "Conversation Name Generator (internal)"

    @property
    def path(self) -> str:
        return "conversation_name"

    @property
    def tool_names(self) -> list[str]:
        return []

    def available_tools(self, _: BaseLLM) -> list[BaseTool]:
        return []

    def get_chain(self) -> Runnable:
        LOGGER.info(f"Creating Chain for {self.model_id}")
        llm = OpenAI(
            openai_api_base=ENDPOINT_URL,
            openai_api_key="EMPTY",
            model_name=self.model_id,
        )
        prompt_template = get_prompt()
        return prompt_template | llm


if __name__ == "__main__":
    chain = ConversationNameChain()
    chain = chain.get_chain()

    context = "Human Question: What is the peroxidase enzyme? Assistent Answer: Peroxidase is a large group of enzymes that break down peroxides and play a role in various biological processes. There are different types of peroxidases, including glutathione peroxidase, which protects organisms from oxidative damage, and horseradish peroxidase, which is commonly used in biochemistry applications."
    conversation_name = chain.invoke(context)["text"]
    print(conversation_name)


@dataclass
class ConversationNameCallback(AsyncCallbackHandler):
    run_metadata: dict[UUID, Any] = field(default_factory=dict)

    async def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID | None = None,
        parent_run_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ):
        if parent_run_id is None and run_id not in self.run_metadata:
            self.run_metadata[run_id] = metadata

    async def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: UUID | None = None,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ):
        if parent_run_id is None and run_id in self.run_metadata:
            metadata = self.run_metadata.pop(run_id)
            conversation_id = metadata.get("conversation_id")
            conversation = get_conversation(conversation_id)
            if conversation and conversation.title == "New Conversation":
                await self._generate_conversation_name(conversation_id)

    @staticmethod
    async def _generate_conversation_name(conversation_id: str):
        LOGGER.debug(f"Generating conversation name for conversation {conversation_id}")
        messages = await get_conversation_history(conversation_id).aget_messages()
        pretty_messages = "\n\n".join(
            f"Name: {m.name}\nContent: {m.content}" for m in messages
        )
        chain = ConversationNameChain().get_chain()
        conversation_name = (
            chain.invoke(pretty_messages).replace('"', "").replace("'", "")[:40]
        )
        LOGGER.debug(f"Generated conversation name: {conversation_name}")
        set_conversation_name(conversation_id, conversation_name)
        LOGGER.debug(f"Set conversation name for conversation {conversation_id}")
        return conversation_name
