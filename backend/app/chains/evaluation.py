import logging
import os
import re

from app.chains.chain import Chain
from app.helpers.huggingface_endpoints import HuggingFaceEndpoint
from app.prompts.evaluation import get_prompt, get_prompt_rubrics_text
from langchain_core.language_models import BaseLLM
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool

LOGGER = logging.getLogger(__name__)

ENDPOINT_URL = os.environ.get("EVAL_INTERFACE_URL", "http://localhost:6666/")


def parse_output(output) -> (str | None, str | None):
    pattern = r"""
        (?:                        # Start of non-capturing group
            \[RESULT\]|\[SCORE\]|   # Match [RESULT] or [SCORE]
            Score:?|score:?|        # Match Score: or score:
            Result:?|\[Result\]:?|  # Match Result: or [Result]:
            score\s+of              # Match "score of"
        )                           # End of non-capturing group
        \s*                         # Allow any whitespace
        (?:\(|\[|\s)*               # Allow opening brackets or whitespace
        (\d+)                       # Capture the digit(s)
        (?:                         # Start of non-capturing group
            (?:\)|\]|\s|$)|         # Allow closing brackets, whitespace, or end of string
            (?:/\s*5|               # Allow /5 with optional whitespace
                \s*out\s*of\s*5)    # or "out of 5" with flexible whitespace
        )                           # End of non-capturing group
    """
    match = re.search(pattern, output, re.IGNORECASE | re.VERBOSE)

    if match:
        result = int(match.group(1))
        if 1 <= result <= 5:  # Ensure the result is within the valid range
            feedback = output[: match.start()].strip()
            return feedback, result

    return None, None


class EvaluationChain(Chain):
    @property
    def model_id(self) -> str:
        return "prometheus-eval/prometheus-7b-v2.0"

    @property
    def name(self) -> str:
        return "Evaluation (internal)"

    @property
    def path(self) -> str:
        return "evaluation"

    @property
    def tool_names(self) -> list[str]:
        return []

    def available_tools(self, _: BaseLLM) -> list[BaseTool]:
        return []

    def get_chain(self) -> Runnable:
        LOGGER.info(f"Creating Chain for {self.model_id}")
        llm = HuggingFaceEndpoint(
            endpoint_url=ENDPOINT_URL,
            inference_server_url=ENDPOINT_URL,
            max_new_tokens=1024,
            top_k=30,
            temperature=0.1,
            repetition_penalty=1.03,
            server_kwargs={
                "headers": {
                    "Content-Type": "application/json",
                }
            },
            stop_sequences=["<|eot_id|>"],
        )

        prompt = get_prompt()

        return (
            {
                "rubric": lambda x: get_prompt_rubrics_text(
                    x["rubric"] if "rubric" in x else "helpfulness"
                ),
                "response": lambda x: x["ai_message"],
                "reference_answer": lambda x: x["human_message"],
                "instruction": lambda x: x["input"],
            }
            | prompt
            | llm
        )


if __name__ == "__main__":
    result = (
        EvaluationChain()
        .get_chain()
        .invoke({"ai_answer": "You are Bob!", "human_answer": "You are Bob."})
    )
    print(result)
