# Gunicorn Configuration for BYOB Flask Blog
# Production-ready configuration with HTTP/2 support

import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gthread"
threads = 2
worker_connections = 1000

# Worker lifecycle
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Process management: only drop privileges when running as root
if hasattr(os, "geteuid") and os.geteuid() == 0:
    user = os.getenv("GUNICORN_USER", "byob")
    group = os.getenv("GUNICORN_GROUP", "byob")

# Logging
accesslog = os.getenv("GUNICORN_ACCESS_LOG", "/var/log/byob/access.log")
errorlog = os.getenv("GUNICORN_ERROR_LOG", "/var/log/byob/error.log")
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Performance tuning
worker_tmp_dir = "/dev/shm"  # Use RAM for worker temp files
