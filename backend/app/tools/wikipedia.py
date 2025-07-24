from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import BaseTool


def get_wikipedia_tool() -> BaseTool:
    return WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
