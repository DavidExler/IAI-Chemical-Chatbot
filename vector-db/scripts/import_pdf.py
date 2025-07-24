import argparse
import logging
import os
import re

import pymilvus
import torch.multiprocessing as mp
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_milvus import Milvus
from langchain_unstructured import UnstructuredLoader
from more_itertools import chunked
from tqdm import tqdm
from unstructured_client.models.shared import Strategy

MIN_WORD_COUNT = 10

try:
    import dotenv

    dotenv.load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "chemical_database")
EMBEDDINGS_MODEL = "intfloat/multilingual-e5-large"
host = os.environ.get("MILVUS_HOST", "127.0.0.1")
port = os.environ.get("MILVUS_PORT", "19530")
user = os.environ.get("MILVUS_ROOT_USER", "root")
password = os.environ.get("MILVUS_ROOT_PASSWORD", "Milvus")
UNSTRUCTURED_URL = os.environ.get("UNSTRUCTURED_URL", "http://unstructured:8000/")


def filter_document(d: Document):
    if d.metadata.get("category") != "NarrativeText":
        return False
    if len(d.page_content.split(" ")) <= MIN_WORD_COUNT:
        return False
    num_digits = sum(c.isdigit() for c in d.page_content)
    if len(d.page_content) < 50:
        return False
    if num_digits / len(d.page_content) > 0.1:
        return False
    num_semicolons = sum(c == ";" for c in d.page_content)
    if num_semicolons > 3:
        return False
    if re.match(r"^\[[0-9]+]", d.page_content):
        return False
    if "doi.org" in d.page_content:
        return False
    if d.page_content.startswith("Figure"):
        return False
    return True


def import_pdfs(file: str | list[str]):
    logger.info(f"Importing {file}...")
    loader = UnstructuredLoader(
        file,
        url=UNSTRUCTURED_URL,
        strategy=Strategy.AUTO,
    )
    documents = [d for d in loader.lazy_load() if filter_document(d)]
    for doc in documents:
        try:
            del doc.metadata["languages"]
            del doc.metadata["parent_id"]
        except KeyError:
            pass
    return documents


def main(files: list[str]):
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDINGS_MODEL,
        model_kwargs={"device": "cuda:0"},
        # multi_process=True,
    )

    chunk_size = 128
    for chunk in tqdm(
        chunked(files, chunk_size),
        total=len(files[1:]) // chunk_size,
        unit_scale=chunk_size,
    ):
        with mp.Pool(64) as pool:
            documents = [d for ds in pool.map(import_pdfs, chunk) for d in ds]
        milvus = Milvus.from_documents(
            documents,
            collection_name=COLLECTION_NAME,
            embedding=embeddings,
            connection_args={
                "uri": "http://milvus:19530",
                "token": f"{user}:{password}",
                #"uri": f"http://{host}:{port}",
                #"host": host,
                #"port": port,
                #"token": f"{user}:{password}",
            },
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--collection",
        help="Collection name",
        type=str,
        default=COLLECTION_NAME,
    )
    parser.add_argument(
        "-f",
        "--force",
        help="Force overwrite collection",
        action="store_true",
    )
    parser.add_argument(
        "folder",
        help="Folder of PDFs to import",
        type=str,
    )
    args = parser.parse_args()

    vector_db = pymilvus.Milvus(host, port, token=f"{user}:{password}")

    sources = set()
    if vector_db.has_collection(args.collection.strip()):
        if args.force:
            logger.warning("Collection already exists. Dropping it...")
            vector_db.drop_collection(args.collection.strip())
        else:
            sources = {
                os.path.basename(s["source"])
                for s in vector_db.query(
                    args.collection.strip(),
                    expr="page_number > 0",
                    output_fields=["source"],
                )
            }
    vector_db.close()

    files = {file for file in os.listdir(args.folder)}
    files = list(files - sources)
    files = [os.path.join(args.folder, file) for file in files]

    print(f"Found {len(files)} files to import")
    main(files)
