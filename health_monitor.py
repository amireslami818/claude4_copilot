#!/usr/bin/env python3
"""
Football Bot Health Monitor
==========================

Monitors the health and performance of the continuous pipeline operation.
Provides real-time metrics, alerts, and system health checks.

Author: GitHub Copilot
Version: 1.0.0
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import psutil

PROJECT_ROOT = Path(__file__).parent

class HealthMonitor:
    """Health monitoring and alerting system for Football Bot"""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.service_name = "football-bot"
        self.log_dir = self.project_root / "logs"
        
    def get_service_status(self):
        """Check systemd service status"""
        try:
            result = subprocess.run(
                ["systemctl", "is-active", self.service_name],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() == "active"
        except Exception:
            return False
    
    def get_service_info(self):
        """Get detailed service information"""
        try:
            # Service status
            status_result = subprocess.run(
                ["systemctl", "status", self.service_name, "--no-pager"],
                capture_output=True, text=True, timeout=10
            )
            
            # Service properties
            props_result = subprocess.run(
                ["systemctl", "show", self.service_name],
                capture_output=True, text=True, timeout=10
            )
            
            props = {}
            for line in props_result.stdout.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    props[key] = value
            
            return {
                "active": self.get_service_status(),
                "status_output": status_result.stdout,
                "uptime": props.get("ActiveEnterTimestamp", ""),
                "restarts": props.get("NRestarts", "0"),
                "memory_usage": props.get("MemoryCurrent", "0"),
                "cpu_usage": props.get("CPUUsageNSec", "0")
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_recent_logs(self, lines=50):
        """Get recent service logs"""
        try:
            result = subprocess.run(
                ["journalctl", "-u", self.service_name, "-n", str(lines), "--no-pager"],
                capture_output=True, text=True, timeout=10
            )
            return result.stdout
        except Exception as e:
            return f"Error getting logs: {str(e)}"
    
    def analyze_log_file(self):
        """Analyze the latest orchestrator log file"""
        log_files = list(self.log_dir.glob("continuous_orchestrator_*.log"))
        if not log_files:
            return {"error": "No log files found"}
        
        # Get the most recent log file
        latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(latest_log, 'r') as f:
                lines = f.readlines()
            
            # Analyze log content
            analysis = {
                "log_file": str(latest_log),
                "total_lines": len(lines),
                "cycles_completed": 0,
                "successful_cycles": 0,
                "failed_cycles": 0,
                "errors": [],
                "last_activity": None,
                "matches_processed": 0
            }
            
            # Parse log lines
            for line in lines:
                if "Pipeline Cycle #" in line:
                    analysis["cycles_completed"] += 1
                    if "completed successfully" in line:
                        analysis["successful_cycles"] += 1
                    elif "failed" in line:
                        analysis["failed_cycles"] += 1
                
                if "ERROR" in line or "❌" in line or "💥" in line:
                    analysis["errors"].append(line.strip())
                
                if "Processed" in line and "matches" in line:
                    # Extract match count
                    import re
                    matches = re.findall(r'(\d+)\s+matches', line)
                    if matches:
                        analysis["matches_processed"] += int(matches[0])
                
                # Update last activity
                if line.strip():
                    analysis["last_activity"] = line[:19]  # Timestamp part
            
            # Calculate success rate
            if analysis["cycles_completed"] > 0:
                analysis["success_rate"] = (
                    analysis["successful_cycles"] / analysis["cycles_completed"] * 100
                )
            else:
                analysis["success_rate"] = 0
            
            return analysis
            
        except Exception as e:
            return {"error": f"Error analyzing log: {str(e)}"}
    
    def get_system_resources(self):
        """Get system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network I/O
            network = psutil.net_io_counters()
            
            return {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv
                }
            }
        except Exception as e:
            return {"error": str(e)}
    
    def check_data_files(self):
        """Check if pipeline data files exist and are recent"""
        files_to_check = [
            "step1.json",
            "step2/step2.json", 
            "step3/step3.json",
            "step4/step4.json",
            "step5/step5.json",
            "step6_matches.log"
        ]
        
        file_status = {}
        current_time = time.time()
        
        for file_path in files_to_check:
            full_path = self.project_root / file_path
            if full_path.exists():
                stat = full_path.stat()
                age_minutes = (current_time - stat.st_mtime) / 60
                file_status[file_path] = {
                    "exists": True,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "age_minutes": age_minutes,
                    "fresh": age_minutes < 5  # Consider fresh if modified within 5 minutes
                }
            else:
                file_status[file_path] = {
                    "exists": False,
                    "fresh": False
                }
        
        return file_status
    
    def generate_health_report(self):
        """Generate comprehensive health report"""
        print("🏥 Football Bot Health Report")
        print("=" * 50)
        print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Service status
        print("🔧 Service Status")
        print("-" * 20)
        service_info = self.get_service_info()
        if service_info.get("active"):
            print("✅ Service is ACTIVE")
        else:
            print("❌ Service is INACTIVE")
        
        if "uptime" in service_info and service_info["uptime"]:
            print(f"⏰ Started: {service_info['uptime']}")
        
        if "restarts" in service_info:
            print(f"🔄 Restarts: {service_info['restarts']}")
        
        print()
        
        # Log analysis
        print("📊 Pipeline Performance")
        print("-" * 25)
        log_analysis = self.analyze_log_file()
        
        if "error" not in log_analysis:
            print(f"🔄 Total Cycles: {log_analysis['cycles_completed']}")
            print(f"✅ Successful: {log_analysis['successful_cycles']}")
            print(f"❌ Failed: {log_analysis['failed_cycles']}")
            print(f"📈 Success Rate: {log_analysis['success_rate']:.1f}%")
            print(f"🎯 Matches Processed: {log_analysis['matches_processed']}")
            
            if log_analysis['last_activity']:
                print(f"🕐 Last Activity: {log_analysis['last_activity']}")
            
            if log_analysis['errors']:
                print(f"⚠️  Recent Errors: {len(log_analysis['errors'])}")
        else:
            print(f"❌ Log Analysis Error: {log_analysis['error']}")
        
        print()
        
        # Data files status
        print("📁 Data Files Status")
        print("-" * 20)
        file_status = self.check_data_files()
        
        for file_path, status in file_status.items():
            if status["exists"]:
                freshness = "🟢" if status["fresh"] else "🟡"
                size_mb = status["size"] / (1024 * 1024)
                print(f"{freshness} {file_path}: {size_mb:.1f}MB ({status['age_minutes']:.1f}m ago)")
            else:
                print(f"🔴 {file_path}: Missing")
        
        print()
        
        # System resources
        print("💻 System Resources")
        print("-" * 19)
        resources = self.get_system_resources()
        
        if "error" not in resources:
            print(f"🖥️  CPU Usage: {resources['cpu_percent']:.1f}%")
            print(f"💾 Memory Usage: {resources['memory']['percent']:.1f}% ({resources['memory']['used']/(1024**3):.1f}GB/{resources['memory']['total']/(1024**3):.1f}GB)")
            print(f"💿 Disk Usage: {resources['disk']['percent']:.1f}% ({resources['disk']['used']/(1024**3):.1f}GB/{resources['disk']['total']/(1024**3):.1f}GB)")
        else:
            print(f"❌ Resource Monitor Error: {resources['error']}")
        
        print()
    
    def generate_alerts(self):
        """Generate alerts for critical issues"""
        alerts = []
        
        # Check service status
        if not self.get_service_status():
            alerts.append("🚨 CRITICAL: Service is not running!")
        
        # Check log analysis
        log_analysis = self.analyze_log_file()
        if "error" not in log_analysis:
            if log_analysis["success_rate"] < 50:
                alerts.append(f"⚠️  WARNING: Low success rate ({log_analysis['success_rate']:.1f}%)")
            
            if log_analysis["failed_cycles"] > 10:
                alerts.append(f"⚠️  WARNING: High number of failed cycles ({log_analysis['failed_cycles']})")
            
            # Check for recent activity
            if log_analysis["last_activity"]:
                try:
                    last_time = datetime.strptime(log_analysis["last_activity"], "%Y-%m-%d %H:%M:%S")
                    time_diff = datetime.now() - last_time
                    if time_diff > timedelta(minutes=10):
                        alerts.append(f"⚠️  WARNING: No activity for {time_diff}")
                except:
                    pass
        
        # Check system resources
        resources = self.get_system_resources()
        if "error" not in resources:
            if resources["cpu_percent"] > 90:
                alerts.append(f"⚠️  WARNING: High CPU usage ({resources['cpu_percent']:.1f}%)")
            
            if resources["memory"]["percent"] > 90:
                alerts.append(f"⚠️  WARNING: High memory usage ({resources['memory']['percent']:.1f}%)")
            
            if resources["disk"]["percent"] > 90:
                alerts.append(f"⚠️  WARNING: High disk usage ({resources['disk']['percent']:.1f}%)")
        
        return alerts
    
    def monitor_live(self, interval=30):
        """Monitor system in real-time"""
        print("📡 Football Bot Live Monitor")
        print("=" * 40)
        print(f"⏰ Monitoring every {interval} seconds (Ctrl+C to stop)")
        print()
        
        try:
            while True:
                os.system('clear')  # Clear screen
                
                print(f"📡 Live Monitor - {datetime.now().strftime('%H:%M:%S')}")
                print("=" * 40)
                
                # Quick status
                service_active = self.get_service_status()
                status_icon = "🟢" if service_active else "🔴"
                print(f"{status_icon} Service: {'ACTIVE' if service_active else 'INACTIVE'}")
                
                # Recent activity
                log_analysis = self.analyze_log_file()
                if "error" not in log_analysis and log_analysis["last_activity"]:
                    print(f"🕐 Last Activity: {log_analysis['last_activity']}")
                    print(f"🔄 Cycles: {log_analysis['cycles_completed']} (Success: {log_analysis['success_rate']:.1f}%)")
                
                # System resources
                resources = self.get_system_resources()
                if "error" not in resources:
                    print(f"🖥️  CPU: {resources['cpu_percent']:.1f}% | 💾 RAM: {resources['memory']['percent']:.1f}%")
                
                # Alerts
                alerts = self.generate_alerts()
                if alerts:
                    print("\n🚨 ALERTS:")
                    for alert in alerts:
                        print(f"  {alert}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")

def main():
    """Main entry point with command-line interface"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 health_monitor.py [report|alerts|monitor|logs]")
        return
    
    command = sys.argv[1]
    
    monitor = HealthMonitor()
    
    if command == "report":
        monitor.generate_health_report()
    elif command == "alerts":
        alerts = monitor.generate_alerts()
        if alerts:
            for alert in alerts:
                print(alert)
        else:
            print("✅ No alerts - system is healthy")
    elif command == "monitor":
        interval = 30
        if len(sys.argv) > 2:
            try:
                interval = int(sys.argv[2])
            except ValueError:
                interval = 30
        monitor.monitor_live(interval)
    elif command == "logs":
        lines = 50
        if len(sys.argv) > 2:
            try:
                lines = int(sys.argv[2])
            except ValueError:
                lines = 50
        print(monitor.get_recent_logs(lines))
    else:
        print("Unknown command. Use: report, alerts, monitor, or logs")

if __name__ == "__main__":
    main()
