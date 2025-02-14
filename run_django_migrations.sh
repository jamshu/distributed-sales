#!/bin/bash


# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color
# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

print_error() {
    echo -e "${RED}[!] $1${NC}"
}

if [ "$EUID" -eq 0 ]; then 
    print_error "This script should not be run as root"
    exit 1
fi



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



# Step 7: Django initial setup - Migrate Database and Custom Commands
echo "Running Django management commands..."
python3 $PROJECT_DIR/manage.py create_shard_database
python3 $PROJECT_DIR/manage.py enable_timescale
python3 $PROJECT_DIR/manage.py migrate
python3 $PROJECT_DIR/manage.py migrate_shards
