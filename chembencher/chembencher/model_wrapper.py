from collections.abc import Generator, Iterable
from dataclasses import dataclass

from chembench.prompter import PrompterBuilder
from chembench.report import Report
from chembench.task import Task
from langchain_core.runnables import Runnable


@dataclass
class Generation:
    text: str


@dataclass
class Generations:
    generations: list[list[Generation]]

    def __getitem__(self, index):
        return self.generations[index]


@dataclass
class ModelWrapper:
    chain: Runnable

    def generate(self, prompts: list[str]) -> (Generations, dict):
        generations = []
        result = {}
        for prompt in prompts:
            result = self.chain.invoke({"input": prompt})
            generations.append([Generation(text=result.content)])
        return Generations(generations), result.response_metadata.get("logprobs")

    def run_task(self, task: Task) -> Report:
        prompter = PrompterBuilder.from_model_object(
            model=self, get_logprobs=True, prompt_type="instruction"
        )
        return prompter.report(task)

    def run_tasks(self, tasks: Iterable[Task]) -> Generator[Report, None, None]:
        for task in tasks:
            yield self.run_task(task)
