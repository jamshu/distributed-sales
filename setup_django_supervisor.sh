#!/bin/bash

# Variables
USER_HOME=$(eval echo ~$USER) # Get the home directory of the current user
PROJECT_DIR="$USER_HOME/cfedsales" # The Django project path in the user's home directory
VENV_DIR="$PROJECT_DIR/venv" # Virtual environment directory inside the project
LOG_DIR="/var/log/supervisor"
SUPERVISOR_CONF="/etc/supervisor/conf.d/django_project.conf"

# Step 1: Install Supervisor
echo "Installing Supervisor..."
sudo apt-get update -y
sudo apt-get install -y supervisor

# Step 2: Create log directory
echo "Creating log directory..."
sudo mkdir -p $LOG_DIR
sudo chown $USER:$USER $LOG_DIR

# Step 3: Check and create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv $VENV_DIR
fi

# Step 4: Activate Virtual Environment
echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

# Step 5: Install dependencies from requirements.txt
echo "Installing dependencies from requirements.txt..."
pip install -r $PROJECT_DIR/requirements.txt

# Step 6: Set DJANGO_SETTINGS_MODULE if necessary (optional)
export DJANGO_SETTINGS_MODULE="cfedsales.settings"

# Step 7: Django initial setup - Migrate Database and Custom Commands
echo "Running Django management commands..."
python $PROJECT_DIR/manage.py migrate

# If you have any other custom commands to run, include them here
# Example: python $PROJECT_DIR/manage.py my_custom_command
# python $PROJECT_DIR/manage.py custom_command

# Step 8: Create Supervisor configuration file
echo "Creating Supervisor configuration..."
sudo tee $SUPERVISOR_CONF > /dev/null <<EOL
[supervisord]
nodaemon=true

[program:django]
command=$VENV_DIR/bin/python $PROJECT_DIR/manage.py runserver 0.0.0.0:8080
directory=$PROJECT_DIR
autostart=true
autorestart=true
stdout_logfile=$LOG_DIR/django.log
stderr_logfile=$LOG_DIR/django_error.log

[program:send_summary]
command=$VENV_DIR/bin/python $PROJECT_DIR/manage.py rqworker send_summary
directory=$PROJECT_DIR
numprocs=4
process_name=%(program_name)s_%(process_num)02d
autostart=true
autorestart=true
stdout_logfile=$LOG_DIR/rq_send_summary.log
stderr_logfile=$LOG_DIR/rq_send_summary_error.log

[program:rq_sales_processing]
command=$VENV_DIR/bin/python $PROJECT_DIR/manage.py rqworker sales_processing
directory=$PROJECT_DIR
numprocs=8
process_name=%(program_name)s_%(process_num)02d
autostart=true
autorestart=true
stdout_logfile=$LOG_DIR/rq_sales_processing.log
stderr_logfile=$LOG_DIR/rq_sales_processing_error.log

[program:rq_day_close]
command=$VENV_DIR/bin/python $PROJECT_DIR/manage.py rqworker day_close
directory=$PROJECT_DIR
numprocs=4
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

