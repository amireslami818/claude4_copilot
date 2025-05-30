#!/bin/bash
##############################################################################
#                           FOOTBALL BOT STARTUP                            #
##############################################################################
#
# Centralized startup system for Football Bot Pipeline
# 
# Author: GitHub Copilot
# Version: 2.0.0
# Date: May 30, 2025
#
##############################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project paths
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ORCHESTRATOR_SCRIPT="$PROJECT_DIR/continuous_orchestrator.py"
LOG_DIR="$PROJECT_DIR/logs"
PID_FILE="$PROJECT_DIR/startup/football-bot.pid"

##############################################################################
# UTILITY FUNCTIONS
##############################################################################

print_header() {
    echo -e "\n${CYAN}══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}                        FOOTBALL BOT PIPELINE                     ${NC}"
    echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

##############################################################################
# PIPELINE MANAGEMENT FUNCTIONS
##############################################################################

start_pipeline() {
    print_header
    print_info "Starting Football Bot Pipeline..."
    
    # Check if already running
    if is_running; then
        print_warning "Pipeline is already running (PID: $(cat $PID_FILE))"
        return 1
    fi
    
    # Create log directory
    mkdir -p "$LOG_DIR"
    
    # Start the pipeline in background
    cd "$PROJECT_DIR"
    nohup python3 "$ORCHESTRATOR_SCRIPT" > "$LOG_DIR/pipeline.log" 2>&1 &
    local pid=$!
    
    # Save PID
    echo $pid > "$PID_FILE"
    
    # Wait a moment and verify it started
    sleep 2
    if kill -0 $pid 2>/dev/null; then
        print_success "Pipeline started successfully!"
        print_info "PID: $pid"
        print_info "Log file: $LOG_DIR/pipeline.log"
        print_info "Use './startup/start.sh stop' to stop the pipeline"
        return 0
    else
        print_error "Failed to start pipeline"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_pipeline() {
    print_header
    print_info "Stopping Football Bot Pipeline..."
    
    if ! is_running; then
        print_warning "Pipeline is not running"
        return 1
    fi
    
    local pid=$(cat "$PID_FILE")
    print_info "Sending SIGTERM to process $pid..."
    
    # Send SIGTERM for graceful shutdown
    kill -TERM $pid 2>/dev/null
    
    # Wait up to 30 seconds for graceful shutdown
    local count=0
    while kill -0 $pid 2>/dev/null && [ $count -lt 30 ]; do
        sleep 1
        count=$((count + 1))
    done
    
    # Force kill if still running
    if kill -0 $pid 2>/dev/null; then
        print_warning "Graceful shutdown failed, forcing termination..."
        kill -KILL $pid 2>/dev/null
        sleep 1
    fi
    
    # Clean up PID file
    rm -f "$PID_FILE"
    
    if ! kill -0 $pid 2>/dev/null; then
        print_success "Pipeline stopped successfully!"
        return 0
    else
        print_error "Failed to stop pipeline"
        return 1
    fi
}

restart_pipeline() {
    print_header
    print_info "Restarting Football Bot Pipeline..."
    
    stop_pipeline
    sleep 2
    start_pipeline
}

status_pipeline() {
    print_header
    
    if is_running; then
        local pid=$(cat "$PID_FILE")
        print_success "Pipeline is RUNNING"
        print_info "PID: $pid"
        print_info "Started: $(ps -o lstart= -p $pid 2>/dev/null || echo 'Unknown')"
        
        # Show memory usage
        local mem=$(ps -o rss= -p $pid 2>/dev/null | tr -d ' ')
        if [ -n "$mem" ]; then
            local mem_mb=$((mem / 1024))
            print_info "Memory: ${mem_mb}MB"
        fi
        
        # Show log tail
        if [ -f "$LOG_DIR/pipeline.log" ]; then
            echo -e "\n${CYAN}Recent Log Entries:${NC}"
            tail -5 "$LOG_DIR/pipeline.log"
        fi
    else
        print_warning "Pipeline is NOT RUNNING"
        
        # Check for recent crash
        if [ -f "$LOG_DIR/pipeline.log" ]; then
            echo -e "\n${CYAN}Last Log Entries:${NC}"
            tail -10 "$LOG_DIR/pipeline.log"
        fi
    fi
}

is_running() {
    [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

show_logs() {
    if [ -f "$LOG_DIR/pipeline.log" ]; then
        print_info "Showing live logs (Ctrl+C to exit)..."
        tail -f "$LOG_DIR/pipeline.log"
    else
        print_error "Log file not found: $LOG_DIR/pipeline.log"
    fi
}

##############################################################################
# MAIN SCRIPT LOGIC
##############################################################################

show_usage() {
    print_header
    echo -e "${PURPLE}Football Bot Pipeline Management${NC}"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start     Start the pipeline"
    echo "  stop      Stop the pipeline"
    echo "  restart   Restart the pipeline"
    echo "  status    Show pipeline status"
    echo "  logs      Show live logs"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start     # Start the pipeline in background"
    echo "  $0 status    # Check if pipeline is running"
    echo "  $0 logs      # Follow live logs"
    echo ""
}

main() {
    case "${1:-help}" in
        start)
            start_pipeline
            ;;
        stop)
            stop_pipeline
            ;;
        restart)
            restart_pipeline
            ;;
        status)
            status_pipeline
            ;;
        logs)
            show_logs
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown command: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
