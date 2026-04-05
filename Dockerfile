# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile — Campus Scheduler OpenEnv Environment
#
# WHY this base image?
#   ghcr.io/meta-pytorch/openenv-base already has Python 3.11, uv, and the
#   openenv-core system dependencies pre-installed. Using it means a faster
#   build and fewer "works on my machine" issues.
#
# HOW HuggingFace Spaces uses this file:
#   1. When you push to the HF Space repo, HF runs `docker build .`
#   2. The container starts and runs your CMD
#   3. HF exposes port 7860 (we map our 8000 → 7860 in the CMD)
#   4. Judges ping https://sky001000-campus-scheduler.hf.space/health
# ─────────────────────────────────────────────────────────────────────────────

FROM ghcr.io/meta-pytorch/openenv-base:latest

WORKDIR /app

# ── Copy dependency manifest first (for Docker layer caching) ────────────────
# Copying these before the source code means Docker reuses the cached
# install layer unless dependencies actually changed.
COPY pyproject.toml ./

# ── Copy the full project source ─────────────────────────────────────────────
COPY . .

# ── Install dependencies ──────────────────────────────────────────────────────
# uv is pre-installed in the openenv-base image.
# We install in --system mode so packages go to the system Python (no venv needed).
# Fallback: if uv isn't available, use pip with server/requirements.txt.
RUN if command -v uv > /dev/null 2>&1; then \
        uv pip install --system -r server/requirements.txt; \
    else \
        pip install --no-cache-dir -r server/requirements.txt; \
    fi

# ── Set PYTHONPATH so imports from root (models.py etc.) resolve ─────────────
ENV PYTHONPATH="/app:$PYTHONPATH"

# ── Health check (judges use GET /health to confirm the Space is live) ────────
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/health')" || exit 1

# ── HuggingFace Spaces requires port 7860 ────────────────────────────────────
EXPOSE 7860

# ── Start the FastAPI server ──────────────────────────────────────────────────
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
