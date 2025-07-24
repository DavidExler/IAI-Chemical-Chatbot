from dataclasses import dataclass

from langchain_core.documents import Document
from langchain_core.runnables import ConfigurableFieldSpec, Runnable, RunnableConfig
from langchain_core.runnables.utils import Input, Output


def format_docs(docs: list[Document]) -> str:
    return "\n\n".join(
        f"Title: {doc.metadata.get('title', doc.metadata.get('filename'))}\n"
        f"Source: {doc.metadata.get('source', doc.metadata.get('filename'))}\n"
        f"Content: {doc.page_content}"
        for doc in docs
    )


@dataclass
class RetrieveContext(Runnable):
    retriever: Runnable

    @property
    def config_specs(self) -> list[ConfigurableFieldSpec]:
        return self.retriever.config_specs

    def invoke(self, input: Input, config: RunnableConfig | None = None) -> Output:
        input = input["input"] if isinstance(input, dict) else input
        return format_docs(self.retriever.invoke(input, config))
