ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim AS python-base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

FROM python-base AS builder

RUN apt-get update  \
    && apt-get install -y --no-install-recommends  \
    curl  \
    ca-certificates

ARG UV_VERSION=0.5.27
ADD https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-installer.sh /uv-installer.sh

RUN sh /uv-installer.sh  \
    && rm /uv-installer.sh

ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

FROM python:3.12-slim

ARG UID=10001
ARG GID=10001
RUN addgroup --gid "${GID}" appgroup && \
  adduser \
  --disabled-password \
  --gecos "" \
  --home "/nonexistent" \
  --shell "/sbin/nologin" \
  --no-create-home \
  --uid "${UID}" \
  --gid "${GID}" \
  appuser

USER appuser

COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY ./app .

CMD ["gunicorn", "-b", "0.0.0.0:8000", "--certfile", "./certs/server.crt.pem", "--keyfile", "./certs/server.key.pem", "main:app"]