import logging
import os
import time

from app.chains.chain import Chain
from app.history.conversations import get_conversation_history
from app.prompts.code import get_prompt
from langchain_core.language_models import BaseLLM
from langchain_core.runnables import ConfigurableFieldSpec, Runnable
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import BaseTool
from langchain_openai.chat_models import ChatOpenAI

LOGGER = logging.getLogger(__name__)

MAX_NEW_TOKENS = 8192
ENDPOINT_URL = os.environ.get("LLM_INTERFACE_URL", "http://tgi-llama3-70b/")
MODEL_ID = os.environ.get("LLM_MODEL_ID", "meta-llama/Llama-3.3-70B-Instruct")


class CodeChain(Chain):
    @property
    def model_id(self) -> str:
        #return "meta-llama/Meta-Llama-3.1-70B-Instruct"
        return MODEL_ID
        #return "llama3.3-70b"

    @property
    def name(self) -> str:
        return "Coder (for Coding Tasks)"

    @property
    def description(self) -> str:
        return "This Chain is designed to help you with coding tasks."

    @property
    def path(self) -> str:
        return "code"

    @property
    def supports_documents(self) -> bool:
        return False

    @property
    def tool_names(self) -> list[str]:
        return []

    @property
    def required_auth_roles(self) -> list[str]:
        return ["coder"]

    def available_tools(self, llm: BaseLLM) -> list[BaseTool]:
        return []

    def get_chain(self) -> Runnable:
        LOGGER.info(f"Creating Python chain for model: {self.model_id}")
        chat_model = ChatOpenAI(
            openai_api_base=ENDPOINT_URL,
            openai_api_key="EMPTY",
            model_name=self.model_id,
            streaming=True,
            logprobs=True,
            top_logprobs=5,
        )

        prompt = get_prompt()

        chain = (
            {
                "input": lambda x: x["input"],
                "chat_history": lambda x: x["chat_history"],
            }
            | prompt
            | chat_model
        )

        return RunnableWithMessageHistory(
            chain,
            get_conversation_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            history_factory_config=[
                ConfigurableFieldSpec(
                    id="conversation_id",
                    annotation=str,
                    name="Conversation ID",
                    description="Unique identifier for the conversation.",
                    is_shared=True,
                ),
            ],
        )


if __name__ == "__main__":
    chain = CodeChain()
    runnable = chain.get_chain()
    print("Starting Time")
    while True:
        question = input("Enter your question: ")
        start = time.time()
        result = runnable.with_config(
            configurable={
                "user_id": 0,
                "conversation_id": 0,
                "search_kwargs": {},
            }
        ).invoke({"input": question})
        end = time.time()

        print("=" * 80)
        print(f"Model: {chain.model_id}")
        print(f"Question: {result['input']}")
        print(f"Answer: {result['output']}")
        print(f"Intermediate Steps: {result['intermediate_steps']}")
        print(f"Processing Time: {end - start:.2f}s")
