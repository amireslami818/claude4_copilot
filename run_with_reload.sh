#!/usr/bin/env bash
# ----------------------------------------------------------------
# run_with_reload.sh
#
# - Watches Python files for changes in the Football Bot directory.
# - Whenever any .py file is modified, it:
#     a) kills the current running pipeline (if it's still up),
#     b) restarts the pipeline fresh.
#
# Usage: ./run_with_reload.sh
#
# Watches: step1.py, step2/, step3/, step4/, step5/, step6/, step7.py, 
#         continuous_orchestrator.py, and alerts/ directory
# ----------------------------------------------------------------

WATCH_DIR="."              # Watch current directory (Football_bot)
MAIN_SCRIPT="continuous_orchestrator.py"
PID=""

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 Football Bot Auto-Reload Watcher${NC}"
echo -e "${BLUE}====================================${NC}"
echo -e "Watching: ${YELLOW}$WATCH_DIR${NC} for .py file changes"
echo -e "Main script: ${YELLOW}$MAIN_SCRIPT${NC}"
echo ""

# Start the pipeline once, in the background:
start_pipeline() {
  echo -e "${GREEN}🚀 Starting pipeline at $(date)${NC}"
  python3 $MAIN_SCRIPT &
  PID=$!   # record its process ID
  echo -e "   ${GREEN}Pipeline PID = $PID${NC}"
  echo ""
}

# Stop the pipeline if it's running:
stop_pipeline() {
  if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
    echo -e "${RED}🛑 Stopping pipeline (PID $PID) at $(date)${NC}"
    kill "$PID"
    wait "$PID" 2>/dev/null
    echo -e "   ${RED}Pipeline stopped${NC}"
  fi
}

# Cleanup on script exit
cleanup() {
  echo -e "\n${YELLOW}🔄 Auto-reload watcher shutting down...${NC}"
  stop_pipeline
  exit 0
}

# Handle Ctrl+C gracefully
trap cleanup SIGINT SIGTERM

# Initially, launch the pipeline:
start_pipeline

# Watch for ANY modification (create/delete/modify) on .py files
echo -e "${BLUE}👀 Watching for .py file changes... (Press Ctrl+C to stop)${NC}"
echo -e "${BLUE}=====================================================${NC}"

inotifywait -m -r -e modify,create,delete,move "$WATCH_DIR" --format '%w%f %e' \
  --include '\.py$' \
  --exclude '__pycache__|\.pyc$' |
while read CHANGED_FILE EVENT; do
  # Skip __pycache__ and .pyc files
  if [[ "$CHANGED_FILE" =~ __pycache__|\.pyc$ ]]; then
    continue
  fi
  
  echo -e "${YELLOW}🔔 File change detected: ${NC}$CHANGED_FILE ${YELLOW}($EVENT)${NC}"
  echo -e "${YELLOW}   Restarting pipeline...${NC}"
  stop_pipeline
  sleep 1  # Brief pause to ensure clean shutdown
  start_pipeline
done
