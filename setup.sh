#!/bin/bash

# WeatherLink Data Logger Installation Script
# This script installs dependencies, configures the application, and sets up cron jobs

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if running as root (not required, but helpful for system installs)
if [[ $EUID -eq 0 ]]; then
   print_warning "Running as root. This is not necessary but will work fine."
fi

print_header "WeatherLink Data Logger - Installation"

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
print_info "Installation directory: $SCRIPT_DIR"

# Step 1: Update package manager
print_header "Step 1: Updating Package Manager"
if command -v apt-get &> /dev/null; then
    print_info "Detected Debian/Ubuntu system"
    sudo apt-get update
    print_success "Package manager updated"
elif command -v yum &> /dev/null; then
    print_info "Detected RedHat/CentOS system"
    sudo yum update -y
    print_success "Package manager updated"
else
    print_warning "Could not detect package manager. Skipping update."
fi

# Step 2: Install Python and pip
print_header "Step 2: Installing Python"
if ! command -v python3 &> /dev/null; then
    print_info "Python3 not found. Installing..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y python3 python3-pip
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3 python3-pip
    fi
    print_success "Python3 installed"
else
    PYTHON_VERSION=$(python3 --version)
    print_success "Python3 already installed: $PYTHON_VERSION"
fi

# Step 3: Install Python dependencies
print_header "Step 3: Installing Python Dependencies"
print_info "Installing requests library..."
if command -v apt-get &> /dev/null; then
    sudo apt-get install -y python3-requests 
else
    pip3 install requests
fi

print_success "Python dependencies installed"

# Step 4: Configure API credentials
print_header "Step 4: Configure WeatherLink API Credentials"
print_info "You need your API credentials from https://weatherlink.com/account/api"

read -p "Enter your API Key: " API_KEY
read -p "Enter your API Secret: " API_SECRET

print_info "Listing available stations..."
python3 "$SCRIPT_DIR/wl_logger.py" --list-stations 2>/dev/null || print_warning "Could not list stations. Make sure credentials are correct."

read -p "Enter your Station ID: " STATION_ID

# Update configuration in wl_logger.py
sed -i "s/API_KEY = .*/API_KEY = \"$API_KEY\"/" "$SCRIPT_DIR/wl_logger.py"
sed -i "s/API_SECRET = .*/API_SECRET = \"$API_SECRET\"/" "$SCRIPT_DIR/wl_logger.py"
sed -i "s/STATION_ID = .*/STATION_ID = \"$STATION_ID\"/" "$SCRIPT_DIR/wl_logger.py"

print_success "API credentials configured"

# Step 5: Configure email (optional)
print_header "Step 5: Configure Email (Optional)"
read -p "Do you want to set up email reporting? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter sender email (Gmail): " SENDER_EMAIL
    read -sp "Enter Gmail app password: " SENDER_PASSWORD
    echo
    read -p "Enter recipient email: " RECIPIENT_EMAIL
    
    # Update configuration in email_csv.py
    sed -i "s/SENDER_EMAIL = .*/SENDER_EMAIL = \"$SENDER_EMAIL\"/" "$SCRIPT_DIR/email_csv.py"
    sed -i "s/SENDER_PASSWORD = .*/SENDER_PASSWORD = \"$SENDER_PASSWORD\"/" "$SCRIPT_DIR/email_csv.py"
    sed -i "s/RECIPIENT_EMAIL = .*/RECIPIENT_EMAIL = \"$RECIPIENT_EMAIL\"/" "$SCRIPT_DIR/email_csv.py"
    
    print_success "Email configuration saved"
    EMAIL_CONFIGURED=true
else
    print_info "Email configuration skipped"
    EMAIL_CONFIGURED=false
fi

# Step 6: Test the logger
print_header "Step 6: Testing Logger"
print_info "Running test fetch..."
if python3 "$SCRIPT_DIR/wl_logger.py"; then
    print_success "Logger test successful!"
else
    print_error "Logger test failed. Check your API credentials."
    exit 1
fi

# Step 7: Set up cron jobs
print_header "Step 7: Setting Up Cron Jobs"

PYTHON_PATH=$(which python3)
FULL_LOGGER_PATH="$SCRIPT_DIR/wl_logger.py"
FULL_EMAIL_PATH="$SCRIPT_DIR/email_csv.py"

print_info "Select data logging interval:"
echo "  1) Every 5 minutes"
echo "  2) Every 10 minutes"
echo "  3) Every 30 minutes"
echo "  4) Every hour"
echo "  5) Every 6 hours"
echo "  6) Custom (enter cron expression)"
echo "  0) Skip cron setup"

read -p "Enter your choice (0-6): " CRON_CHOICE

LOGGER_CRON=""
case $CRON_CHOICE in
    1) LOGGER_CRON="*/5 * * * *" ;;
    2) LOGGER_CRON="*/10 * * * *" ;;
    3) LOGGER_CRON="*/30 * * * *" ;;
    4) LOGGER_CRON="0 * * * *" ;;
    5) LOGGER_CRON="0 */6 * * *" ;;
    6) read -p "Enter cron expression: " LOGGER_CRON ;;
    0) LOGGER_CRON="" ;;
esac

# Set up logging cron if selected
if [ ! -z "$LOGGER_CRON" ]; then
    # Remove existing cron job if it exists
    crontab -l 2>/dev/null | grep -v "$FULL_LOGGER_PATH" | crontab - 2>/dev/null || true
    
    # Add new cron job
    (crontab -l 2>/dev/null || true; echo "$LOGGER_CRON $PYTHON_PATH $FULL_LOGGER_PATH") | crontab -
    print_success "Logger cron job added: $LOGGER_CRON"
fi

# Set up email cron if configured
if [ "$EMAIL_CONFIGURED" = true ]; then
    echo
    print_info "Select email reporting interval:"
    echo "  1) Daily at 8 PM"
    echo "  2) Every morning at 7 AM"
    echo "  3) Weekly (Monday at 9 AM)"
    echo "  4) Twice daily (7 AM & 7 PM)"
    echo "  5) Custom (enter cron expression)"
    echo "  0) Skip email cron"
    
    read -p "Enter your choice (0-5): " EMAIL_CRON_CHOICE
    
    EMAIL_CRON=""
    case $EMAIL_CRON_CHOICE in
        1) EMAIL_CRON="0 20 * * *" ;;
        2) EMAIL_CRON="0 7 * * *" ;;
        3) EMAIL_CRON="0 9 * * 1" ;;
        4) EMAIL_CRON="0 7,19 * * *" ;;
        5) read -p "Enter cron expression: " EMAIL_CRON ;;
        0) EMAIL_CRON="" ;;
    esac
    
    if [ ! -z "$EMAIL_CRON" ]; then
        # Add email cron job
        (crontab -l 2>/dev/null || true; echo "$EMAIL_CRON $PYTHON_PATH $FULL_EMAIL_PATH") | crontab -
        print_success "Email cron job added: $EMAIL_CRON"
    fi
fi

# Step 8: Summary
print_header "Installation Complete!"
print_success "WeatherLink Data Logger is now installed and configured"

echo
print_info "Your current cron jobs:"
crontab -l 2>/dev/null | grep -E "(wl_logger|email_csv)" || print_info "No weatherlink cron jobs found"

echo
print_info "Log files will be saved to:"
echo "  - $SCRIPT_DIR/weather_data.csv (Excel-readable)"
echo "  - $SCRIPT_DIR/weather_data.json (JSON format)"

echo
print_info "Configuration files:"
echo "  - $SCRIPT_DIR/wl_logger.py (Data logger)"
echo "  - $SCRIPT_DIR/email_csv.py (Email sender)"

echo
print_info "Manual commands:"
echo "  Fetch data now:     python3 $FULL_LOGGER_PATH"
echo "  List stations:      python3 $FULL_LOGGER_PATH --list-stations"
echo "  Send email now:     python3 $FULL_EMAIL_PATH"
echo "  View cron jobs:     crontab -l"
echo "  Edit cron jobs:     crontab -e"

echo
print_success "Installation finished! Your weather logger is ready to run."