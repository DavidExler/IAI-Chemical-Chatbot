from app.retrievers.vector_db import get_vector_db_retriever
from app.tools.configurable_tool import ConfigurableRetrieverTool
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import ConfigurableField
from langchain_core.tools import BaseTool, Tool, create_retriever_tool

CONFLUENCE_TOOL_NAME = "confluence"
CONFLUENCE_TOOL_DESCRIPTION = """
Vector database wrapper
The vector database contains data from the internal wiki of the institute IAI which is part of the KIT.
It contains information about projects, publications, and personnel.
Most of the pages are in german, so it would be good if you can provide your query in german, but english should work as well.
Querying only for a part of the real query could also bring some new results.
This tool only accepts a string, please be very specific with your query and rather provide more context than less.
If a query doesn't return any results, please try again with more details or try the kit_pages tool.
"""

KIT_PAGES_TOOL_NAME = "kit_pages"
KIT_PAGES_TOOL_DESCRIPTION = """
Vector database wrapper
The vector database contains data that got crawled from the KIT, SCC and IAI websites.
It contains information about the university, the SCC, the IAI, and the KIT.
Most of the pages are in german, so it would be good if you can provide your query in german, but english should work as well.
Querying only for a part of the real query could also bring some new results.
This tool only accepts a string, please be specific with your query and rather provide more context than less.
If a query doesn't return any results, please try again with more details or try the confluence tool.
"""


def get_confluence_vector_db_tool() -> BaseTool:
    retriever = get_vector_db_retriever(
        collection_name="confluence_documents", k=2
    ).configurable_alternatives(
        ConfigurableField(
            id="confluence_private",
            name="Confluence Private",
            description="Whether to include private confluence documents",
        ),
        default_key="public",
        private=get_vector_db_retriever(
            collection_name="confluence_documents_private", k=2
        ),
    )
    return ConfigurableRetrieverTool(
        retriever=retriever,
        document_prompt=PromptTemplate.from_template("Source {source}: {page_content}"),
        name=CONFLUENCE_TOOL_NAME,
        description=CONFLUENCE_TOOL_DESCRIPTION,
    )


def get_kit_pages_vector_db_tool() -> Tool:
    retriever = get_vector_db_retriever(collection_name="kit_pages", k=2)
    return create_retriever_tool(
        retriever,
        KIT_PAGES_TOOL_NAME,
        KIT_PAGES_TOOL_DESCRIPTION,
        document_prompt=PromptTemplate.from_template("Source {source}: {page_content}"),
    )
