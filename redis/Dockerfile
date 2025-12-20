FROM redis:6-alpine

# Run as root to avoid permission issues with the persistent volume
USER root

# Override the default entrypoint to prevent the base image from dropping privileges
ENTRYPOINT []

# Start Redis directly
CMD [ "redis-server", "--bind", "0.0.0.0", "--port", "6379", "--protected-mode", "no", "--dir", "/data" ]