FROM redis:6-alpine

# Start Redis with configuration passed directly as command-line arguments.
# This bypasses any issues with config file creation, permissions, or line endings.
CMD [ "redis-server", "--bind", "0.0.0.0", "--port", "6379", "--protected-mode", "no", "--dir", "/data" ]