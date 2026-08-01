# syntax=docker/dockerfile:1
#
# Multi-stage Docker build for example-app
# See ADR-006 for the containerization strategy.
#
# The build context must be the repository root (not this directory) because
# libs/example-lib is a local path dependency required at build time:
#   docker build -f apps/example-app/Dockerfile .

# ── Stage 1: Builder ────────────────────────────────────────────────────────
# Resolves dependencies and pre-builds wheels for reproducible installs.
FROM python:3.12-slim AS builder

RUN pip install --no-cache-dir uv

WORKDIR /build

COPY pyproject.toml uv.lock ./

# Copy the shared library (local path dependency)
COPY libs/example-lib ./libs/example-lib

# Copy application manifests before source code for Docker layer cache efficiency
COPY apps/example-app/pyproject.toml ./apps/example-app/

# Use uv to generate requirements from the lock file for reproducible builds.
RUN uv export \
      --package example-app \
      --frozen \
      --no-dev \
      --no-hashes \
      --output-file /tmp/requirements.txt \
    && grep -vE "^(-e |example-lib)" /tmp/requirements.txt \
      > /tmp/app-requirements.txt || true

# Pre-build wheels for reproducible, offline installation in the runtime stage
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r /tmp/app-requirements.txt
RUN pip wheel --no-cache-dir --wheel-dir /wheels ./libs/example-lib

# ── Stage 2: Runtime ────────────────────────────────────────────────────────
# Minimal production image — no uv, no build tools, no source trees.
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install pre-built wheels (no network access needed at this stage)
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

# Copy application source code
COPY apps/example-app/app ./app

CMD ["python", "-m", "app.main"]
