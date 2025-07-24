import uuid
from collections.abc import Sequence

from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.runnables import RunnableWithMessageHistory


class AgentRunnableWithMessageHistory(RunnableWithMessageHistory):
    def _get_output_messages(
        self, output_val: str | BaseMessage | Sequence[BaseMessage] | dict
    ) -> list[BaseMessage]:
        if (
            isinstance(output_val, dict)
            and "output" in output_val
            and "intermediate_steps" in output_val
        ):
            intermediate_steps = [
                {"action": action, "observation": observation}
                for action, observation in output_val["intermediate_steps"]
            ]
            return [
                AIMessage(
                    id=str(output_val.get("id", uuid.uuid4())),
                    content=output_val["output"],
                    additional_kwargs={"intermediate_steps": intermediate_steps},
                )
            ]
        return super()._get_output_messages(output_val)
