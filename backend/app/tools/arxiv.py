from langchain_community.retrievers import ArxivRetriever
from langchain_core.tools import Tool, create_retriever_tool

TOOL_NAME = "arxiv"
TOOL_DESCRIPTION = (
    "A wrapper around Arxiv.org "
    "Useful for when you need to answer questions about Physics, Mathematics, "
    "Computer Science, Quantitative Biology, Quantitative Finance, Statistics, "
    "Electrical Engineering, and Economics "
    "from scientific articles on arxiv.org. "
    "Input should be a search query."
)


def get_arxiv_tool() -> Tool:
    retriever = ArxivRetriever(
        get_full_documents=True, doc_content_chars_max=None, load_max_docs=3
    )
    return create_retriever_tool(retriever, TOOL_NAME, TOOL_DESCRIPTION)
