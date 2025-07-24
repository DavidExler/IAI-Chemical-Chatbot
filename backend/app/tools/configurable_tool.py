from typing import Any

from langchain_core.callbacks import Callbacks
from langchain_core.prompts import BasePromptTemplate, format_document
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import Runnable
from langchain_core.runnables.utils import ConfigurableFieldSpec
from langchain_core.tools import BaseTool


def _get_relevant_documents(
    query: str,
    retriever: BaseRetriever,
    document_prompt: BasePromptTemplate,
    document_separator: str,
    callbacks: Callbacks = None,
) -> str:
    docs = retriever.get_relevant_documents(query, callbacks=callbacks)
    return document_separator.join(
        format_document(doc, document_prompt) for doc in docs
    )


class ConfigurableRetrieverTool(BaseTool):
    retriever: Runnable
    document_prompt: BasePromptTemplate

    @property
    def config_specs(self) -> list[ConfigurableFieldSpec]:
        return self.retriever.config_specs if "retriever" in dir(self.retriever) else []

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        return _get_relevant_documents(
            *args,
            retriever=self.retriever,
            document_prompt=self.document_prompt,
            document_separator="\n\n",
            **kwargs,
        )
