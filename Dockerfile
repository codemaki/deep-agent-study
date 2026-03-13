FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy dependency files first (layer caching)
COPY pyproject.toml uv.lock* ./

# Install dependencies into system Python (no venv needed inside Docker)
RUN uv pip install --system \
    "deepagents>=0.4.10" \
    "langchain-openai>=0.3.0" \
    "python-dotenv>=1.0.0" \
    "rich>=13.0.0"

COPY main.py .env ./

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "main.py"]
CMD []
