# Football Bot Pipeline - Startup System Migration

## ⚠️ IMPORTANT: Startup System Updated

**The Football Bot Pipeline now uses a simplified startup system. All systemd and cron references in documentation are deprecated.**

## Current Startup Method

Use the centralized startup system:

```bash
cd /root/CascadeProjects/Football_bot

# Start the pipeline
./startup/start.sh start

# Check status  
./startup/start.sh status

# View logs
./startup/start.sh logs

# Stop pipeline
./startup/start.sh stop
```

## Documentation Status

📚 **Current Documentation Files** (may contain outdated systemd/cron references):
- `PIPELINE_ANALYSIS.md` - Contains systemd references (ignore deployment sections)
- `CONTINUOUS_OPERATION_README.md` - May reference systemd 
- `DEPLOYMENT_SUCCESS_REPORT.md` - May reference systemd

🎯 **Authoritative Startup Documentation**:
- `startup/README.md` - **USE THIS** for all startup instructions
- `startup/start.sh` - The actual startup script

## Quick Migration

If you were using systemd before:

```bash
# Stop old systemd service (if running)
sudo systemctl stop football-bot.service
sudo systemctl disable football-bot.service

# Use new startup system
./startup/start.sh start
```

**For all pipeline operations, refer to `startup/README.md` - it contains the current and accurate instructions.**
