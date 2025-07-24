import json
import logging
import uuid

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import ConfigurableFieldSpec

LOGGER = logging.getLogger(__name__)


def is_valid_uuid(val: str) -> bool:
    try:
        return val == str(uuid.UUID(str(val)))
    except ValueError:
        return False


class DocumentRetriever(BaseRetriever):
    @property
    def config_specs(self) -> list[ConfigurableFieldSpec]:
        return [
            ConfigurableFieldSpec(
                id="document_ids",
                annotation=str,
                name="Document IDs",
                description="The IDs of the documents to retrieve",
                is_shared=True,
            ),
            ConfigurableFieldSpec(
                id="conversation_id",
                annotation=str,
                name="Conversation ID",
                description="Unique identifier for the conversation.",
                is_shared=True,
            ),
        ]

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        LOGGER.info(f"Retrieving documents")

        configurable = run_manager.metadata
        conversation_id = configurable.get("conversation_id")
        document_ids = configurable.get("document_ids", "").split(",")
        document_ids = [doc_id.strip() for doc_id in document_ids if doc_id.strip()]
        document_ids = [doc for doc in document_ids if is_valid_uuid(doc)]
        if not conversation_id or not document_ids or len(document_ids) == 0:
            LOGGER.warning("No document IDs provided")
            return []

        paths = [
            f"documents/{conversation_id}/{doc_id}.json" for doc_id in document_ids
        ]
        documents = []
        for path in paths:
            with open(path) as f:
                content = json.load(f)
            documents.extend(
                Document(
                    **{
                        k: str(v) if k == "id" else v
                        for k, v in {**c, **c["kwargs"]}.items()
                    }
                )
                for c in content
            )
        return documents
