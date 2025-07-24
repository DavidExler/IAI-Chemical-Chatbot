import logging
import os
import time

from app.chains.chain import Chain
from app.helpers.agent_message_history import AgentRunnableWithMessageHistory
from app.helpers.agent_output_parser import JSONAgentOutputParser
from app.helpers.configurable_agent import ConfigurableAgentExecutor
from app.helpers.parse_tools import ParseToolNames, ParseTools
from app.helpers.retrieve_context import RetrieveContext
from app.history.conversations import get_conversation_history
from app.prompts.agent import get_biological_prompt, get_chemical_prompt, get_prompt
from app.retrievers.document_retriever import DocumentRetriever
from app.tools.arxiv import get_arxiv_tool
from app.tools.calculator import get_calculator_tool
from app.tools.chembl import get_chembl_tool
from app.tools.pubchem import get_pubchem_compound_tool, get_pubchem_substance_tool
from app.tools.vector_db import (
    get_confluence_vector_db_tool,
    get_kit_pages_vector_db_tool,
)
from app.tools.wikipedia import get_wikipedia_tool
from langchain.agents.format_scratchpad import format_log_to_messages
from langchain_core.language_models import BaseLLM
from langchain_core.runnables import ConfigurableField, ConfigurableFieldSpec, Runnable
from langchain_core.tools import BaseTool, render_text_description
from langchain_openai import OpenAI
from langchain_openai.chat_models import ChatOpenAI

LOGGER = logging.getLogger(__name__)

MAX_NEW_TOKENS = 8192
ENDPOINT_URL = os.environ.get("LLM_INTERFACE_URL", "http://tgi-llama3-70b/")
MODEL_ID = os.environ.get("LLM_MODEL_ID", "meta-llama/Llama-3.3-70B-Instruct")

class AgentChain(Chain):
    @property
    def model_id(self) -> str:
        #return "meta-llama/Meta-Llama-3.1-70B-Instruct"
        return MODEL_ID

    @property
    def name(self) -> str:
        return "Agent (Access external Data and Tools)"

    @property
    def description(self) -> str:
        return "This agent can access external data sources and tools to provide answers to your questions."

    @property
    def path(self) -> str:
        return "agent"

    @property
    def supports_documents(self) -> bool:
        return True

    @property
    def tool_names(self) -> list[str]:
        return [
            "arxiv",
            "wikipedia",
            "confluence",
            "kit_pages",
            "calculator",
            "pubchem_compound",
            "pubchem_substance",
            "chembl",
        ]

    @property
    def prompt_names(self) -> list[str]:
        return ["Default", "Chemical", "Biological"]

    def available_tools(self, llm: BaseLLM) -> list[BaseTool]:
        return [
            get_arxiv_tool(),
            get_wikipedia_tool(),
            get_confluence_vector_db_tool(),
            get_kit_pages_vector_db_tool(),
            get_calculator_tool(llm),
            get_pubchem_compound_tool(),
            get_pubchem_substance_tool(),
            get_chembl_tool(),
        ]

    def get_chain(self) -> Runnable:
        LOGGER.info(f"Creating Agent chain for model: {self.model_id}")
        llm = OpenAI(
            openai_api_base=ENDPOINT_URL,
            openai_api_key="EMPTY",
            model_name=self.model_id,
        )
        chat_model = ChatOpenAI(
            openai_api_base=ENDPOINT_URL,
            openai_api_key="EMPTY",
            model_name=self.model_id,
            streaming=True,
            logprobs=True,
            top_logprobs=5,
        )

        tools = self.available_tools(llm)
        tool_descriptions = {
            tool.name: render_text_description([tool]) for tool in tools
        }
        prompt = get_prompt().configurable_alternatives(
            ConfigurableField(id="prompt", name="Prompt", description="Prompt to use."),
            default_key="Default",
            Chemical=get_chemical_prompt(),
            Biological=get_biological_prompt(),
        )

        retriever = DocumentRetriever()

        agent = (
            {
                "input": lambda x: x["input"],
                "chat_history": lambda x: x["chat_history"],
                "agent_scratchpad": lambda x: format_log_to_messages(
                    [
                        (
                            step["output"]
                            if isinstance(step, dict) and "output" in step
                            else step
                        )
                        for step in x["intermediate_steps"]
                    ],
                ),
                "context": RetrieveContext(retriever),
                "tools": ParseTools(tool_descriptions),
                "tool_names": ParseToolNames(),
            }
            | prompt
            | chat_model
            | JSONAgentOutputParser()
        )

        return AgentRunnableWithMessageHistory(
            ConfigurableAgentExecutor(
                tools=tools, agent=agent, return_intermediate_steps=True
            ),
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
    chain = AgentChain()
    agent_executor = chain.get_chain()
    print("Starting Time")
    while True:
        question = input("Enter your question: ")
        start = time.time()
        result = agent_executor.with_config(
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
