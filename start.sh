#!/bin/bash
##############################################################################
#                        FOOTBALL BOT STARTUP (LEGACY)                      #
##############################################################################
# 
# DEPRECATED: This file is kept for compatibility
# Please use: ./startup/start.sh instead
#
##############################################################################

echo "⚠️  DEPRECATED: This start.sh is no longer used"
echo ""
echo "Please use the new centralized startup system:"
echo "  ./startup/start.sh start     # Start pipeline"
echo "  ./startup/start.sh status    # Check status"
echo "  ./startup/start.sh stop      # Stop pipeline"
echo "  ./startup/start.sh logs      # View logs"
echo ""
echo "Redirecting to new startup system..."
echo ""

# Redirect to new startup system
exec ./startup/start.sh "$@"
