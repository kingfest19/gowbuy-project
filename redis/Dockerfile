FROM redis:6-alpine

# Copy the custom configuration file
COPY redis.conf /usr/local/etc/redis/redis.conf

# Fix potential Windows line endings (CRLF) and set permissions
# This prevents "Application exited early" errors due to config parsing failures
RUN sed -i 's/\r$//' /usr/local/etc/redis/redis.conf && \
    chown redis:redis /usr/local/etc/redis/redis.conf

# Start Redis with the custom configuration
CMD [ "redis-server", "/usr/local/etc/redis/redis.conf" ]