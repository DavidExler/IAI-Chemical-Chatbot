from typing import Any

from langchain.agents import AgentExecutor
from langchain_core.agents import AgentFinish
from langchain_core.callbacks import (
    AsyncCallbackManagerForChainRun,
    CallbackManagerForChainRun,
)
from langchain_core.runnables import ConfigurableFieldSpec


class ConfigurableAgentExecutor(AgentExecutor):
    def _return(
        self,
        output: AgentFinish,
        intermediate_steps: list,
        run_manager: CallbackManagerForChainRun | None = None,
    ) -> dict[str, Any]:
        out = super()._return(output, intermediate_steps, run_manager)
        out["id"] = out.get("id", run_manager.parent_run_id or run_manager.run_id)
        return out

    async def _areturn(
        self,
        output: AgentFinish,
        intermediate_steps: list,
        run_manager: AsyncCallbackManagerForChainRun | None = None,
    ) -> dict[str, Any]:
        out = await super()._areturn(output, intermediate_steps, run_manager)
        out["id"] = out.get("id", run_manager.parent_run_id or run_manager.run_id)
        return out

    @property
    def config_specs(self) -> list[ConfigurableFieldSpec]:
        return self.agent.runnable.config_specs + [
            c for t in self.tools for c in t.config_specs if "config_specs" in dir(t)
        ]
