FROM python:3.10-slim

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies globally using uv
RUN uv pip install --system -r pyproject.toml

# Copy environment code and server
COPY . .

# Expose the port for the OpenEnv validator API
EXPOSE 8000

# Start the web server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]