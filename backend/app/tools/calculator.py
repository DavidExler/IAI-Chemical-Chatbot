from langchain.chains.llm_math.base import LLMMathChain
from langchain_core.language_models import BaseLLM
from langchain_core.tools import Tool

TOOL_NAME = "calculator"
TOOL_DESCRIPTION = (
    "Useful for when you need to answer questions"
    "about math. This tool is only for math questions and nothing else. Only input"
    "math expressions."
)


def get_calculator_tool(llm: BaseLLM) -> Tool:
    return Tool.from_function(
        name=TOOL_NAME,
        description=TOOL_DESCRIPTION,
        func=LLMMathChain.from_llm(llm=llm).run,
    )
