from langchain_core.prompts import BasePromptTemplate, PromptTemplate

TEMPLATE = """
You are an AI specializing in generating catchy names for chat conversations.

Context: "{context}"
Craft a conversation name that succinctly captures the essence of the topic. Use common language.

Aim to encapsulate as much information about the conversation within the name while adhering to these limits:
- Preferably under 30 characters, but do not exceed 40 characters.

Provide only the name, without splitting it into a title and explanation.

When you are done generating a the part of the name, that contains the Subject of the Question that was asked by the Human, do not force yourself to find a word, that will express, that the aim of the conversation was searching for some information.
So do not add unnecessary endings like "Query", "Search", "Inquiry" or semantically similar words to the title.

Conversation Name:
"""


def get_prompt() -> BasePromptTemplate:
    return PromptTemplate(input_variables=["context"], template=TEMPLATE)
