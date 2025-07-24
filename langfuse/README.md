# Langfuse

This package contains a Docker Compose configuration for setting up and running the Langfuse Server along with a PostgreSQL database.

Langfuse is an open-source LLM engineering platform.
Useful for debugging, tracing and monitoring LLMs in real-time, it also supports user feedback collection.
Read more about Langfuse [here](https://github.com/langfuse/langfuse).

## Docker Container

### [Langfuse Server](https://github.com/langfuse/langfuse)

- **Image**: `langfuse/langfuse`
- **Description**: Langfuse is an open-source LLM engineering platform. It is useful for debugging, tracing, and monitoring LLMs in real-time. It also supports user feedback collection.
- **Deployment**: As langfuse doesn't support relative base path currently, we can only host it under the port 8999. To access the server, visit `http://iai-ml4home028.iai.kit.edu:8999/`

### [PostgreSQL Database](https://hub.docker.com/_/postgres)

- **Image**: `postgres:16`
- **Description**: The Postgres database stores the data for Langfuse
