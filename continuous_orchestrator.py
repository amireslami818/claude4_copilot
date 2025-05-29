#!/usr/bin/env python3
"""
Football Bot Continuous Pipeline Orchestrator
============================================

A robust continuous operation system that runs the complete football betting
data pipeline (Steps 1-6) at 60-second intervals with comprehensive error
handling, logging, and graceful shutdown capabilities.

Author: GitHub Copilot
Version: 1.0.0
"""

import os
import sys
import time
import signal
import asyncio
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import json
import subprocess

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

class ContinuousOrchestrator:
    """
    Continuous Pipeline Orchestrator for Football Bot
    
    Features:
    - Full pipeline execution (Steps 1-6)
    - 60-second interval scheduling
    - Comprehensive error handling
    - Graceful shutdown handling
    - Performance monitoring
    - Health checks
    """
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.running = False
        self.cycle_count = 0
        self.start_time = None
        self.last_success = None
        self.error_count = 0
        self.consecutive_errors = 0
        
        # Setup logging
        self.setup_logging()
        
        # Pipeline step configurations
        self.steps = {
            1: {"script": "step1.py", "desc": "Data Fetcher"},
            2: {"script": "step2/step2.py", "desc": "Data Processor"},
            3: {"script": "step3/step3.py", "desc": "JSON Summary Generator"},
            4: {"script": "step4/step4.py", "desc": "Match Summary Extractor"},
            5: {"script": "step5/step5.py", "desc": "Odds & Environment Converter"},
            6: {"script": "step6/step6.py", "desc": "Pretty Print Display"}
        }
        
        # Performance metrics
        self.metrics = {
            "total_cycles": 0,
            "successful_cycles": 0,
            "failed_cycles": 0,
            "total_runtime": 0,
            "average_cycle_time": 0,
            "matches_processed": 0
        }
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.logger.info("🚀 Football Bot Continuous Orchestrator initialized")
    
    def setup_logging(self):
        """Configure comprehensive logging system"""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)8s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler for detailed logs
        file_handler = logging.FileHandler(
            log_dir / f"continuous_orchestrator_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler for real-time monitoring
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        
        # Setup logger
        self.logger = logging.getLogger("FootballBot")
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        signal_names = {signal.SIGINT: "SIGINT", signal.SIGTERM: "SIGTERM"}
        signal_name = signal_names.get(signum, f"Signal {signum}")
        
        self.logger.info(f"🛑 Received {signal_name}, initiating graceful shutdown...")
        self.running = False
    
    async def execute_step(self, step_num: int) -> Dict[str, Any]:
        """
        Execute a single pipeline step
        
        Args:
            step_num: Step number (1-6)
            
        Returns:
            Dict with execution results
        """
        step_info = self.steps[step_num]
        script_path = self.project_root / step_info["script"]
        
        start_time = time.time()
        
        try:
            self.logger.debug(f"  📋 Executing Step {step_num}: {step_info['desc']}")
            
            # Execute step script
            process = await asyncio.create_subprocess_exec(
                sys.executable, str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_root)
            )
            
            stdout, stderr = await process.communicate()
            execution_time = time.time() - start_time
            
            if process.returncode == 0:
                self.logger.debug(f"  ✅ Step {step_num} completed in {execution_time:.2f}s")
                return {
                    "success": True,
                    "step": step_num,
                    "execution_time": execution_time,
                    "stdout": stdout.decode('utf-8'),
                    "stderr": stderr.decode('utf-8')
                }
            else:
                self.logger.error(f"  ❌ Step {step_num} failed (exit code: {process.returncode})")
                self.logger.error(f"  Error output: {stderr.decode('utf-8')}")
                return {
                    "success": False,
                    "step": step_num,
                    "execution_time": execution_time,
                    "exit_code": process.returncode,
                    "stdout": stdout.decode('utf-8'),
                    "stderr": stderr.decode('utf-8')
                }
                
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"  💥 Step {step_num} crashed: {str(e)}")
            return {
                "success": False,
                "step": step_num,
                "execution_time": execution_time,
                "exception": str(e),
                "traceback": traceback.format_exc()
            }
    
    async def execute_full_pipeline(self) -> Dict[str, Any]:
        """
        Execute the complete pipeline (Steps 1-6)
        
        Returns:
            Dict with pipeline execution results
        """
        pipeline_start = time.time()
        results = {
            "cycle": self.cycle_count,
            "start_time": datetime.now().isoformat(),
            "steps": {},
            "success": False,
            "total_time": 0,
            "matches_processed": 0
        }
        
        self.logger.info(f"🔄 Starting Pipeline Cycle #{self.cycle_count}")
        
        # Execute each step sequentially
        for step_num in range(1, 7):
            if not self.running:
                self.logger.info("🛑 Shutdown requested, aborting pipeline")
                break
                
            step_result = await self.execute_step(step_num)
            results["steps"][step_num] = step_result
            
            if not step_result["success"]:
                self.logger.error(f"💥 Pipeline failed at Step {step_num}")
                break
        else:
            # All steps completed successfully
            results["success"] = True
            self.last_success = datetime.now()
            self.consecutive_errors = 0
            
            # Extract match count from step output if available
            if 6 in results["steps"] and results["steps"][6]["success"]:
                try:
                    # Try to extract match count from step6 output
                    step6_output = results["steps"][6]["stdout"]
                    if "matches" in step6_output.lower():
                        # Simple regex to find number of matches
                        import re
                        matches = re.findall(r'(\d+)\s+matches?', step6_output.lower())
                        if matches:
                            results["matches_processed"] = int(matches[-1])
                except Exception:
                    pass
        
        results["total_time"] = time.time() - pipeline_start
        
        # Update metrics
        self.update_metrics(results)
        
        if results["success"]:
            self.logger.info(f"✅ Pipeline Cycle #{self.cycle_count} completed successfully in {results['total_time']:.2f}s")
            if results["matches_processed"]:
                self.logger.info(f"📊 Processed {results['matches_processed']} matches")
        else:
            self.logger.error(f"❌ Pipeline Cycle #{self.cycle_count} failed after {results['total_time']:.2f}s")
            self.consecutive_errors += 1
        
        return results
    
    def update_metrics(self, results: Dict[str, Any]):
        """Update performance metrics"""
        self.metrics["total_cycles"] += 1
        
        if results["success"]:
            self.metrics["successful_cycles"] += 1
            if results["matches_processed"]:
                self.metrics["matches_processed"] += results["matches_processed"]
        else:
            self.metrics["failed_cycles"] += 1
            self.error_count += 1
        
        self.metrics["total_runtime"] += results["total_time"]
        self.metrics["average_cycle_time"] = (
            self.metrics["total_runtime"] / self.metrics["total_cycles"]
        )
    
    def log_status_report(self):
        """Log comprehensive status report"""
        uptime = time.time() - self.start_time if self.start_time else 0
        
        self.logger.info("📊 === STATUS REPORT ===")
        self.logger.info(f"🕐 Uptime: {uptime/3600:.1f} hours")
        self.logger.info(f"🔄 Total Cycles: {self.metrics['total_cycles']}")
        self.logger.info(f"✅ Successful: {self.metrics['successful_cycles']}")
        self.logger.info(f"❌ Failed: {self.metrics['failed_cycles']}")
        self.logger.info(f"📈 Success Rate: {(self.metrics['successful_cycles']/max(1, self.metrics['total_cycles']))*100:.1f}%")
        self.logger.info(f"⏱️  Avg Cycle Time: {self.metrics['average_cycle_time']:.2f}s")
        self.logger.info(f"🎯 Matches Processed: {self.metrics['matches_processed']}")
        if self.last_success:
            self.logger.info(f"🕐 Last Success: {self.last_success.strftime('%H:%M:%S')}")
        self.logger.info("========================")
    
    async def run_continuous(self):
        """
        Main continuous operation loop
        
        Runs the pipeline every 60 seconds with error handling and monitoring
        """
        self.running = True
        self.start_time = time.time()
        
        self.logger.info("🌟 Starting Football Bot Continuous Pipeline")
        self.logger.info("⏰ Running every 60 seconds - Press Ctrl+C to stop gracefully")
        
        while self.running:
            try:
                self.cycle_count += 1
                
                # Execute pipeline
                results = await self.execute_full_pipeline()
                
                # Check for excessive consecutive errors
                if self.consecutive_errors >= 5:
                    self.logger.error(f"🚨 Too many consecutive errors ({self.consecutive_errors}), implementing backoff")
                    await asyncio.sleep(300)  # 5-minute backoff
                    self.consecutive_errors = 0  # Reset after backoff
                
                # Log status report every 10 cycles
                if self.cycle_count % 10 == 0:
                    self.log_status_report()
                
                # Wait for next cycle (60 seconds total, minus execution time)
                if self.running:
                    wait_time = max(0, 60 - results["total_time"])
                    if wait_time > 0:
                        self.logger.debug(f"⏳ Waiting {wait_time:.1f}s until next cycle...")
                        await asyncio.sleep(wait_time)
                    else:
                        self.logger.warning(f"⚠️  Pipeline took {results['total_time']:.1f}s, no wait time!")
                
            except Exception as e:
                self.logger.error(f"💥 Orchestrator error: {str(e)}")
                self.logger.error(traceback.format_exc())
                self.error_count += 1
                
                # Wait before retrying on error
                await asyncio.sleep(30)
        
        self.logger.info("🏁 Football Bot Continuous Pipeline stopped")
        self.log_status_report()

async def main():
    """Main entry point"""
    orchestrator = ContinuousOrchestrator()
    try:
        await orchestrator.run_continuous()
    except KeyboardInterrupt:
        orchestrator.logger.info("🛑 Keyboard interrupt received")
    except Exception as e:
        orchestrator.logger.error(f"💥 Fatal error: {str(e)}")
        orchestrator.logger.error(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
