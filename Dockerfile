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

# Copy application code
COPY . .

# Create and set permissions for the Numba cache directory
RUN mkdir -p /var/cache/numba && \
    chown -R appuser:appgroup /var/cache/numba

# Change ownership to the non-root user
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

# The command to run the application will be specified by your hosting provider (e.g., Render)
# or in a docker-compose.yml file. It would typically be:
# CMD ["gunicorn", "Nexus.wsgi:application"]