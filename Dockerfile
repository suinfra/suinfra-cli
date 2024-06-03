FROM python:3.12-slim-bookworm as poetry_base

ENV POETRY_VERSION=1.8.3

RUN apt update -y && apt install -y curl
RUN curl -sSL https://install.python-poetry.org | python

FROM poetry_base as builder

WORKDIR /app

RUN apt -y install build-essential

RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.local/share/pypoetry/venv/bin:/root/.cargo/bin:${PATH}"

COPY README.md ./README.md
COPY pyproject.toml poetry.lock ./
COPY ./suinfra_cli ./suinfra_cli

RUN poetry config virtualenvs.in-project true \
    && poetry install --no-interaction --no-ansi --without=dev

FROM poetry_base as runtime

WORKDIR /app

COPY README.md /app/README.md
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/pyproject.toml /app/pyproject.toml
COPY --from=builder /app/poetry.lock /app/poetry.lock
COPY --from=builder /app/suinfra_cli /app/suinfra_cli

ENTRYPOINT ["/root/.local/share/pypoetry/venv/bin/poetry"]