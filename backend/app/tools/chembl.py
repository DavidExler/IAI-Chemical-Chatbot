from app.retrievers.chembl import get_chembl_retriever
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool, create_retriever_tool

TOOL_NAME = "chembl"
TOOL_DESCRIPTION = (
    "A wrapper around Chembl API to retrieve information about chemical molecules. "
    "Useful for when you need to answer questions about chemical molecules. "
    "Molecules need to be searched by their Chembl ID or the name of the molecule."
    'Example Queries: "CHEMBL521" or "Ibuprofen". '
    "Input should be a search query."
)


def get_chembl_tool() -> Tool:
    return create_retriever_tool(
        get_chembl_retriever(),
        TOOL_NAME,
        TOOL_DESCRIPTION,
        document_prompt=PromptTemplate.from_template(
            "Molecule {chembl_id}\n\n"
            "Molecule Properties: {molecule_properties}\n\n"
            "Molecule Type: {molecule_type}\n\n"
            "Mechanisms: {mechanisms}\n\n"
            "Name: {name}\n\n"
            "Description: {page_content}"
        ),
    )
