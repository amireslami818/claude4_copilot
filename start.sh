#!/bin/bash
#
# Quick Start Script for Football Bot
# ==================================
# One-command service management
#

cd "$(dirname "$0")"

# Source aliases
source systemd/aliases.sh

echo ""
echo "🚀 Football Bot Quick Start"
echo "=========================="
echo ""
echo "Service Management:"
echo "  fb-start     # Start the service"
echo "  fb-stop      # Stop the service"  
echo "  fb-restart   # Restart the service"
echo "  fb-status    # Check service status"
echo "  fb-logs      # View recent logs"
echo "  fb-follow    # Follow live logs"
echo ""
echo "Full Deployment:"
echo "  sudo ./systemd/deploy_service.sh install"
echo ""

# Show current status
echo "Current Status:"
echo "==============="
if systemctl is-active --quiet football-bot; then
    echo "✅ Service is RUNNING"
    echo ""
    fb-status
else
    echo "❌ Service is STOPPED"
    echo ""
    echo "To start: fb-start"
fi
