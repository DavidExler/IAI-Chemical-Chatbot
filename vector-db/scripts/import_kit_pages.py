import argparse
import logging
import os
import sys
from urllib.parse import urljoin

import more_itertools
import pymilvus
import requests
from bs4 import BeautifulSoup
from langchain_community.document_transformers import Html2TextTransformer
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_milvus import Milvus
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tqdm import tqdm

try:
    import dotenv

    dotenv.load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)


COLLECTION_NAME = "kit_pages"
EMBEDDINGS_MODEL = "intfloat/multilingual-e5-large"
host = os.environ.get("MILVUS_HOST", "127.0.0.1")
port = os.environ.get("MILVUS_PORT", "19530")
user = os.environ.get("MILVUS_ROOT_USER", "root")
password = os.environ.get("MILVUS_ROOT_PASSWORD", "Milvus")
CHUNK_OVERLAP = 100
CHUNK_SIZE = 16384


def remove_anchor_tag(url: str) -> str:
    if "#" in url:
        url = url.split("#")[0]
    return url


def is_valid_url(url: str) -> bool:
    if not url.startswith("http"):
        return False
    if url.endswith("pdf") or url.endswith("jpg") or url.endswith("png"):
        return False
    if "/downloads/" in url:
        return False
    if "emailform" in url:
        return False
    if "/personen/" in url:
        return False
    if url.endswith(".zip"):
        return False
    if "events" in url and "reminder" in url:
        return False
    if "www.cammp.online" in url:
        return False
    return (
        "://www.kit.edu" in url
        or "://www.scc.kit.edu" in url
        or "://www.iai.kit.edu" in url
    )


def transform_url(url: str) -> str:
    # remove query args
    url = url.split("?")[0]
    return url


def build_metadata(soup: BeautifulSoup, url: str) -> dict:
    metadata = {"source": url, "title": "", "description": "", "language": ""}
    if title := soup.find("title"):
        metadata["title"] = title.get_text()
    if description := soup.find("meta", attrs={"name": "description"}):
        metadata["description"] = description.get("content", "No description found.")
    if html := soup.find("html"):
        metadata["language"] = html.get("lang", "No language found.")
    return metadata


def load_webpage(url: str, soup: BeautifulSoup) -> Document | None:
    try:
        metadata = build_metadata(soup, url)
        [x.extract() for x in soup.findAll("header")]
        [x.extract() for x in soup.findAll("footer")]
        [x.extract() for x in soup.select("[role=navigation]")]
        page_content = f"Title: {metadata['title']}\n\n{str(soup)}"
        return Document(page_content=page_content, metadata=metadata)
    except Exception as e:
        print(f"Error loading url {url}: {e}")
        return None


def crawl():
    html2text = Html2TextTransformer()
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    vector_db = Milvus(
        embeddings,
        connection_args={
            "uri": "http://milvus:19530",
            "token": f"{user}:{password}",
            #"host": host,
            #"port": port,
            #"token": f"{user}:{password}",
        },
        collection_name=COLLECTION_NAME,
        auto_id=True,
    )

    documents = crawl_documents()

    unique_document_content = set()
    for documents_chunk in more_itertools.chunked(documents, 10):
        docs = html2text.transform_documents(list(documents_chunk))

        unique_documents = []
        for document in docs:
            if document.page_content not in unique_document_content:
                unique_document_content.add(document.page_content)
                unique_documents.append(document)

        docs = text_splitter.split_documents(unique_documents)
        try:
            vector_db.add_texts(
                texts=[d.page_content for d in docs],
                metadatas=[d.metadata for d in docs],
            )
        except Exception as e:
            logger.error(f"Failed to import documents: {e}")
            continue

        logger.info(
            f"Imported {len(docs)} paragraphs from KIT Pages to Milvus {COLLECTION_NAME}."
        )


def crawl_documents():
    urls_to_visit = {"https://www.kit.edu"}
    visited_urls = set()
    pbar = tqdm(total=1, dynamic_ncols=True, desc="Crawling")
    session = requests.Session()
    while urls_to_visit:
        pbar.update(1)
        pbar.total = len(urls_to_visit) + len(visited_urls)
        print(pbar)

        current_url = urls_to_visit.pop()
        if not is_valid_url(current_url):
            continue

        try:
            response = session.get(current_url, timeout=5)
            if "text/html" not in response.headers.get("content-type", "text/html"):
                print(
                    f"Skipping {current_url} because it is not an HTML page, but {response.headers.get('content-type')}"
                )
                continue
            print(f"Page: {current_url} Size: {len(response.content)}")
            soup = BeautifulSoup(response.text, "lxml")

            if (
                "page not found" not in response.text.lower()
                and "seite nicht gefunden" not in response.text.lower()
            ):
                if document := load_webpage(current_url, soup):
                    yield document

            link_elements = soup.select("a[href]")
            urls = {
                remove_anchor_tag(urljoin(current_url, elem["href"])).lower()
                for elem in link_elements
            }
            urls = {transform_url(url) for url in urls}
            valid_urls = {url for url in urls if is_valid_url(url)} - visited_urls
            for url in valid_urls:
                urls_to_visit.add(url)

            visited_urls.add(current_url)
        except Exception as e:
            print(f"Failed to crawl {current_url}: {e}")
            continue


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--force",
        help="Force the crawler to re-crawl all URLs",
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

    crawl()
