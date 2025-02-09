import os

# Worker configurations
workers = 4  # Adjust based on your CPU cores (2-4 x num_cores)
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 50

# Logging configurations
loglevel = "debug"
errorlog = "/var/log/gunicorn/error.log"
accesslog = "/var/log/gunicorn/access.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s'

# Ensure the log directory exists and has the right permissions
log_dir = "/var/log/gunicorn"
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)
    os.chmod(log_dir, 0o755)
