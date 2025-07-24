import json
import logging
import os
from uuid import UUID

import sqlalchemy
from app.history.db_models import Document
from app.models.chain import APIDocument
from fastapi import UploadFile
from langchain_unstructured import UnstructuredLoader
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

LOGGER = logging.getLogger(__name__)

CHAT_HISTORY_DB_CONNECTION = os.environ.get("CHAT_HISTORY_DB", "sqlite:///sqlite.db")
UNSTRUCTURED_URL = os.environ.get("UNSTRUCTURED_URL", "http://unstructured:8000/")


def get_documents(conversation_id: str) -> list[APIDocument]:
    LOGGER.debug(f"Getting documents for conversation {conversation_id}")
    engine = create_engine(CHAT_HISTORY_DB_CONNECTION, echo=False)
    with Session(engine) as session:
        documents = (
            session.query(Document).filter_by(conversation_uuid=conversation_id).all()
        )
        return [d.to_api() for d in documents]


async def add_documents(conversation_id: str, files: list[UploadFile]) -> list[str]:
    LOGGER.debug(f"Adding {len(files)} documents to conversation {conversation_id}")

    return [await add_document(conversation_id, f) for f in files]


async def load_document(
    conversation_id: str, document_uuid: UUID, file: UploadFile, file_path: str
):
    LOGGER.debug(f"Loading document {document_uuid} to vector database")
    metadata = {
        "namespace": str(document_uuid),
        "source": file.filename,
        "type": file.content_type,
    }

    loader = UnstructuredLoader(
        file_path,
        url=UNSTRUCTURED_URL,
        partition_via_api=True,
        split_pdf_concurrency_level=15,
    )
    documents = await loader.aload()
    document = None
    for doc in documents:
        if document is None:
            document = doc
            continue
        document.page_content += f"\n{doc.page_content}"
        document.metadata = {**document.metadata, **doc.metadata, **metadata}

    out_path = os.path.join("documents", conversation_id, f"{document_uuid}.json")
    with open(out_path, "w") as f:
        json.dump([document.to_json()], f)
    LOGGER.info(f"Saved {len(documents)} documents from {file.filename} to {out_path}")


async def add_document(conversation_id: str, file: UploadFile) -> str:
    LOGGER.debug(f"Adding document {file.filename} to conversation {conversation_id}")
    folder_path = f"documents/{conversation_id}"
    file_path = f"{folder_path}/{file.filename}"
    os.makedirs(folder_path, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    LOGGER.debug(f"Saved document {file.filename} to {file_path}")

    engine = create_engine(CHAT_HISTORY_DB_CONNECTION, echo=False)
    with Session(engine) as session:
        document = Document(
            conversation_uuid=conversation_id,
            title=file.filename,
            type=file.content_type,
            filepath=file.filename,
        )
        try:
            session.add(document)
            session.flush()
            await load_document(conversation_id, document.uuid, file, file_path)
            session.commit()
            LOGGER.debug(
                f"Added document {file.filename} to conversation {conversation_id}"
            )
            return str(document.uuid)
        except sqlalchemy.exc.IntegrityError as e:
            LOGGER.warning(
                f"Failed to add document {file.filename} to conversation {conversation_id}, {e}"
            )
            session.rollback()
            raise e
        except Exception as e:
            LOGGER.warning(
                f"Failed to add document {file.filename} to conversation {conversation_id}, {e}"
            )
            delete_document_by_uuid(document.uuid)
            session.rollback()
            raise e


def delete_document(document: Document):
    LOGGER.debug(f"Deleting document {document.uuid}")
    try:
        os.remove(f"documents/{document.conversation_uuid}/{document.filepath}")
        os.remove(f"documents/{document.conversation_uuid}/{document.uuid}.json")
    except FileNotFoundError:
        pass

    engine = create_engine(CHAT_HISTORY_DB_CONNECTION, echo=False)
    with Session(engine) as session:
        document = session.merge(document)
        session.delete(document)
        session.commit()


def delete_document_by_uuid(document_uuid: str):
    LOGGER.debug(f"Deleting document {document_uuid}")
    engine = create_engine(CHAT_HISTORY_DB_CONNECTION, echo=False)
    with Session(engine) as session:
        document = session.query(Document).filter_by(uuid=document_uuid).first()
        if not document:
            return
        try:
            os.remove(f"documents/{document.conversation_uuid}/{document.filepath}")
            os.remove(f"documents/{document.conversation_uuid}/{document_uuid}.json")
        except FileNotFoundError:
            pass
        session.delete(document)
        session.commit()
