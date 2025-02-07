# gunicorn_config.py
workers = 4  # Adjust based on your CPU cores (2-4 x num_cores)
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 50