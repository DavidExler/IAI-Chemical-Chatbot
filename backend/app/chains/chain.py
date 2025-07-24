from abc import ABC, abstractmethod

from app.models.chain import APIChain
from langchain_core.language_models import BaseLLM
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool


class Chain(ABC):
    @property
    @abstractmethod
    def model_id(self) -> str: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    def description(self) -> str:
        return ""

    @property
    @abstractmethod
    def path(self) -> str: ...

    @property
    @abstractmethod
    def tool_names(self) -> list[str]: ...

    @property
    def prompt_names(self) -> list[str]:
        return ["Default"]

    @property
    def required_auth_roles(self) -> list[str]:
        return []

    @property
    def supports_documents(self) -> bool:
        return False

    @abstractmethod
    def available_tools(self, llm: BaseLLM) -> list[BaseTool]: ...

    @abstractmethod
    def get_chain(self) -> Runnable: ...

    def to_api(self) -> APIChain:
        return APIChain(
            name=self.name,
            description=self.description,
            path=self.path,
            supports_documents=self.supports_documents,
            tool_names=self.tool_names,
            prompt_names=self.prompt_names,
        )
