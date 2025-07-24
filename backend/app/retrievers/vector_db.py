import logging
import os

from app.helpers.huggingface_endpoints import HuggingFaceEndpointEmbeddings
from langchain_core.retrievers import BaseRetriever
from langchain_milvus import Milvus

LOGGER = logging.getLogger(__name__)

HOST = os.environ.get("MILVUS_HOST", "127.0.0.1")
PORT = os.environ.get("MILVUS_PORT", "19530")
USER = os.environ.get("MILVUS_ROOT_USER", "root")
PASSWORD = os.environ.get("MILVUS_ROOT_PASSWORD", "Milvus")

ENDPOINT_URL = os.environ.get("TEI_INTERFACE_URL", "http://embeddings-model/")
EMBEDDINGS_MODEL = "intfloat/multilingual-e5-large"
embeddings = HuggingFaceEndpointEmbeddings(model=ENDPOINT_URL)


def get_vector_db_retriever(
    collection_name: str = "confluence_documents",
    k: int = 2,
) -> BaseRetriever:
    vector_db = Milvus(
        embeddings,
        connection_args={
            "uri": "http://milvus:19530",
            "token": f"{USER}:{PASSWORD}",
            #"host": HOST,
            #"port": PORT,
            #"token": f"{USER}:{PASSWORD}",
        },
        collection_name=collection_name,
    )
    return vector_db.as_retriever(search_kwargs={"k": k})

if __name__ == "__main__":
    print("Testing vector DB retriever...")
    retriever = get_vector_db_retriever()
    query = "Luca Rettenberger head circumference"
    print(f"Running test query: {query}")
    results = retriever.get_relevant_documents(query)
    
    print(f"Got {len(results)} results")
    for i, doc in enumerate(results):
        print(f"--- Result {i+1} ---\n{doc.page_content[:1500]}")
