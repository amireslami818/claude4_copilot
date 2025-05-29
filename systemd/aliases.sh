#!/bin/bash
#
# Football Bot Service Control Scripts
# ===================================
# Quick access scripts for managing the Football Bot systemd service
#

# Service management shortcuts
alias fb-start='sudo systemctl start football-bot'
alias fb-stop='sudo systemctl stop football-bot'  
alias fb-restart='sudo systemctl restart football-bot'
alias fb-status='sudo systemctl status football-bot --no-pager'
alias fb-logs='sudo journalctl -u football-bot -n 20 --no-pager'
alias fb-follow='sudo journalctl -u football-bot -f'

echo "Football Bot Service Control Aliases Loaded!"
echo "============================================="
echo "Available commands:"
echo "  fb-start    - Start the service"
echo "  fb-stop     - Stop the service"
echo "  fb-restart  - Restart the service"
echo "  fb-status   - Show service status"
echo "  fb-logs     - Show recent logs"
echo "  fb-follow   - Follow logs in real-time"
echo ""
echo "Usage: source systemd/aliases.sh"
