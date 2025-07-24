# Backend

The Chatbot runs on top of LangChain, and gets served with a FastAPI Server and LangServe.

## Retreivers

This code includes some retreivers to serve the LLM with external information.
Adapt the retreivers and the databases, we however do not provide a database here.
Also see [vector-db](./../vector-db) for a Docker to host a vector database from embeddings corresponding to the deployed LLM with example document-imports.

## LLM

The LLM deployed in the [models](./../models) Docker needs to be referenced here, as the Endpoint will not be reached otherwise.

## Docker Container

### backend

- **Image**: self-hosted (ghrc)
- **Description**: Serves the Chatbot Backend
- **Url**: [http://iai-ml4home028.iai.kit.edu/chatbot](http://iai-ml4home028.iai.kit.edu/chat)
- **Additional Info** If your build is not a deployed production build, this Service can be used for everything for simplicity. For your final version, the access to the local Volumes this Service is given should be commented out or deleted.

### backend-staging

- **Image**: self-built
- **Description**: Serves the Chatbot Backend. This is the staging environment.
- **Url**: [http://iai-ml4home028.iai.kit.edu/chatbot-staging](http://iai-ml4home028.iai.kit.edu/chat-staging)
- **Additional Info** This Service is only necessary if you are testing changes that must not be published to a running production build

### chat_history

- **Image**: `postgres:16`
- **Description**: Stores the user chat history

### chat_history-staging

- **Image**: `postgres:16`
- **Description**: Stores the user chat history. This is the staging environment.
