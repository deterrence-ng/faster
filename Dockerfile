# Bissmillahirrahmanirraheem

FROM python:3.13

ENV ENVIRONMENT="PRODUCTION"

ENV GPG_TTY=/dev/console

ENV PYTHONUNBUFFERED="TRUE"
ENV PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg2 \
    gpg \
    nano \
    wget \
    build-essential


# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv


WORKDIR /app

COPY . .

RUN uv sync --frozen --no-cache

RUN ["/bin/bash", "-c", "source .venv/bin/activate && alembic upgrade head && python initialize.py"]

CMD ["/bin/bash", "-c",  "source .venv/bin/activate && uvicorn app.main:app --port $PORT --host 0.0.0.0"]

