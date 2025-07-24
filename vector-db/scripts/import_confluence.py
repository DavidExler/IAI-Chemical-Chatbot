import argparse
import logging
import os
import sys
from collections.abc import Iterator

import pymilvus
from atlassian import Confluence
from langchain_community.document_loaders import ConfluenceLoader
from langchain_community.document_loaders.confluence import ContentFormat
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_milvus import Milvus
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pytesseract import pytesseract

try:
    import dotenv

    dotenv.load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pytesseract.SUPPORTED_FORMATS = {
    "JPEG",
    "JPEG2000",
    "PNG",
    "PBM",
    "PGM",
    "PPM",
    "TIFF",
    "BMP",
    "GIF",
    "WEBP",
    "MPO",
}

CONFLUENCE_TOKEN = os.environ["CONFLUENCE_TOKEN"]
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "confluence_documents")
EMBEDDINGS_MODEL = "intfloat/multilingual-e5-large"
IAI_WIKI_BASE_URL = "https://iai-wiki.iai.kit.edu"
CHUNK_OVERLAP = 100
CHUNK_SIZE = 16384
host = os.environ.get("MILVUS_HOST", "127.0.0.1")
port = os.environ.get("MILVUS_PORT", "19530")
user = os.environ.get("MILVUS_ROOT_USER", "root")
password = os.environ.get("MILVUS_ROOT_PASSWORD", "Milvus")


def load_confluence_documents(space: str) -> Iterator[Document]:
    logger.debug(f"Loading documents from Confluence space {space}...")
    loader = ConfluenceLoader(
        url=IAI_WIKI_BASE_URL,
        token=CONFLUENCE_TOKEN,
        limit=999999,  # limit=999999 means no limit
        max_pages=999999,  # max_pages=999999 means no limit
        space_key=space,
        include_attachments=False,
        ocr_languages="de+eng",
        include_comments=True,
        cloud=False,
        content_format=ContentFormat.EXPORT_VIEW,
        include_restricted_content=True,
    )

    def add_title_to_content(doc: Document) -> Document:
        doc.page_content = f"Title: {doc.metadata['title']}\n\n{doc.page_content}"
        return doc

    return (add_title_to_content(d) for d in loader.lazy_load())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--force",
        help="Force the creation of the collection even if it already exists.",
        action="store_true",
        default=False,
    )
    args = parser.parse_args()

    vector_db = pymilvus.Milvus(host, port, token=f"{user}:{password}")
    if vector_db.has_collection(COLLECTION_NAME):
        if args.force:
            logger.warning("Collection already exists. Dropping it...")
            vector_db.drop_collection(COLLECTION_NAME)
        else:
            logger.info("Collection already exists. Exiting...")
            sys.exit(0)
    vector_db.close()

    confluence = Confluence(url=IAI_WIKI_BASE_URL, token=CONFLUENCE_TOKEN)
    spaces = [s["key"] for s in confluence.get_all_spaces()["results"]]

    logger.info(f"Loading Documents from Confluence Spaces: {spaces}")
    documents = (doc for space in spaces for doc in load_confluence_documents(space))

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    documents = text_splitter.split_documents(documents)

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)
    vector_db = Milvus.from_documents(
        documents,
        embeddings,
        connection_args={
            "uri": "http://milvus:19530",
            "token": f"{user}:{password}",
            #"host": host,
            #"port": port,
            #"token": f"{user}:{password}",
        },
        collection_name=COLLECTION_NAME,
    )

    logger.info(
        f"Imported {len(documents)} paragraphs from Confluence to Milvus {COLLECTION_NAME}."
    )
