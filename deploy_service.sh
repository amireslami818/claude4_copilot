#!/bin/bash
"""
Football Bot Deployment Script
=============================

Deploys the Football Bot continuous pipeline as a systemd service
for 24/7 operation with automatic startup on boot.

Usage: sudo bash deploy_service.sh [action]
Actions: install, start, stop, restart, status, logs, uninstall
"""

set -e

PROJECT_DIR="/root/CascadeProjects/Football_bot"
SERVICE_NAME="football-bot"
SERVICE_FILE="${PROJECT_DIR}/${SERVICE_NAME}.service"
SYSTEMD_DIR="/etc/systemd/system"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Install Python dependencies
install_dependencies() {
    print_info "Installing Python dependencies..."
    
    # Ensure pip is available
    if ! command -v pip3 &> /dev/null; then
        print_info "Installing pip3..."
        apt-get update
        apt-get install -y python3-pip
    fi
    
    # Install required packages
    pip3 install aiohttp asyncio requests beautifulsoup4 lxml
    
    print_success "Dependencies installed"
}

# Install the service
install_service() {
    print_info "Installing Football Bot service..."
    
    # Check if project directory exists
    if [[ ! -d "$PROJECT_DIR" ]]; then
        print_error "Project directory not found: $PROJECT_DIR"
        exit 1
    fi
    
    # Check if service file exists
    if [[ ! -f "$SERVICE_FILE" ]]; then
        print_error "Service file not found: $SERVICE_FILE"
        exit 1
    fi
    
    # Install dependencies
    install_dependencies
    
    # Make orchestrator executable
    chmod +x "${PROJECT_DIR}/continuous_orchestrator.py"
    
    # Copy service file to systemd directory
    cp "$SERVICE_FILE" "${SYSTEMD_DIR}/${SERVICE_NAME}.service"
    
    # Reload systemd daemon
    systemctl daemon-reload
    
    # Enable service to start on boot
    systemctl enable "$SERVICE_NAME"
    
    print_success "Service installed and enabled for auto-start"
}

# Start the service
start_service() {
    print_info "Starting Football Bot service..."
    systemctl start "$SERVICE_NAME"
    print_success "Service started"
    show_status
}

# Stop the service
stop_service() {
    print_info "Stopping Football Bot service..."
    systemctl stop "$SERVICE_NAME"
    print_success "Service stopped"
}

# Restart the service
restart_service() {
    print_info "Restarting Football Bot service..."
    systemctl restart "$SERVICE_NAME"
    print_success "Service restarted"
    show_status
}

# Show service status
show_status() {
    print_info "Service status:"
    systemctl status "$SERVICE_NAME" --no-pager
}

# Show service logs
show_logs() {
    print_info "Service logs (last 50 lines):"
    journalctl -u "$SERVICE_NAME" -n 50 --no-pager
    
    print_info "To follow logs in real-time, use:"
    echo "  journalctl -u $SERVICE_NAME -f"
}

# Follow logs in real-time
follow_logs() {
    print_info "Following logs in real-time (Ctrl+C to stop):"
    journalctl -u "$SERVICE_NAME" -f
}

# Uninstall the service
uninstall_service() {
    print_warning "Uninstalling Football Bot service..."
    
    # Stop service if running
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_info "Stopping service..."
        systemctl stop "$SERVICE_NAME"
    fi
    
    # Disable service
    if systemctl is-enabled --quiet "$SERVICE_NAME"; then
        print_info "Disabling service..."
        systemctl disable "$SERVICE_NAME"
    fi
    
    # Remove service file
    if [[ -f "${SYSTEMD_DIR}/${SERVICE_NAME}.service" ]]; then
        rm "${SYSTEMD_DIR}/${SERVICE_NAME}.service"
        print_info "Service file removed"
    fi
    
    # Reload systemd daemon
    systemctl daemon-reload
    
    print_success "Service uninstalled"
}

# Show usage information
show_usage() {
    echo "Football Bot Deployment Script"
    echo "============================="
    echo ""
    echo "Usage: sudo bash deploy_service.sh [action]"
    echo ""
    echo "Actions:"
    echo "  install   - Install and enable the service"
    echo "  start     - Start the service"
    echo "  stop      - Stop the service"
    echo "  restart   - Restart the service"
    echo "  status    - Show service status"
    echo "  logs      - Show recent logs"
    echo "  follow    - Follow logs in real-time"
    echo "  uninstall - Uninstall the service"
    echo ""
    echo "Examples:"
    echo "  sudo bash deploy_service.sh install"
    echo "  sudo bash deploy_service.sh start"
    echo "  sudo bash deploy_service.sh logs"
    echo "  sudo bash deploy_service.sh follow"
}

# Main execution
main() {
    local action="${1:-help}"
    
    case "$action" in
        "install")
            check_root
            install_service
            ;;
        "start")
            check_root
            start_service
            ;;
        "stop")
            check_root
            stop_service
            ;;
        "restart")
            check_root
            restart_service
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "follow")
            follow_logs
            ;;
        "uninstall")
            check_root
            uninstall_service
            ;;
        "help"|*)
            show_usage
            ;;
    esac
}

# Run the script
main "$@"
