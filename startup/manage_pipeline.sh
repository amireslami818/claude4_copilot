#!/bin/bash

# Pipeline management script using tmux
# Usage: ./manage_pipeline.sh [start|stop|status|logs]

SESSION_NAME="football-pipeline"
PIPELINE_DIR="/root/CascadeProjects/Football_bot"
ORCHESTRATOR="continuous_orchestrator.py"
LOG_DIR="$PIPELINE_DIR/logs"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

start_pipeline() {
    # Check if session already exists
    if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        echo "Pipeline session already exists!"
        echo "Use './manage_pipeline.sh status' to check status"
        echo "Use './manage_pipeline.sh stop' to stop existing session"
        return 1
    fi

    # Create new tmux session
    tmux new-session -d -s "$SESSION_NAME" -c "$PIPELINE_DIR"
    
    # Split window into panes for different components
    tmux split-window -h -t "$SESSION_NAME" -c "$PIPELINE_DIR"
    tmux split-window -v -t "$SESSION_NAME:0.1" -c "$PIPELINE_DIR"
    
    # Pane 0: Orchestrator
    tmux send-keys -t "$SESSION_NAME:0.0" "python3 $ORCHESTRATOR 2>&1 | tee $LOG_DIR/orchestrator_$(date +%Y%m%d_%H%M%S).log" C-m
    
    # Pane 1: Pipeline logs (live tail)
    tmux send-keys -t "$SESSION_NAME:0.1" "tail -f $LOG_DIR/pipeline.log" C-m
    
    # Pane 2: System monitoring
    tmux send-keys -t "$SESSION_NAME:0.2" "watch -n 5 'ps aux | grep -E \"python|orchestrator\" | grep -v grep'" C-m

    echo "Pipeline started in tmux session '$SESSION_NAME'"
    echo "Use './manage_pipeline.sh status' to check status"
    echo "To attach to session: tmux attach -t $SESSION_NAME"
}

stop_pipeline() {
    if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        echo "Pipeline session not found!"
        return 1
    fi

    # Send SIGTERM to all Python processes in the session
    tmux list-panes -a -F "#{pane_pid}" -t "$SESSION_NAME" | while read pid; do
        pkill -TERM -P "$pid" python 2>/dev/null
    done

    # Kill the tmux session
    tmux kill-session -t "$SESSION_NAME"
    echo "Pipeline stopped"
}

show_status() {
    if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        echo "Pipeline is not running"
        return 1
    fi

    echo "Pipeline is running in tmux session '$SESSION_NAME'"
    echo "Recent processes:"
    ps aux | grep -E "python|orchestrator" | grep -v grep

    echo -e "\nRecent log entries:"
    tail -n 10 "$LOG_DIR/pipeline.log"
}

show_logs() {
    if [ ! -d "$LOG_DIR" ]; then
        echo "Log directory not found!"
        return 1
    fi

    echo "Available logs in $LOG_DIR:"
    ls -lh "$LOG_DIR"
    echo -e "\nMost recent entries from pipeline.log:"
    tail -n 20 "$LOG_DIR/pipeline.log"
}

case "$1" in
    start)
        start_pipeline
        ;;
    stop)
        stop_pipeline
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "Usage: $0 [start|stop|status|logs]"
        exit 1
        ;;
esac
