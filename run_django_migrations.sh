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

# Step 5: Set up Virtual Environment
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment in $VENV_DIR..."
  python3 -m venv $VENV_DIR
fi


# Activate Virtual Environment
echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

# Step 6: Install Python requirements
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
  echo "Installing Python requirements..."
  pip install --upgrade pip
  pip install -r $PROJECT_DIR/requirements.txt
else
  echo "requirements.txt not found in $PROJECT_DIR. Skipping installation."
fi

# Step 7: Django initial setup - Migrate Database and Custom Commands
echo "Running Django management commands..."
python3 $PROJECT_DIR/manage.py create_shard_database
python3 $PROJECT_DIR/manage.py enable_timescale
python3 $PROJECT_DIR/manage.py migrate
python3 $PROJECT_DIR/manage.py migrate_shards
