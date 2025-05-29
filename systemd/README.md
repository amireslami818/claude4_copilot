# Football Bot Systemd Management
================================

This directory contains all systemd service management files for the Football Bot continuous pipeline.

## 📁 Files in this directory:

### `football-bot.service`
- **Purpose:** systemd service definition file
- **Install Location:** `/etc/systemd/system/football-bot.service`
- **Contains:** Service configuration, resource limits, security settings

### `deploy_service.sh`
- **Purpose:** Automated service deployment script
- **Usage:** `sudo ./deploy_service.sh [action]`
- **Actions:** install, start, stop, restart, status, logs, uninstall

### `aliases.sh`
- **Purpose:** Quick command aliases for service management
- **Usage:** `source systemd/aliases.sh`
- **Provides:** fb-start, fb-stop, fb-restart, fb-status, fb-logs, fb-follow

## 🚀 Quick Start:

1. **Install service:**
   ```bash
   sudo ./systemd/deploy_service.sh install
   ```

2. **Load aliases:**
   ```bash
   source systemd/aliases.sh
   ```

3. **Use quick commands:**
   ```bash
   fb-start    # Start service
   fb-stop     # Stop service
   fb-status   # Check status
   fb-logs     # View logs
   ```

## 📊 Service Status:

Check if service is running:
```bash
fb-status
```

Follow live logs:
```bash
fb-follow
```

## 🔧 Maintenance:

All systemd-related operations should be performed from this directory to keep the project organized.
