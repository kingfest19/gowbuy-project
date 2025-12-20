FROM redis:6-alpine

# Create the config directory
RUN mkdir -p /usr/local/etc/redis

# Generate redis.conf dynamically to avoid Windows line-ending issues (CRLF)
RUN echo "bind 0.0.0.0" > /usr/local/etc/redis/redis.conf && \
    echo "port 6379" >> /usr/local/etc/redis/redis.conf && \
    echo "protected-mode no" >> /usr/local/etc/redis/redis.conf && \
    echo "daemonize no" >> /usr/local/etc/redis/redis.conf && \
    echo "dir /data" >> /usr/local/etc/redis/redis.conf && \
    echo "dbfilename dump.rdb" >> /usr/local/etc/redis/redis.conf && \
    echo "save 900 1" >> /usr/local/etc/redis/redis.conf && \
    echo "save 300 10" >> /usr/local/etc/redis/redis.conf && \
    chown redis:redis /usr/local/etc/redis/redis.conf

# Start Redis with the custom configuration
CMD [ "redis-server", "/usr/local/etc/redis/redis.conf" ]