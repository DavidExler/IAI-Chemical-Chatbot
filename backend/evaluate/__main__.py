import argparse
import glob
import logging
import os
from datetime import datetime
from functools import lru_cache
from uuid import UUID

import dotenv
import requests
from evaluate.models import (
    BearerAuth,
    Chat,
    ChatEvaluation,
    ChatEvaluations,
    ChatMessage,
    MessageEvaluation,
)
from langchain_core.messages import AIMessageChunk
from langchain_core.runnables import RunnableConfig
from langserve import RemoteRunnable
from pydantic_yaml import parse_yaml_file_as, to_yaml_file
from requests import Session
from tabulate import tabulate

dotenv.load_dotenv()

MIN_SCORE = 1
MAX_SCORE = 5
CHATS_DIR = "evaluation/chats/"
DOCUMENTS_BASE_PATH = "evaluation/documents/"
BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:8080/chatbot")
EVALUATION_USER = os.environ.get("EVALUATION_USER", "evaluation")
EVALUATION_PASSWORD = os.environ.get("EVALUATION_PASSWORD", "evaluation")
KEYCLOAK_REALM_URI = os.environ["KEYCLOAK_REALM_URI"]
DELETE_CONVERSATIONS = (
    str(os.environ.get("DELETE_CONVERSATIONS", "true")).lower() == "true"
)
BACKEND_CLIENT = Session()

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


@lru_cache
def get_access_token() -> str:
    LOGGER.info("Getting access token")
    return requests.post(
        f"{KEYCLOAK_REALM_URI}/protocol/openid-connect/token",
        data={
            "client_id": "oauth",
            "username": EVALUATION_USER,
            "password": EVALUATION_PASSWORD,
            "grant_type": "password",
        },
    ).json()["access_token"]


def load_chats(chat_files: list[str]) -> list[Chat]:
    LOGGER.info("Loading chats")
    return [
        parse_yaml_file_as(Chat, f)
        for f in glob.iglob(f"{CHATS_DIR}**/*", recursive=True)
        if (f.endswith(".yaml") or f.endswith(".yml"))
        and (not chat_files or any(cf in f for cf in chat_files))
    ]


def evaluate_message(
    conversation_id: UUID, message: ChatMessage, documents: dict[str, str]
) -> MessageEvaluation:
    LOGGER.info(f"Evaluating message {message}")
    document_ids = [
        documents.get(d) for d in message.document_filenames or [] if d in documents
    ]
    config: RunnableConfig = {
        "configurable": {
            "conversation_id": conversation_id,
            "document_ids": ",".join(document_ids),
            "tool_names": message.tool_names,
            "prompt": message.prompt,
        }
    }
    LOGGER.info(f"Config: {config}")

    try:
        chain = RemoteRunnable(
            f"{BACKEND_URL}/chains/{message.chain}",
            headers={"Authorization": f"Bearer {get_access_token()}"},
        )
        start = datetime.now()
        response = "".join(
            (
                c.content
                if isinstance(c, AIMessageChunk)
                else c if isinstance(c, str) else c.get("output", "")
            )
            for c in chain.stream({"input": message.content}, config)
        )
        end = datetime.now()
        if response == "Agent stopped due to iteration limit or time limit.":
            raise Exception(response)
        LOGGER.info(f"Got response: {response}")
        if message.expected_answer:
            evaluation = BACKEND_CLIENT.post(
                f"{BACKEND_URL}/evaluate_answer",
                json={
                    "rubric": "helpfulness",  # One of "helpfulness", "harmlessness", "honesty", "factual_validity", "reasoning"
                    "input": message.content,
                    "ai_message": response,
                    "human_message": message.expected_answer,
                },
            ).json()
            LOGGER.info(f"Got evaluation: {evaluation}")
            feedback, score = evaluation["feedback"], evaluation["score"]
            score = int(score)
            if message.expect_wrong:
                score = MAX_SCORE - score + MIN_SCORE
        else:
            score = None
            feedback = None
        evaluation = MessageEvaluation(
            message=message,
            response=response,
            feedback=feedback,
            score=score,
            duration=end - start,
        )
    except Exception as error:
        LOGGER.error(f"Error: {error}")
        evaluation = MessageEvaluation(
            message=message, response="", feedback=None, score=None, error=str(error)
        )
    return evaluation


def evaluate_chat(chat: Chat) -> ChatEvaluation:
    LOGGER.info(f"Evaluating chat {chat}")
    conversation_id = BACKEND_CLIENT.post(f"{BACKEND_URL}/conversations").json()["uuid"]

    document_filenames = list({d for m in chat.messages for d in m.document_filenames})
    if document_filenames:
        files = [
            (
                "files",
                (
                    d.split("/")[-1],
                    open(os.path.join(DOCUMENTS_BASE_PATH, d), "rb"),
                    "application/pdf",
                ),
            )
            for d in document_filenames
        ]
        LOGGER.info(f"Uploading documents: {files}")
        document_ids = BACKEND_CLIENT.post(
            f"{BACKEND_URL}/conversations/{conversation_id}/documents",
            files=files,
        ).json()
        document_ids = {d: i for d, i in zip(document_filenames, document_ids)}

        LOGGER.info(f"Uploaded documents: {document_ids}")
    else:
        document_ids = dict()
    evaluation = ChatEvaluation(
        chat_name=chat.name,
        message_evaluations=[
            evaluate_message(conversation_id, msg, document_ids)
            for msg in chat.messages
        ],
    )
    if DELETE_CONVERSATIONS:
        BACKEND_CLIENT.delete(
            f"{BACKEND_URL}/conversations/{conversation_id}"
        ).raise_for_status()
    return evaluation


def generate_table(chat: ChatEvaluation) -> str:
    return tabulate(
        [
            [
                msg.message.content or "",
                msg.response or "",
                msg.message.expected_answer or "",
                "expected to be wrong" if msg.message.expect_wrong else "",
                msg.feedback or "",
                float(msg.score) if msg.score is not None else "",
                msg.error or "",
                f"{msg.duration.seconds}s" if msg.duration else "",
            ]
            for msg in chat.message_evaluations
        ],
        headers=[
            "Message",
            "Response",
            "Expected Response",
            "Expect Wrong",
            "Feedback",
            "Score",
            "Error",
            "Duration",
        ],
        tablefmt="rounded_grid",
        floatfmt=".2f",
        maxcolwidths=[40, 40, 40, 20, 40, 5, 20, 5],
    )


def generate_report(chat_evaluations: ChatEvaluations) -> str:
    return ("\n\n" + "-" * 145 + "\n\n").join(
        "\n".join(
            (
                f"{chat.chat_name}:",
                generate_table(chat),
            )
        )
        for chat in chat_evaluations.chat_evaluations
    )


def evaluate(chat_files: list[str]):
    LOGGER.info("Evaluating")
    chats = load_chats(chat_files)
    chat_evaluations = [evaluate_chat(c) for c in chats]
    created_at = datetime.now()
    chat_evaluations = ChatEvaluations(
        created_at=created_at, chat_evaluations=chat_evaluations
    )

    report = generate_report(chat_evaluations)
    summary = tabulate(
        [
            [
                chat.chat_name,
                sum(c.score for c in chat.message_evaluations if c.score)
                / max(1, len([c for c in chat.message_evaluations if c.score])),
                ", ".join(m.error for m in chat.message_evaluations if m.error),
            ]
            for chat in chat_evaluations.chat_evaluations
        ],
        headers=["Chat", "Average Score", "Errors"],
        tablefmt="rounded_grid",
        floatfmt=".2f",
    )

    print(report)
    print(summary)

    formatted_date_time = created_at.strftime("%Y-%m-%d_%H:%M:%S")
    with open(f"evaluation/reports/report_{formatted_date_time}.txt", "w") as f:
        f.write(report + "\n\n" + summary)
    to_yaml_file(
        f"evaluation/reports/report_{formatted_date_time}.yaml", chat_evaluations
    )


if __name__ == "__main__":
    BACKEND_CLIENT.auth = BearerAuth(get_access_token())
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--chat-files",
        "-f",
        nargs="+",
        help="Path to chat file",
    )
    args = parser.parse_args()
    evaluate(args.chat_files)
