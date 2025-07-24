FROM python:3.12.3

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ffmpeg libsm6 libxext6 && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry && poetry config virtualenvs.create false

WORKDIR /code

COPY ../pyproject.toml ./README.md ./poetry.lock* ./

RUN poetry install  --no-interaction --no-ansi --no-root --without dev

COPY ./app ./app
COPY ./evaluate ./evaluate

RUN poetry install --no-interaction --no-ansi --without dev

EXPOSE 8080

CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8080", "--loop", "asyncio"]
