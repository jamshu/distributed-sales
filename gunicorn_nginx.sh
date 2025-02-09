#!/bin/bash

# Django Deployment Automated Script
# Usage: ./deploy.sh /path/to/project ProjectName domain.com username

# Arguments
PROJECT_PATH="$(dirname "$(realpath "$0")")"
PROJECT_NAME="cfedsales"
DOMAIN="localhost"
USERNAME=$USER

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Log function
log() {
    echo -e "${GREEN}[DEPLOY] $1${NC}"
}

# Error function
error() {
    echo -e "${YELLOW}[ERROR] $1${NC}"
    exit 1
}

# Validate inputs
validate_inputs() {
    # Check if project path exists
    if [ ! -d "$PROJECT_PATH" ]; then
        error "Project path does not exist: $PROJECT_PATH"
    fi

    # Check if user exists
    id "$USERNAME" &>/dev/null || error "User $USERNAME does not exist"
}

# System Update and Dependencies
system_prep() {
    log "Updating system and installing dependencies..."
    sudo apt install -y nginx ufw
}

# Django Project Configuration
configure_django() {
    log "Configuring Django project..."
    cd "$PROJECT_PATH"
    source venv/bin/activate
    
    # Create a directory for static files
    STATIC_ROOT="/static"
    sudo mkdir -p "$STATIC_ROOT"
    sudo chown -R $USERNAME:www-data "$STATIC_ROOT"
    sudo chmod -R 755 "$STATIC_ROOT"
    
    # Collect static files
    python3 manage.py collectstatic --noinput --clear --settings=$PROJECT_NAME.settings
    
    deactivate
}

# Gunicorn Socket Configuration
configure_gunicorn_socket() {
    log "Configuring Gunicorn socket..."
    sudo tee /etc/systemd/system/gunicorn.socket > /dev/null <<EOL
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
EOL
}

# Gunicorn Service Configuration
configure_gunicorn_service() {
    log "Configuring Gunicorn service..."
    
    # Create Gunicorn log directory and set permissions
    log "Creating Gunicorn log directory..."
    sudo mkdir -p /var/log/gunicorn
    sudo chown -R $USERNAME:www-data /var/log/gunicorn
    sudo chmod -R 755  /var/log/gunicorn
    
    sudo tee /etc/systemd/system/gunicorn.service > /dev/null <<EOL
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=$USERNAME
Group=www-data
WorkingDirectory=$PROJECT_PATH
ExecStart=$PROJECT_PATH/venv/bin/gunicorn \
    --config $PROJECT_PATH/gunicorn_config.py \
    --bind unix:/run/gunicorn.sock \
    $PROJECT_NAME.wsgi:application

[Install]
WantedBy=multi-user.target
EOL
}

# Nginx Configuration
configure_nginx() {
    log "Configuring Nginx..."
    STATIC_ROOT="/static"
    
    sudo tee /etc/nginx/sites-available/"$PROJECT_NAME" > /dev/null <<EOL
server {
     listen 80;
    
     server_name _;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias $STATIC_ROOT/;
    }

    location /media/ {
        root $PROJECT_PATH;
    }
    location = / {
        return 301 /sales/dashboard;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
EOL

    # Enable site and test configuration
    sudo ln -sf /etc/nginx/sites-available/"$PROJECT_NAME" /etc/nginx/sites-enabled/
    sudo rm /etc/nginx/sites-enabled/default
    sudo rm /etc/nginx/sites-available/default
    sudo nginx -t || error "Nginx configuration test failed"
}

# Firewall Configuration
configure_firewall() {
    log "Configuring firewall..."
    sudo ufw allow 'Nginx Full'
    sudo ufw enable
}

# Start and Enable Services
start_services() {
    log "Starting and enabling services..."
    sudo systemctl start gunicorn.socket
    sudo systemctl enable gunicorn.socket
    sudo systemctl restart gunicorn.service
    sudo systemctl restart nginx
}

# Main Deployment Function
main() {
    validate_inputs
    system_prep
    configure_django
    configure_gunicorn_socket
    configure_gunicorn_service
    configure_nginx
    configure_firewall
    start_services

    log "Deployment completed successfully!"
}

# Run main function
main

# Optional: Print credentials or additional notes
echo "Deployment Complete for $PROJECT_NAME"
echo "Domain: $DOMAIN"