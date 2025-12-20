FROM redis:6-alpine

# Copy the custom configuration file
COPY redis.conf /usr/local/etc/redis/redis.conf

# Start Redis with the custom configuration
CMD [ "redis-server", "/usr/local/etc/redis/redis.conf" ]