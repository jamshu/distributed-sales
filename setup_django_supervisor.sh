#!/bin/bash


# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}



# Variables
USER_HOME=$(eval echo ~$USER) # Get the home directory of the current user
PROJECT_DIR="$(dirname "$(realpath "$0")")" # The Django project path in the user's home directory
PROJECT_NAME="cfedsales" # The Django project name
VENV_DIR="$PROJECT_DIR/venv" # Virtual environment directory inside the project
LOG_DIR="/var/log/supervisor"
SUPERVISOR_CONF="/etc/supervisor/conf.d/django_project.conf"
DB_USER="django"
DB_PASSWORD="secure_password"



# Add PostgreSQL repository
echo "Adding PostgreSQL repository..."
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -

# Add TimescaleDB repository
echo "Adding TimescaleDB repository..."
echo "deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main" | sudo tee /etc/apt/sources.list.d/timescaledb.list
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/timescaledb.gpg

# Update package list again
sudo apt-get update

sudo apt-get update -y
sudo apt-get install -y apt-transport-https
sudo apt-get install -y supervisor python3-venv python3-pip wget gnupg lsb-release
sudo apt-get install -y postgresql-14
sudo apt-get install -y redis-server

# Step 2: Enable and Start Redis Server
echo "Configuring Redis server..."
sudo systemctl enable redis
sudo systemctl start redis
# Step 2: Install TimescaleDB
echo "Installing TimescaleDB..."
sudo apt-get install -y timescaledb-2-postgresql-14

# Configure TimescaleDB
echo "Configuring TimescaleDB..."
sudo timescaledb-tune --quiet --yes
sudo systemctl restart postgresql

# Step 3: Configure PostgreSQL
echo "Configuring PostgreSQL..."
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "ALTER USER $DB_USER CREATEDB;"


# Step 4: Create log directory
echo "Creating log directory..."
sudo mkdir -p $LOG_DIR
sudo chown $USER:$USER $LOG_DIR

# Step 5: Create Supervisor configuration file
echo "Creating Supervisor configuration..."
sudo tee $SUPERVISOR_CONF > /dev/null <<EOL
[supervisord]
nodaemon=true

[program:send_summary]
command=$VENV_DIR/bin/python3 $PROJECT_DIR/manage.py rqworker send_summary
directory=$PROJECT_DIR
numprocs=2
process_name=%(program_name)s_%(process_num)02d
autostart=true
autorestart=true
stdout_logfile=$LOG_DIR/rq_send_summary.log
stderr_logfile=$LOG_DIR/rq_send_summary_error.log

[program:rq_sales_processing]
command=$VENV_DIR/bin/python3 $PROJECT_DIR/manage.py rqworker sales_processing
directory=$PROJECT_DIR
numprocs=4
process_name=%(program_name)s_%(process_num)02d
autostart=true
autorestart=true
stdout_logfile=$LOG_DIR/rq_sales_processing.log
stderr_logfile=$LOG_DIR/rq_sales_processing_error.log

[program:rq_day_close]
command=$VENV_DIR/bin/python3 $PROJECT_DIR/manage.py rqworker day_close
directory=$PROJECT_DIR
numprocs=12
process_name=%(program_name)s_%(process_num)02d
autostart=true
autorestart=true
stdout_logfile=$LOG_DIR/rq_day_close_%(process_num)02d.log
stderr_logfile=$LOG_DIR/rq_day_close_error_%(process_num)02d.log
EOL

# Step 9: Update Supervisor configuration
echo "Updating Supervisor service..."
sudo supervisorctl reread
sudo supervisorctl update

# Step 10: Start Supervisor services
echo "Starting Supervisor services..."
sudo systemctl enable supervisor
sudo systemctl start supervisor

# Status check
echo "Supervisor Status:"
sudo supervisorctl status

echo "Setup Complete!"
echo "User: $DB_USER"
echo "Password: $DB_PASSWORD"
