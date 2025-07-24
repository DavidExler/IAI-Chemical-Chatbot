from dataclasses import dataclass
from typing import Any, cast

from langchain_core.runnables import ConfigurableFieldSpec, Runnable, RunnableConfig
from langchain_core.runnables.utils import Input


@dataclass
class ParseTools(Runnable):
    tool_descriptions: dict[str, str]

    @property
    def config_specs(self) -> list[ConfigurableFieldSpec]:
        return [
            ConfigurableFieldSpec(
                id="tool_names",
                annotation=list,
                name="Tool Names",
                description="The names of the tools to parse.",
                is_shared=True,
            )
        ]

    def invoke(self, input: Input, config: RunnableConfig | None = None) -> str:
        configurable = cast(dict[str, Any], config.pop("configurable", {}))
        return "\n".join(
            self.tool_descriptions[t] for t in configurable.get("tool_names", [])
        )


class ParseToolNames(Runnable):
    @property
    def config_specs(self) -> list[ConfigurableFieldSpec]:
        return [
            ConfigurableFieldSpec(
                id="tool_names",
                annotation=list,
                name="Tool Names",
                description="The names of the tools to parse.",
                is_shared=True,
            )
        ]

    def invoke(self, input: Input, config: RunnableConfig | None = None) -> str:
        configurable = cast(dict[str, Any], config.pop("configurable", {}))
        return ",".join(configurable.get("tool_names", []))
