FROM redis:6-alpine

# Run as root to avoid permission issues with the persistent volume
USER root

# Override the default entrypoint to prevent the base image from dropping privileges
ENTRYPOINT []

# Start Redis directly
# Start Redis with a memory limit and an eviction policy.
# --maxmemory 24mb: Sets a hard memory limit just below the typical 25MB free tier limit.
# --maxmemory-policy allkeys-lru: When the memory limit is reached, Redis will
# automatically remove the "least recently used" keys to make space. This is
# ideal for caches and Celery result backends.
CMD [ "redis-server", "--bind", "0.0.0.0", "--port", "6379", "--protected-mode", "no", "--dir", "/data", "--maxmemory", "24mb", "--maxmemory-policy", "allkeys-lru" ]