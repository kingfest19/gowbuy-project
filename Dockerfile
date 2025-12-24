# syntax=docker/dockerfile:1

# ---- Builder Stage ----
# This stage installs dependencies and builds the application.
FROM python:3.11-slim-bullseye AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies required for packages like psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev

# Install python dependencies
# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt


# ---- Runtime Stage ----
# This stage creates the final, smaller image.
FROM python:3.11-slim-bullseye AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV NUMBA_CACHE_DIR=/var/cache/numba
ENV HOME=/home/appuser

# Create a non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Install only necessary system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Copy installed python packages from builder stage
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# Copy application code. This is commented out for faster local development,
# The docker-compose.yml file uses a volume to mount the code directly.
# For production builds (like on Render), this line should be UNCOMMENTED.
COPY . .

# Create and set permissions for the Numba cache directory
RUN mkdir -p /var/cache/numba && \
    chown -R appuser:appgroup /var/cache/numba

# Create home directory and ensure permissions (for rembg/u2net cache)
RUN mkdir -p /home/appuser && chown -R appuser:appgroup /home/appuser

# Change ownership to the non-root user
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

# Start the application using Gunicorn. We use the shell form to allow variable expansion.
CMD gunicorn Nexus.wsgi:application --bind 0.0.0.0:${PORT:-10000}