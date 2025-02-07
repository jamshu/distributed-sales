#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
    echo -e "${GREEN}[*] $1${NC}"
}

print_error() {
    echo -e "${RED}[!] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[!] $1${NC}"
}

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root"
    exit 1
fi

# Prompt for configuration values
read -p "Enter PostgreSQL username [django]: " PG_USER
PG_USER=${PG_USER:-django}

read -sp "Enter PostgreSQL password: " PG_PASSWORD
echo
read -sp "Confirm PostgreSQL password: " PG_PASSWORD_CONFIRM
echo

if [ "$PG_PASSWORD" != "$PG_PASSWORD_CONFIRM" ]; then
    print_error "Passwords do not match!"
    exit 1
fi

read -p "Enter PostgreSQL host [localhost]: " PG_HOST
PG_HOST=${PG_HOST:-localhost}

read -p "Enter PostgreSQL port [5432]: " PG_PORT
PG_PORT=${PG_PORT:-5432}

read -p "Enter PgBouncer port [6432]: " PGBOUNCER_PORT
PGBOUNCER_PORT=${PGBOUNCER_PORT:-6432}

# Install required packages
print_status "Installing PgBouncer and dependencies..."
apt-get update
apt-get install -y pgbouncer postgresql-client-14

# Backup original config
print_status "Backing up original configuration..."
cp /etc/pgbouncer/pgbouncer.ini /etc/pgbouncer/pgbouncer.ini.bak

# Create directories
print_status "Creating required directories..."
mkdir -p /etc/pgbouncer
mkdir -p /var/log/pgbouncer
mkdir -p /var/run/pgbouncer

# Generate MD5 password
print_status "Generating MD5 password hash..."
MD5_PASS=$(printf "%s%s" "$PG_PASSWORD" "$PG_USER" | md5sum | cut -d' ' -f1)
echo "\"$PG_USER\" \"md5$MD5_PASS\"" > /etc/pgbouncer/userlist.txt

# Configure PgBouncer
print_status "Configuring PgBouncer..."
cat > /etc/pgbouncer/pgbouncer.ini << EOL
[databases]
* = host=$PG_HOST port=$PG_PORT

[pgbouncer]
logfile = /var/log/pgbouncer/pgbouncer.log
pidfile = /var/run/pgbouncer/pgbouncer.pid

listen_addr = *
listen_port = $PGBOUNCER_PORT

auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt

; Pool settings
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 5      
min_pool_size = 2         
reserve_pool_size = 1      
max_db_connections = 360   

; Connection lifetime
server_reset_query = DISCARD ALL
server_idle_timeout = 240
server_lifetime = 3600

; TCP Keepalive
tcp_keepalive = 1
tcp_keepidle = 30
tcp_keepintvl = 10

; Memory management
max_prepared_statements = 0

; Logging
admin_users = $PG_USER
stats_users = $PG_USER
EOL

# Set permissions
print_status "Setting permissions..."
chown -R postgres:postgres /etc/pgbouncer
chown -R postgres:postgres /var/log/pgbouncer
chown -R postgres:postgres /var/run/pgbouncer
chmod 640 /etc/pgbouncer/userlist.txt
chmod 640 /etc/pgbouncer/pgbouncer.ini

# Create systemd service if it doesn't exist
if [ ! -f /etc/systemd/system/pgbouncer.service ]; then
    print_status "Creating systemd service..."
    cat > /etc/systemd/system/pgbouncer.service << EOL
[Unit]
Description=PgBouncer connection pooler
Documentation=https://www.pgbouncer.org/
After=network.target

[Service]
Type=simple
User=postgres
Group=postgres
ExecStart=/usr/sbin/pgbouncer /etc/pgbouncer/pgbouncer.ini
ExecReload=/bin/kill -HUP \$MAINPID
PIDFile=/var/run/pgbouncer/pgbouncer.pid
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOL
fi

# Reload systemd and restart PgBouncer
print_status "Starting PgBouncer service..."
systemctl daemon-reload
systemctl enable pgbouncer
systemctl restart pgbouncer

# Wait a few seconds for the service to start
sleep 5

# Check if PgBouncer is running
if systemctl is-active --quiet pgbouncer; then
    print_status "PgBouncer installation completed successfully!"
    print_status "PgBouncer is running on port $PGBOUNCER_PORT"
    
    # Print Django settings
    print_status "Add these settings to your Django configuration:"
    echo -e "${GREEN}"
    cat << EOL
DATABASES = {
    'default': {
        'ENGINE': 'timescale.db.backends.postgresql',
        'NAME': 'your_database_name',
        'USER': '$PG_USER',
        'PASSWORD': '$PG_PASSWORD',
        'HOST': 'localhost',
        'PORT': '$PGBOUNCER_PORT',
        'CONN_MAX_AGE': 300,
        'OPTIONS': {
            'application_name': 'django_app'
        }
    }
}
EOL
    echo -e "${NC}"
else
    print_error "PgBouncer failed to start. Check logs with: journalctl -u pgbouncer"
fi

# Print verification commands
print_status "To verify installation, run these commands:"
echo "psql -h localhost -p $PGBOUNCER_PORT -U $PG_USER -d pgbouncer -c 'SHOW POOLS;'"
echo "psql -h localhost -p $PGBOUNCER_PORT -U $PG_USER -d pgbouncer -c 'SHOW DATABASES;'"