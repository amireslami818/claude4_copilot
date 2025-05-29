# Football Bot Continuous Operation System

## 🚀 Overview

The Football Bot Continuous Operation System provides 24/7 automated execution of the complete football betting data pipeline (Steps 1-6) at 60-second intervals. This system includes robust error handling, comprehensive monitoring, and service management capabilities.

## 📋 Features

### ✅ Core Features
- **Continuous Pipeline Execution**: Runs Steps 1-6 every 60 seconds
- **24/7 Operation**: Systemd service for persistent operation
- **Graceful Shutdown**: Handles SIGINT/SIGTERM signals properly
- **Error Recovery**: Automatic retry with exponential backoff
- **Comprehensive Logging**: Detailed logs with rotation
- **Performance Monitoring**: Real-time metrics and health checks
- **Resource Management**: Memory and CPU limits

### ✅ Monitoring & Alerts
- **Health Reports**: Comprehensive system status reports
- **Live Monitoring**: Real-time dashboard with system metrics
- **Alert System**: Automated alerts for critical issues
- **Log Analysis**: Intelligent parsing of pipeline logs
- **Resource Tracking**: CPU, memory, and disk usage monitoring

## 🗂️ File Structure

```
Football_bot/
├── continuous_orchestrator.py    # Main continuous pipeline orchestrator
├── football-bot.service          # Systemd service configuration
├── deploy_service.sh             # Service deployment script
├── health_monitor.py             # Health monitoring and alerting
├── logs/                         # Log directory (auto-created)
│   ├── continuous_orchestrator_YYYYMMDD.log
│   └── step6_matches.log
└── [existing step files...]
```

## 🛠️ Installation & Setup

### Prerequisites

1. **Python 3.8+** with required packages:
   ```bash
   pip3 install aiohttp asyncio requests beautifulsoup4 lxml psutil
   ```

2. **Root access** for systemd service installation

3. **API credentials** configured in Step 1

### Quick Installation

1. **Make deployment script executable:**
   ```bash
   chmod +x deploy_service.sh
   ```

2. **Install and start the service:**
   ```bash
   sudo bash deploy_service.sh install
   sudo bash deploy_service.sh start
   ```

3. **Verify installation:**
   ```bash
   sudo bash deploy_service.sh status
   ```

## 🎛️ Service Management

### Service Commands

```bash
# Install service (one-time setup)
sudo bash deploy_service.sh install

# Start the service
sudo bash deploy_service.sh start

# Stop the service
sudo bash deploy_service.sh stop

# Restart the service
sudo bash deploy_service.sh restart

# Check service status
sudo bash deploy_service.sh status

# View recent logs
sudo bash deploy_service.sh logs

# Follow logs in real-time
sudo bash deploy_service.sh follow

# Uninstall service
sudo bash deploy_service.sh uninstall
```

### Manual Service Control

```bash
# Using systemctl directly
sudo systemctl start football-bot
sudo systemctl stop football-bot
sudo systemctl restart football-bot
sudo systemctl status football-bot

# Enable/disable auto-start
sudo systemctl enable football-bot
sudo systemctl disable football-bot

# View logs
journalctl -u football-bot -f
journalctl -u football-bot -n 100
```

## 📊 Monitoring & Health Checks

### Health Monitor Commands

```bash
# Generate comprehensive health report
python3 health_monitor.py report

# Check for alerts
python3 health_monitor.py alerts

# Live monitoring dashboard
python3 health_monitor.py monitor

# View recent logs
python3 health_monitor.py logs --lines 100
```

### Sample Health Report

```
🏥 Football Bot Health Report
==================================================
📅 Generated: 2024-01-15 14:30:22

🔧 Service Status
--------------------
✅ Service is ACTIVE
⏰ Started: Mon 2024-01-15 10:00:00 UTC
🔄 Restarts: 0

📊 Pipeline Performance
-------------------------
🔄 Total Cycles: 245
✅ Successful: 242
❌ Failed: 3
📈 Success Rate: 98.8%
🎯 Matches Processed: 27,195
🕐 Last Activity: 2024-01-15 14:29:45

📁 Data Files Status
--------------------
🟢 step1.json: 39.5MB (0.3m ago)
🟢 step2/step2.json: 6.5MB (0.3m ago)
🟢 step3/step3.json: 13.3MB (0.3m ago)
🟢 step4/step4.json: 2.1MB (0.3m ago)
🟢 step5/step5.json: 2.1MB (0.3m ago)
🟢 step6_matches.log: 1.2MB (0.3m ago)

💻 System Resources
-------------------
🖥️  CPU Usage: 12.3%
💾 Memory Usage: 45.2% (3.6GB/8.0GB)
💿 Disk Usage: 23.4% (45.2GB/193.5GB)
```

## 🔄 Pipeline Operation

### Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                  CONTINUOUS PIPELINE CYCLE                     │
├─────────────────────────────────────────────────────────────────┤
│ Step 1: Fetch Data (5-10s) → Step 2: Process (2-3s) →         │
│ Step 3: Summarize (1-2s) → Step 4: Extract (1-2s) →           │
│ Step 5: Convert (1-2s) → Step 6: Display (1-2s)               │
├─────────────────────────────────────────────────────────────────┤
│ Total Cycle Time: ~12-20 seconds                               │
│ Wait Time: 40-48 seconds (to maintain 60s intervals)           │
│ Data Processed: ~111 matches per cycle                         │
└─────────────────────────────────────────────────────────────────┘
```

### Performance Metrics

- **Cycle Frequency**: Every 60 seconds
- **Daily Cycles**: ~1,440 cycles per day
- **Matches Per Day**: ~159,840 matches processed
- **Data Generation**: ~86 GB per day (with full history)
- **Success Rate**: Typically >95%

## 🚨 Error Handling

### Automatic Recovery

1. **Step Failures**: Individual step failures stop the current cycle, log errors, and retry in the next cycle
2. **Consecutive Errors**: After 5 consecutive failures, implements 5-minute backoff
3. **Service Crashes**: Systemd automatically restarts the service after 30 seconds
4. **Network Issues**: Built-in timeout and retry mechanisms

### Alert Conditions

- Service not running
- Success rate below 50%
- More than 10 failed cycles
- No activity for >10 minutes
- High resource usage (>90% CPU/Memory/Disk)

## 📁 Log Management

### Log Locations

```bash
# Service logs (systemd)
journalctl -u football-bot

# Application logs
/root/CascadeProjects/Football_bot/logs/continuous_orchestrator_YYYYMMDD.log

# Match display logs
/root/CascadeProjects/Football_bot/step6_matches.log
```

### Log Rotation

- **Application logs**: Daily rotation (one file per day)
- **System logs**: Handled by systemd journal
- **Match logs**: Appended continuously (manual cleanup required)

## 🔧 Configuration

### Service Configuration

Edit `football-bot.service` to modify:

- **Resource Limits**: `MemoryMax`, `CPUQuota`
- **User/Group**: Change from `root` if needed
- **Environment Variables**: Add custom settings
- **Restart Policy**: Modify restart behavior

### Orchestrator Configuration

Edit `continuous_orchestrator.py` to modify:

- **Cycle Interval**: Change from 60 seconds
- **Error Thresholds**: Adjust backoff triggers
- **Logging Levels**: Modify verbosity
- **Step Configuration**: Add/remove pipeline steps

## 🚀 Deployment Options

### Option 1: Local Systemd Service (Current)
- **Pros**: Simple setup, local control, auto-restart
- **Cons**: Requires machine to stay on
- **Best For**: Development, testing, dedicated servers

### Option 2: Cloud Deployment
- **Platforms**: AWS ECS, Google Cloud Run, Azure Container Instances
- **Pros**: True 24/7 operation, scalability, managed infrastructure
- **Cons**: Cloud costs, setup complexity
- **Best For**: Production, high availability requirements

### Option 3: VPS Deployment
- **Providers**: DigitalOcean, Linode, Vultr
- **Pros**: Cost-effective, full control, 24/7 operation
- **Cons**: Server management overhead
- **Best For**: Budget-conscious production deployments

## 🛡️ Security Considerations

### Current Security Measures

- **No New Privileges**: Service cannot escalate privileges
- **Private Temp**: Isolated temporary directories
- **Protected System**: Read-only system directories
- **Resource Limits**: Prevents resource exhaustion

### Recommended Enhancements

1. **Dedicated User**: Run as non-root user
2. **API Key Security**: Use environment variables or secrets management
3. **Network Security**: Firewall configuration
4. **Log Security**: Secure log file permissions

## 📈 Scaling Considerations

### Current Limitations

- **Single Instance**: One pipeline instance per machine
- **Sequential Processing**: Steps run sequentially
- **Local Storage**: Data stored locally only

### Scaling Options

1. **Horizontal Scaling**: Multiple instances across machines
2. **Parallel Processing**: Concurrent step execution
3. **Distributed Storage**: Shared data storage systems
4. **Load Balancing**: Distribute API calls across instances

## 🆘 Troubleshooting

### Common Issues

1. **Service Won't Start**
   ```bash
   # Check service status
   sudo systemctl status football-bot
   
   # Check logs for errors
   journalctl -u football-bot -n 50
   
   # Verify permissions
   chmod +x continuous_orchestrator.py
   ```

2. **High Error Rate**
   ```bash
   # Check health report
   python3 health_monitor.py report
   
   # Check recent alerts
   python3 health_monitor.py alerts
   
   # Monitor live
   python3 health_monitor.py monitor
   ```

3. **API Issues**
   ```bash
   # Test API connectivity
   python3 step1.py
   
   # Check API credentials
   # Verify rate limits
   ```

4. **Resource Issues**
   ```bash
   # Check system resources
   python3 health_monitor.py report
   
   # Monitor disk space
   df -h
   
   # Check memory usage
   free -h
   ```

### Support Commands

```bash
# Full system check
python3 health_monitor.py report

# Emergency stop
sudo systemctl stop football-bot

# Service reset
sudo systemctl restart football-bot

# Log cleanup
sudo journalctl --vacuum-time=7d
```

## 📞 Support

For issues or questions:

1. **Check Health Report**: `python3 health_monitor.py report`
2. **Review Logs**: `journalctl -u football-bot -f`
3. **Check Service Status**: `sudo systemctl status football-bot`
4. **Monitor Resources**: `python3 health_monitor.py monitor`

---

**Football Bot Continuous Operation System v1.0.0**  
*Automated 24/7 Football Betting Data Pipeline*
