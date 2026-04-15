# Multi-stage build for ARM64 (Raspberry Pi 5)
FROM python:3.12-slim AS base

# System deps
# - gcc/g++/cmake: required to compile llama-cpp-python from source on ARM64
# - libopenblas-dev: BLAS acceleration for llama-cpp on ARM (significant speedup)
# - libpq-dev: asyncpg PostgreSQL driver
# - pango/cairo/gdk-pixbuf: required by weasyprint for PDF generation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc=4:14.2.0-1 \
    g++=4:14.2.0-1 \
    cmake=3.31.6-2 \
    libopenblas-dev=0.3.29+ds-3 \
    libpq-dev=17.9-0+deb13u1 \
    libffi-dev=3.4.8-2 \
    libxml2-dev=2.12.7+dfsg+really2.9.14-2.1+deb13u2 \
    libxslt1-dev=1.1.35-1.2+deb13u2 \
    libcairo2=1.18.4-1+b1 \
    libpango-1.0-0=1.56.3-1 \
    libpangocairo-1.0-0=1.56.3-1 \
    libgdk-pixbuf-2.0-0=2.42.12+dfsg-4+deb13u1 \
    libfontconfig1=2.15.0-2.3 \
    shared-mime-info=2.4-5+b2 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install poetry
RUN pip install --no-cache-dir poetry==2.1.1

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install core dependencies (excludes optional LLM backends)
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-root --no-interaction

# Install llama-cpp-python with OpenBLAS acceleration for ARM64.
# This compiles from source — takes a few minutes on the Pi.
# OpenBLAS gives a meaningful throughput boost on the Cortex-A76 cores.
RUN CMAKE_ARGS="-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS" \
    pip install --no-cache-dir llama-cpp-python

# Copy source
COPY src/ ./src/
COPY .env.example ./.env.example

# Create directories
RUN mkdir -p /app/reports /app/models

# Non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
