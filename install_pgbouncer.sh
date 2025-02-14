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

PG_USER="django"
# Prompt for configuration values

read -p "Enter PostgreSQL host [localhost]: " PG_HOST
PG_HOST=${PG_HOST:-localhost}

read -p "Enter PostgreSQL port [5432]: " PG_PORT
PG_PORT=${PG_PORT:-5432}

read -p "Enter PgBouncer port [6432]: " PGBOUNCER_PORT
PGBOUNCER_PORT=${PGBOUNCER_PORT:-6432}

# New prompts for pool settings
read -p "Enter max client connections [1000]: " MAX_CLIENT_CONN
MAX_CLIENT_CONN=${MAX_CLIENT_CONN:-1000}

read -p "Enter default pool size [5]: " DEFAULT_POOL_SIZE
DEFAULT_POOL_SIZE=${DEFAULT_POOL_SIZE:-5}

read -p "Enter max DB connections [360]: " MAX_DB_CONN
MAX_DB_CONN=${MAX_DB_CONN:-360}

# Install required packages
print_status "Installing PgBouncer and dependencies..."
apt-get install -y pgbouncer postgresql-client-14

# Stop PgBouncer if running
systemctl stop pgbouncer

# Backup original config
print_status "Backing up original configuration..."
if [ -f /etc/pgbouncer/pgbouncer.ini ]; then
    cp /etc/pgbouncer/pgbouncer.ini /etc/pgbouncer/pgbouncer.ini.bak.$(date +%Y%m%d_%H%M%S)
fi

# Create directories with proper permissions
print_status "Creating required directories..."
install -d -m 755 -o postgres -g postgres /etc/pgbouncer
install -d -m 755 -o postgres -g postgres /var/log/pgbouncer
install -d -m 755 -o postgres -g postgres /var/run/pgbouncer

# Create log file with proper permissions
touch /var/log/pgbouncer/pgbouncer.log
chown postgres:postgres /var/log/pgbouncer/pgbouncer.log
chmod 640 /var/log/pgbouncer/pgbouncer.log

# Generate password hash directly from PostgreSQL
print_status "Getting PostgreSQL password hash..."
PG_HASH=$(su - postgres -c "psql -c \"SELECT concat('\\\"$PG_USER\\\" \\\"', passwd, '\\\"') FROM pg_shadow WHERE usename='$PG_USER'\" -t -A")
echo "$PG_HASH" > /etc/pgbouncer/userlist.txt
chmod 640 /etc/pgbouncer/userlist.txt
chown postgres:postgres /etc/pgbouncer/userlist.txt

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

pool_mode = transaction
max_client_conn = $MAX_CLIENT_CONN
default_pool_size = $DEFAULT_POOL_SIZE
min_pool_size = 2
reserve_pool_size = 1
max_db_connections = $MAX_DB_CONN

server_reset_query = DISCARD ALL
server_idle_timeout = 60
server_lifetime = 3600

tcp_keepalive = 1
tcp_keepidle = 30
tcp_keepintvl = 10


admin_users = $PG_USER
stats_users = $PG_USER

tcp_defer_accept = 1
tcp_socket_buffer = 0
so_reuseport = 1
EOL

chmod 640 /etc/pgbouncer/pgbouncer.ini
chown postgres:postgres /etc/pgbouncer/pgbouncer.ini

# Create systemd service
print_status "Creating systemd service..."
cat > /etc/systemd/system/pgbouncer.service << EOL
[Unit]
Description=PgBouncer connection pooler
Documentation=https://www.pgbouncer.org/
After=network.target postgresql.service

[Service]
Type=simple
User=postgres
Group=postgres
Environment=LANG=en_US.UTF-8
RuntimeDirectory=pgbouncer
RuntimeDirectoryMode=0755
ExecStart=/usr/sbin/pgbouncer /etc/pgbouncer/pgbouncer.ini
ExecReload=/bin/kill -HUP \$MAINPID
PIDFile=/var/run/pgbouncer/pgbouncer.pid
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL

# Create logrotate configuration
print_status "Configuring log rotation..."
cat > /etc/logrotate.d/pgbouncer << EOL
/var/log/pgbouncer/pgbouncer.log {
    daily
    rotate 7
    missingok
    compress
    delaycompress
    notifempty
    create 640 postgres postgres
    postrotate
        /bin/kill -HUP \`cat /var/run/pgbouncer/pgbouncer.pid 2>/dev/null\` 2> /dev/null || true
    endscript
}
EOL

# Reload systemd and restart PgBouncer
print_status "Starting PgBouncer service..."
systemctl daemon-reload
systemctl enable pgbouncer
systemctl restart pgbouncer

# Wait for service to start
sleep 5

# Check if PgBouncer is running
if systemctl is-active --quiet pgbouncer; then
    print_status "PgBouncer installation completed successfully!"
    print_status "PgBouncer is running on port $PGBOUNCER_PORT"
    
   

    # Print monitoring commands
    print_status "Monitoring commands:"
    echo "Show pools: psql -h localhost -p $PGBOUNCER_PORT -U $PG_USER -d pgbouncer -c 'SHOW POOLS;'"
    echo "Show clients: psql -h localhost -p $PGBOUNCER_PORT -U $PG_USER -d pgbouncer -c 'SHOW CLIENTS;'"
    echo "Show servers: psql -h localhost -p $PGBOUNCER_PORT -U $PG_USER -d pgbouncer -c 'SHOW SERVERS;'"
    echo "Show stats: psql -h localhost -p $PGBOUNCER_PORT -U $PG_USER -d pgbouncer -c 'SHOW STATS;'"
else
    print_error "PgBouncer failed to start. Check logs with: journalctl -u pgbouncer"
fi