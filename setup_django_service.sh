#!/bin/bash

# Exit on any error
set -e

# Default values
PROJECT_NAME="cfedsales"
PROJECT_PATH="$(dirname "$(realpath "$0")")"
VENV_PATH="$PROJECT_PATH/venv"
USER_NAME=$(whoami)
GUNICORN_PORT="3000"
MAX_REQUESTS="1000"
MAX_REQUESTS_JITTER="50"

# Function to display script usage
usage() {
    echo "Usage: $0 -p PROJECT_PATH -n PROJECT_NAME [-v VENV_PATH] [-u USER_NAME] [-g GUNICORN_PORT] [-m MAX_REQUESTS]"
    echo "  -p: Full path to Django project directory"
    echo "  -n: Django project name (used in WSGI application)"
    echo "  -v: Path to virtual environment (optional, defaults to PROJECT_PATH/venv)"
    echo "  -u: User to run the service as (optional, defaults to current user)"
    echo "  -g: Gunicorn port (optional, defaults to 3000)"
    echo "  -m: Max requests per worker (optional, defaults to 1000)"
    exit 1
}

# Parse command line arguments
while getopts "p:n:v:u:g:m:h" opt; do
    case $opt in
        p) PROJECT_PATH="$OPTARG" ;;
        n) PROJECT_NAME="$OPTARG" ;;
        v) VENV_PATH="$OPTARG" ;;
        u) USER_NAME="$OPTARG" ;;
        g) GUNICORN_PORT="$OPTARG" ;;
        m) MAX_REQUESTS="$OPTARG" ;;
        h) usage ;;
        ?) usage ;;
    esac
done

# Validate required parameters
if [ -z "$PROJECT_PATH" ] || [ -z "$PROJECT_NAME" ]; then
    echo "Error: Project path and name are required"
    usage
fi

# Set default virtual environment path if not provided
if [ -z "$VENV_PATH" ]; then
    VENV_PATH="$PROJECT_PATH/venv"
fi

# Ensure paths are absolute
PROJECT_PATH=$(realpath "$PROJECT_PATH")
VENV_PATH=$(realpath "$VENV_PATH")

echo "Setting up Gunicorn service for Django project..."
echo "Project Path: $PROJECT_PATH"
echo "Project Name: $PROJECT_NAME"
echo "Virtual Env: $VENV_PATH"
echo "User: $USER_NAME"
echo "Port: $GUNICORN_PORT"

# Create Gunicorn config
echo "Creating Gunicorn configuration..."
cat << EOF > "$PROJECT_PATH/gunicorn_config.py"
import multiprocessing

bind = "0.0.0.0:$GUNICORN_PORT"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gthread"
threads = 2
timeout = 120
keepalive = 5
max_requests = $MAX_REQUESTS
max_requests_jitter = $MAX_REQUESTS_JITTER
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"
EOF

# Create log directory
echo "Creating log directory..."
sudo mkdir -p /var/log/gunicorn
sudo chown -R "$USER_NAME:$USER_NAME" /var/log/gunicorn

# Create systemd service file
echo "Creating systemd service..."
sudo bash -c "cat << EOF > /etc/systemd/system/django-$PROJECT_NAME.service
[Unit]
Description=Django Application Server ($PROJECT_NAME)
After=network.target

[Service]
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$PROJECT_PATH
Environment=\"PATH=$VENV_PATH/bin\"
ExecStart=$VENV_PATH/bin/gunicorn \\
    --config gunicorn_config.py \\
    ${PROJECT_NAME}.wsgi:application

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF"

# Reload systemd and enable service
echo "Configuring systemd service..."
sudo systemctl daemon-reload
sudo systemctl enable "django-$PROJECT_NAME"
sudo systemctl start "django-$PROJECT_NAME"

# Check service status
echo "Checking service status..."
sudo systemctl status "django-$PROJECT_NAME"

echo "Setup complete! Your Django application is now running as a service."
echo ""
echo "Useful commands:"
echo "  Check status: sudo systemctl status django-$PROJECT_NAME"
echo "  View logs: sudo journalctl -u django-$PROJECT_NAME"
echo "  Restart service: sudo systemctl restart django-$PROJECT_NAME"
echo "  Stop service: sudo systemctl stop django-$PROJECT_NAME"