# Football Bot Startup System

## Overview

Centralized startup and management system for the Football Bot Pipeline. This system uses tmux for better process control, monitoring, and logging.

## Architecture

The startup system uses:
- **tmux sessions** for process isolation and monitoring
- **Multi-pane display** for real-time monitoring of different components
- **Direct process execution** (no systemd/cron dependencies)
- **PID-based process management** for clean start/stop operations
- **Background execution** with proper logging
- **Graceful shutdown** handling with SIGTERM/SIGKILL fallback

## tmux Session Layout

The pipeline runs in a tmux session named "football-pipeline" with three panes:
1. Main pane (left): Orchestrator process
2. Top-right pane: Live log tail
3. Bottom-right pane: Process monitoring

### Interacting with tmux

- `tmux attach -t football-pipeline` to connect to the session
- `Ctrl+B` then arrow keys to switch between panes
- `Ctrl+B` then `d` to detach (pipeline keeps running)
- `Ctrl+C` in a pane to stop that component

## Usage

### Basic Commands

```bash
# Start the pipeline in tmux
./startup/manage_pipeline.sh start

# Check pipeline status and recent logs
./startup/manage_pipeline.sh status

# View detailed logs
./startup/manage_pipeline.sh logs

# Stop the pipeline gracefully
./startup/manage_pipeline.sh stop

# Attach to running pipeline session
tmux attach -t football-pipeline
```

### Quick Start

```bash
cd /root/CascadeProjects/Football_bot
./startup/manage_pipeline.sh start
```

The pipeline will:
1. Start running in the background
2. Log all output to `logs/pipeline.log`
3. Use smart timing (60s intervals or immediate if >2min)
4. Continue running until manually stopped

## Process Management

### How it Works

1. **Start**: Launches `continuous_orchestrator.py` in background with `nohup`
2. **PID Tracking**: Saves process ID to `startup/football-bot.pid`
3. **Monitoring**: Uses PID to check if process is running
4. **Stop**: Sends SIGTERM for graceful shutdown, SIGKILL if needed
5. **Cleanup**: Removes PID file after shutdown

### Log Management

- **Main Log**: `logs/pipeline.log` (all pipeline output)
- **Log Rotation**: Handled automatically by the pipeline
- **Live Viewing**: Use `./startup/start.sh logs` to follow logs in real-time

## Smart Timing Logic

The pipeline uses intelligent timing:
- **If cycle takes ≥ 2 minutes**: Next cycle starts immediately
- **If cycle takes < 2 minutes**: Waits to maintain 60-second intervals

This ensures optimal data freshness without resource overload.

## File Structure

```
startup/
├── start.sh              # Main startup script
├── README.md             # This documentation
└── football-bot.pid      # Process ID file (created when running)

logs/
└── pipeline.log          # Main pipeline log file
```

## Migration from systemd

If you previously used systemd:

```bash
# Stop and disable old systemd service
sudo systemctl stop football-bot.service
sudo systemctl disable football-bot.service

# Use new startup system
./startup/start.sh start
```

## Troubleshooting

### Pipeline Won't Start
1. Check if already running: `./startup/start.sh status`
2. Check logs: `./startup/start.sh logs`
3. Verify Python script exists: `ls -la continuous_orchestrator.py`

### Pipeline Stops Unexpectedly
1. Check recent logs: `tail -20 logs/pipeline.log`
2. Look for error messages or memory issues
3. Restart: `./startup/start.sh restart`

### Can't Stop Pipeline
1. Check PID file: `cat startup/football-bot.pid`
2. Manual kill: `kill -9 $(cat startup/football-bot.pid)`
3. Clean up: `rm startup/football-bot.pid`

## Integration

The startup system is designed to work with:
- The existing `continuous_orchestrator.py` pipeline
- All 6 pipeline steps (step1-step6)
- Alert system integration
- Smart timing logic

No code changes required in the main pipeline - it's a pure management layer.
