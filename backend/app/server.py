import json
import logging
import os
from sqlite3 import OperationalError
from typing import Any, Literal
from uuid import UUID

import uvicorn
from app.chains.agent import AgentChain
from app.chains.code import CodeChain
from app.chains.conversation_name import ConversationNameCallback, ConversationNameChain
from app.chains.evaluation import EvaluationChain, parse_output
from app.chains.rag import RAGChain
from app.helpers.auth import FastAPIKeycloak, KeycloakUser
from app.history.conversations import (
    ConversationSettings,
    create_conversation,
    delete_conversation,
    get_conversation,
    get_conversation_history,
    get_conversations,
    get_message,
    set_conversation_name,
    set_conversation_settings,
)
from app.history.documents import add_documents, delete_document_by_uuid, get_documents
from app.models.chain import APIChain, APIConversation, APIDocument
from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langfuse.api import Observation
from langfuse.callback import CallbackHandler
from langserve import add_routes
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from starlette.middleware.cors import CORSMiddleware

from langfuse import Langfuse

try:
    import dotenv

    dotenv.load_dotenv()
except ImportError:
    pass

VIRTUAL_PATH = os.environ.get("VIRTUAL_PATH", "")

LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()
logging.basicConfig(level=LOGLEVEL)
LOGGER = logging.getLogger(__name__)

app = FastAPI(root_path=VIRTUAL_PATH)
if os.environ.get("IS_DEVELOPMENT", "false") == "true":
    app.debug = True
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

keycloak = FastAPIKeycloak()

ALL_CHAINS = [RAGChain(), AgentChain(), CodeChain()]


@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse(f"{VIRTUAL_PATH}/docs")


@app.get("/current_user")
async def current_user(user: KeycloakUser = Depends(keycloak.get_current_user())):
    return user.user_id


@app.post("/conversations")
async def create_chat_conversation(
    user: KeycloakUser = Depends(keycloak.get_current_user()),
) -> APIConversation:
    return create_conversation(user.user_id)


@app.get("/conversations")
async def get_chat_conversations(
    user: KeycloakUser = Depends(keycloak.get_current_user()),
) -> list[APIConversation]:
    try:
        return [c.to_api() for c in get_conversations(user.user_id)]
    except OperationalError:
        return [create_conversation(user.user_id)]


@app.get("/conversations/{conversation_id}")
async def get_chat_conversation(
    conversation_id: str,
    user: KeycloakUser = Depends(keycloak.get_current_user()),
) -> APIConversation:
    check_conversation_id(conversation_id, user.user_id)
    try:
        return get_conversation(conversation_id).to_api()
    except OperationalError:
        raise HTTPException(status_code=404, detail="Conversation not found")


@app.get("/conversations/{conversation_id}/messages")
async def get_chat_conversation_messages(
    conversation_id: str, user: KeycloakUser = Depends(keycloak.get_current_user())
) -> list[dict]:
    check_conversation_id(conversation_id, user.user_id)
    chat_history = get_conversation_history(conversation_id)
    messages = await chat_history.aget_messages()
    return [dict(m) for m in messages]


@app.put("/conversations/{conversation_id}/settings")
async def update_conversation_settings(
    conversation_id: str,
    settings: ConversationSettings,
    user: KeycloakUser = Depends(keycloak.get_current_user()),
) -> APIConversation:
    check_conversation_id(conversation_id, user.user_id)

    try:
        set_conversation_settings(conversation_id, settings)
        LOGGER.debug(f"Saved settings {settings} for {conversation_id}")
        return await get_chat_conversation(conversation_id, user)
    except Exception as e:
        LOGGER.error(f"Failed to save settings {settings} for {conversation_id}, {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/conversations/{conversation_id}")
async def delete_chat_conversation(
    conversation_id: str, user: KeycloakUser = Depends(keycloak.get_current_user())
):
    check_conversation_id(conversation_id, user.user_id)
    delete_conversation(user.user_id, conversation_id)


@app.get("/conversations/{conversation_id}/documents")
async def get_conversation_documents(
    conversation_id: str,
    user: KeycloakUser = Depends(keycloak.get_current_user()),
) -> list[APIDocument]:
    check_conversation_id(conversation_id, user.user_id)
    return get_documents(conversation_id)


@app.delete("/conversations/{conversation_id}/documents/{document_id}")
async def delete_conversation_document(
    conversation_id: str,
    document_id: str,
    user: KeycloakUser = Depends(keycloak.get_current_user()),
):
    check_conversation_id(conversation_id, user.user_id)
    if UUID(document_id) not in {d.uuid for d in get_documents(conversation_id)}:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )
    delete_document_by_uuid(document_id)


@app.post("/conversations/{conversation_id}/documents")
async def add_conversation_documents(
    conversation_id: str,
    files: list[UploadFile],
    user: KeycloakUser = Depends(keycloak.get_current_user()),
) -> list[str]:
    check_conversation_id(conversation_id, user.user_id)
    try:
        return await add_documents(conversation_id, files)
    except IntegrityError as e:
        LOGGER.error(f"Document already exists: {e}")
        raise HTTPException(status_code=409, detail="Document already exists")
    except Exception as e:
        LOGGER.error(f"Failed to add documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/conversations/{conversation_id}/generate_conversation_name")
async def generate_conversation_name(
    conversation_id: str,
    user: KeycloakUser = Depends(keycloak.get_current_user()),
):
    check_conversation_id(conversation_id, user.user_id)
    return await _generate_conversation_name(conversation_id)


async def _generate_conversation_name(conversation_id: str):
    LOGGER.debug(f"Generating conversation name for conversation {conversation_id}")
    messages: list[BaseMessage] = await get_conversation_history(
        conversation_id
    ).aget_messages()
    pretty_messages = "\n\n".join(
        f"Name: {m.name}\nContent: {m.content}" for m in messages
    )
    chain = ConversationNameChain().get_chain()
    conversation_name = (
        chain.invoke(pretty_messages, config={"callbacks": [langfuse_handler]})
        .replace('"', "")
        .replace("'", "")[:40]
    )
    LOGGER.debug(f"Generated conversation name: {conversation_name}")
    set_conversation_name(conversation_id, conversation_name)
    LOGGER.debug(f"Set conversation name for conversation {conversation_id}")
    return conversation_name


class EvaluationRequest(BaseModel):
    input: str
    ai_message: str
    human_message: str
    rubric: Literal[
        "helpfulness", "harmlessness", "honesty", "factual_validity", "reasoning"
    ] = "helpfulness"


class Feedback(BaseModel):
    type: Literal["up", "down"]
    expected_answer: str | None = None
    feedback: str | None = None


@app.post("/feedback/{msg_id}")
async def save_feedback(
    msg_id: str,
    feedback: Feedback,
    user: KeycloakUser = Depends(keycloak.get_current_user()),
):
    LOGGER.debug(f"Saving feedback for message {msg_id}")

    db_message = get_message(msg_id)
    if db_message is None:
        raise HTTPException(status_code=404, detail="Message not found")

    message_data = db_message.message.get("data")
    if message_data is None:
        raise HTTPException(status_code=404, detail="Message data not found")

    run_id = message_data.get("id")
    if run_id is None:
        raise HTTPException(status_code=404, detail="Run ID not found")
    run_id = run_id.replace("run-", "")

    client = Langfuse()
    observations = client.fetch_observations(type="SPAN", user_id=user.user_id).data
    trace_id = next(
        (
            o.trace_id
            for o in observations
            if isinstance(o, Observation)
            and isinstance(o.output, dict)
            and o.output.get("id") in (run_id, f"run-{run_id}")
        ),
        None,
    )
    if trace_id is None:
        raise HTTPException(status_code=404, detail="Trace ID not found")

    client.score(
        name=user.name,
        trace_id=trace_id,
        data_type="NUMERIC",
        value=1 if feedback.type == "up" else 0,
        comment=json.dumps(feedback.model_dump()),
    )


class EvaluationResponse(BaseModel):
    feedback: str | None
    score: int | None


@app.post("/evaluate_answer")
async def evaluate_answer(
    request: EvaluationRequest,
    _: KeycloakUser = Depends(keycloak.get_current_user()),
) -> EvaluationResponse:
    LOGGER.debug(f"Evaluate answer")
    evaluation = (
        EvaluationChain()
        .get_chain()
        .invoke(
            {
                "input": request.input,
                "ai_message": request.ai_message,
                "human_message": request.human_message,
            },
            config={"callbacks": [langfuse_handler]},
        )
    )
    LOGGER.info(f"Evaluated answer: {evaluation}")
    feedback, score = parse_output(evaluation)
    LOGGER.debug(
        f"Evaluated answer:\nAI: {request.ai_message}\nHuman: {request.human_message}\nFeedback: {feedback}\nScore: {score}"
    )
    return EvaluationResponse(feedback=feedback, score=int(score))


def check_conversation_id(conversation_id: str, user_id: str):
    conversations = {str(c.uuid) for c in get_conversations(user_id)}
    if conversation_id not in conversations:
        raise HTTPException(
            status_code=401,
            detail="User not authenticated",
        )


async def _per_request_config_modifier(
    config: dict[str, Any], request: Request
) -> dict[str, Any]:
    params = request.url.path.split("/")
    chain_path = params[params.index("chains") + 1]
    required_roles = next(
        (
            c.required_auth_roles
            for c in ALL_CHAINS
            if c.path.lower() == chain_path.lower()
        ),
        None,
    )
    user = await keycloak.current_user_by_request(request=request)

    if user is None or not all(role in user.roles for role in required_roles):
        raise HTTPException(
            status_code=401,
            detail="User not authenticated",
        )

    config = config.copy()
    LOGGER.debug(f"raw config: {config}")
    configurable = config.get("configurable", {})
    configurable["user_id"] = user.user_id
    configurable["user_roles"] = user.roles
    configurable["document_ids"] = configurable.get("document_ids", [])
    configurable["confluence_private"] = (
        "private" if "confluence-private" in user.roles else "public"
    )
    configurable["user"] = user
    config["configurable"] = configurable

    langfuse_handler = CallbackHandler(
        user_id=user.user_id,
        session_id=configurable["session_id"] if "session_id" in configurable else None,
    )

    if "callbacks" not in config:
        config["callbacks"] = []
    config["callbacks"].extend([langfuse_handler])

    LOGGER.info(f"parsed config: {config}")
    return config


@app.get("/chains")
async def get_chains(
    user: KeycloakUser = Depends(keycloak.get_current_user()),
) -> list[APIChain]:
    return [
        c.to_api()
        for c in ALL_CHAINS
        if all(role in user.roles for role in c.required_auth_roles)
    ]


langfuse_handler = CallbackHandler()
conversation_name_callback = ConversationNameCallback()
config = RunnableConfig(callbacks=[conversation_name_callback])

for chain in ALL_CHAINS:
    add_routes(
        app,
        chain.get_chain().with_config(config),
        path=f"/chains/{chain.path}",
        per_req_config_modifier=_per_request_config_modifier,
        enable_feedback_endpoint=True,
        output_type=dict,
    )


@app.get(
    "/health",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
)
def get_health():
    return {"status": "ok"}


class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("/health") == -1


logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, root_path=VIRTUAL_PATH, loop="asyncio")
