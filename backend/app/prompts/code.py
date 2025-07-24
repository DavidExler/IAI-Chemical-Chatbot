import logging

from langchain_core.prompts import BasePromptTemplate, ChatPromptTemplate

SYSTEM_MESSAGE = """
Assistant is a Llama 3 70B Model trained by Meta based on the Llama architecture.

Knowledge cutoff: December, 2023

Assistant is designed to be able to assist with all sorts of coding tasks, from debugging to code generation.

Assistant is also able to provide explanations for code snippets, and can help with understanding error messages.

Assistant explains the code snippets in detail, and always provides some test cases for the code he generated.
"""

HUMAN_MESSAGE = """
USER'S INPUT
--------------------
Remember to respond in a plain string, you can use markdown to format your code output.
Here is the user's input:

{input}
"""


LOGGER = logging.getLogger(__name__)


def get_prompt() -> BasePromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_MESSAGE),
            ("placeholder", "{chat_history}"),
            ("human", HUMAN_MESSAGE),
        ]
    )
