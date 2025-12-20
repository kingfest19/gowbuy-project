FROM redis:6-alpine

# Switch to root to ensure we can fix permissions on the volume
USER root

# Fix permissions on /data (in case the volume is owned by root) and start Redis
# We use 'sh -c' to execute the permission fix followed by the server start
CMD [ "sh", "-c", "chown -R redis:redis /data && redis-server --bind 0.0.0.0 --port 6379 --protected-mode no --dir /data" ]