# ==============================================================================
# AeroCool-AI: Production Dockerfile
# ==============================================================================
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Install system dependencies including GDAL, PROJ, GEOS for geospatial operations
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for ultra-fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copy dependency definition
COPY pyproject.toml README.md ./

# Install dependencies using uv
RUN uv pip install --system -r pyproject.toml

# Copy application source code
COPY src/ /app/src/

# Install the application in editable mode
RUN uv pip install --system -e .

EXPOSE 8000

CMD ["uvicorn", "aerocool_ai.backend_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
