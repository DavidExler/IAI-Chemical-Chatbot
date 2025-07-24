from app.retrievers.pubchem import get_pubchem_retriever
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool, create_retriever_tool

COMPOUND_TOOL_NAME = "pubchem_compound"
COMPOUND_TOOL_DESCRIPTION = (
    "A wrapper around PubChem API to retrieve information about chemical compounds. "
    "Useful for when you need to answer questions about chemical compounds. "
    "Compounds need to be searched by their name, if you only have a molecular formula use the pubchem_substance instead."
    "If this tool does not return the information please try the pubchem_substance tool. "
    'Example Queries: "aspirin", "benzaldehyde". '
    "Input should be a search query."
)

SUBSTANCE_TOOL_NAME = "pubchem_substance"
SUBSTANCE_TOOL_DESCRIPTION = (
    "A wrapper around PubChem API to retrieve information about chemical substances. "
    "Useful for when you need to answer questions about chemical substances. "
    "If you need further information about the compound itself you can use the attached CIDs to query the pubchem_compound tool only query a single CID. "
    'Example Queries: "C9H8O4", "aspirin", "acetylsalicylic acid". '
    "Input should be a search query."
)


def get_pubchem_compound_tool() -> Tool:
    return create_retriever_tool(
        get_pubchem_retriever(domain="compound"),
        COMPOUND_TOOL_NAME,
        COMPOUND_TOOL_DESCRIPTION,
        document_prompt=PromptTemplate.from_template(
            "Compound {title}\n\n"
            "Source {source}\n\n"
            "CID: {cid}\n\n"
            "Molecular Formula: {molecular_formula}\n\n"
            "Molecular Weight: {molecular_weight}\n\n"
            "Synonyms: {synonyms}\n\n"
            "Content: {page_content}"
        ),
    )


def get_pubchem_substance_tool() -> Tool:
    return create_retriever_tool(
        get_pubchem_retriever(domain="substance"),
        SUBSTANCE_TOOL_NAME,
        SUBSTANCE_TOOL_DESCRIPTION,
        document_prompt=PromptTemplate.from_template(
            "Substance {title}\n\n"
            "Source {source}\n\n"
            "SID: {sid}\n\n"
            "Referenced CIDs: {cid}\n\n"
            "Content: {page_content}"
        ),
    )
