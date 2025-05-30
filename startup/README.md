# Football Bot Startup System

## Overview

Centralized startup and management system for the Football Bot Pipeline. This replaces all previous systemd and cron-based approaches with a simple shell-based solution.

## Architecture

The startup system uses:
- **Direct process execution** (no systemd/cron dependencies)
- **PID-based process management** for clean start/stop operations
- **Background execution** with proper logging
- **Graceful shutdown** handling with SIGTERM/SIGKILL fallback

## Usage

### Basic Commands

```bash
# Start the pipeline
./startup/start.sh start

# Check status
./startup/start.sh status

# View live logs
./startup/start.sh logs

# Stop the pipeline
./startup/start.sh stop

# Restart the pipeline
./startup/start.sh restart
```

### Quick Start

```bash
cd /root/CascadeProjects/Football_bot
./startup/start.sh start
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
