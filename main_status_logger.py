#!/usr/bin/env python3
"""
Main Status Logger - Consolidates status summaries from all pipeline steps
Creates Main_Status.log with unified status tracking across Steps 1, 5, 6, and 7
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# Use the same timezone as other modules
TZ = ZoneInfo("America/New_York")

# Path constants
BASE_DIR = Path(__file__).resolve().parent  # Football_bot directory
MAIN_STATUS_LOG = BASE_DIR / "Main_Status.log"
STEP1_JSON = BASE_DIR / "step1" / "step1.json"
STEP2_JSON = BASE_DIR / "step2" / "step2.json"
STEP5_JSON = BASE_DIR / "step5" / "step5.json"
STEP6_LOG = BASE_DIR / "step6" / "step6_matches.log"
STEP7_LOG = BASE_DIR / "step7" / "step7_matches.log"

def setup_main_status_logger():
    """Setup the main status logger"""
    logger = logging.getLogger('main_status')
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    file_handler = logging.FileHandler(MAIN_STATUS_LOG, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# Global logger instance
main_logger = setup_main_status_logger()

def get_eastern_time():
    """Get current time in Eastern timezone"""
    return datetime.now(TZ).strftime("%m/%d/%Y %I:%M:%S %p %Z")

def get_status_name(status_id):
    """Get human-readable status name from status ID"""
    status_map = {
        1: "Not started",
        2: "First half", 
        3: "Half-time",
        4: "Second half",
        5: "Overtime", 
        6: "Overtime (deprecated)",
        7: "Penalty shoot-out",
        8: "End",
        9: "Postponed",
        10: "Suspended",
        11: "Interrupted",
        12: "Abandoned", 
        13: "To be determined",
        14: "Cancelled"
    }
    return status_map.get(status_id, f"Unknown (ID: {status_id})")

def format_status_breakdown(status_counts):
    """Format status counts into readable breakdown"""
    if not status_counts:
        return "No status data available"
    
    breakdown_lines = []
    for status_id in sorted(status_counts.keys()):
        count = status_counts[status_id]
        status_name = get_status_name(status_id)
        breakdown_lines.append(f"  {status_name} (ID: {status_id}): {count}")
    
    return "\n".join(breakdown_lines)

def extract_step1_status(step1_file):
    """Extract status information from Step 1 JSON"""
    try:
        if not step1_file.exists():
            return {"error": "Step 1 file not found"}
        
        with open(step1_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        results = data.get("live_matches", {}).get("results", [])
        total_matches = len(results)
        timestamp = data.get("timestamp", "Unknown")
        
        # Count matches by status_id - check both locations where status might be stored
        status_counts = {}
        for match in results:
            status_id = None
            
            # First, check if status_id is directly in the match (added by our processing)
            if "status_id" in match:
                status_id = match["status_id"]
            # Otherwise, extract from score array (raw API structure)
            elif "score" in match and isinstance(match["score"], list) and len(match["score"]) > 1:
                status_id = match["score"][1]
            
            if status_id is not None:
                if status_id in status_counts:
                    status_counts[status_id] += 1
                else:
                    status_counts[status_id] = 1
        
        # Also get comprehensive summary if available
        comprehensive_summary = data.get("comprehensive_status_summary", {})
        detailed_status_mapping = data.get("detailed_status_mapping", {})
        
        return {
            "total_matches": total_matches,
            "timestamp": timestamp,
            "status": "Raw API data",
            "status_counts": status_counts,
            "comprehensive_summary": comprehensive_summary,
            "detailed_status_mapping": detailed_status_mapping
        }
    except Exception as e:
        return {"error": f"Error reading Step 1: {str(e)}"}

def extract_step2_status(step2_file):
    """Extract status information from Step 2 JSON"""
    try:
        if not step2_file.exists():
            return {"error": "Step 2 file not found"}
        
        with open(step2_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Get the latest batch from history
        history = data.get("history", [])
        if not history:
            return {"error": "No history in Step 2 data"}
        
        latest_batch = history[-1]
        total_matches = latest_batch.get("total_matches", 0)
        timestamp = latest_batch.get("timestamp", "Unknown")
        matches = latest_batch.get("matches", {})
        
        # Count matches by status_id and calculate in-play matches
        status_counts = {}
        in_play_matches = 0
        matches_with_status = 0
        matches_without_status = 0
        
        for match_id, match_data in matches.items():
            status_id = None
            
            # Check for status_id directly or in nested status object
            if "status_id" in match_data:
                status_id = match_data["status_id"]
            elif "status" in match_data and isinstance(match_data["status"], dict):
                status_id = match_data["status"].get("id")
            
            if status_id is not None:
                status_counts[status_id] = status_counts.get(status_id, 0) + 1
                matches_with_status += 1
                
                # Count in-play matches (status 2,3,4,5,6)
                if status_id in [2, 3, 4, 5, 6]:
                    in_play_matches += 1
            else:
                matches_without_status += 1
        
        # Create comprehensive summary
        comprehensive_summary = {
            "in_play_matches": in_play_matches,
            "matches_with_status": matches_with_status,
            "matches_without_status": matches_without_status
        }
        
        return {
            "total_matches": total_matches,
            "timestamp": timestamp,
            "status": "Processed and summarized data",
            "status_counts": status_counts,
            "comprehensive_summary": comprehensive_summary
        }
        
    except Exception as e:
        return {"error": f"Error reading Step 2: {str(e)}"}

def extract_step5_status(step5_file):
    """Extract status information from Step 5 JSON"""
    try:
        if not step5_file.exists():
            return {"error": "Step 5 file not found"}
        
        # Since step5.json is large, we'll sample from it to get status breakdown
        status_counts = {}
        total_matches = 0
        timestamp = "Unknown"
        
        with open(step5_file, 'r', encoding='utf-8') as f:
            # Read the file in chunks to find recent data and count statuses
            chunk_size = 1024 * 1024  # 1MB chunks
            content_buffer = ""
            matches_found = 0
            
            # First, try to get the most recent history entry
            f.seek(0)
            first_chunk = f.read(chunk_size)
            
            # Extract timestamp and total from the beginning
            import re
            timestamp_match = re.search(r'"generated_at":\s*"([^"]+)"', first_chunk)
            total_match = re.search(r'"total_matches":\s*(\d+)', first_chunk)
            
            if timestamp_match:
                timestamp = timestamp_match.group(1)
            if total_match:
                total_matches = int(total_match.group(1))
            
            # Look for status_id patterns in the first chunk to get status breakdown
            f.seek(0)
            sample_content = f.read(chunk_size * 2)  # Read 2MB to get a good sample
            
            # Find all status_id occurrences in the sample
            status_matches = re.findall(r'"status_id":\s*(\d+)', sample_content)
            
            # Count the status IDs from the sample
            for status_id_str in status_matches:
                status_id = int(status_id_str)
                status_counts[status_id] = status_counts.get(status_id, 0) + 1
        
        return {
            "total_matches": total_matches,
            "timestamp": timestamp,
            "status": "Processed with odds data",
            "status_counts": status_counts
        }
        
    except Exception as e:
        return {"error": f"Error reading Step 5: {str(e)}"}

def extract_step6_status(step6_log):
    """Extract status information from Step 6 log"""
    try:
        if not step6_log.exists():
            return {"error": "Step 6 log not found"}
        
        # Read the last part of the log to get the most recent summary
        with open(step6_log, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the most recent MATCH STATUS SUMMARY block
        import re
        
        # Look for the last occurrence of MATCH STATUS SUMMARY and get the content after it
        # Find all positions where "MATCH STATUS SUMMARY" occurs
        summary_positions = [match.start() for match in re.finditer(r'MATCH STATUS SUMMARY', content)]
        
        if not summary_positions:
            return {"error": "No status summary found in Step 6 log"}
        
        # Get the content starting from the last MATCH STATUS SUMMARY
        last_summary_start = summary_positions[-1]
        # Find the end of this summary block (look for the next "END OF SUMMARY FETCH" or end of file)
        summary_content = content[last_summary_start:]
        end_marker = summary_content.find("END OF SUMMARY FETCH")
        if end_marker != -1:
            summary_content = summary_content[:end_marker]
        
        # Extract data from the summary block
        status_counts = {}
        total_matches = 0
        timestamp = "Unknown"
        
        # Find total matches
        total_match = re.search(r'Total Matches:\s*(\d+)', summary_content)
        if total_match:
            total_matches = int(total_match.group(1))
        
        # Find all status lines in the summary using line-by-line processing
        # Look for patterns like "First half (ID: 2): 23 Matches" or "Half-time (ID: 3): 1 Match"
        lines = summary_content.split('\n')
        for line in lines:
            line = line.strip()
            # Skip header lines and separators
            if ('SUMMARY' in line or '====' in line or '---' in line or 
                'Total Matches:' in line or not line):
                continue
            
            # Match status lines with flexible Match/Matches
            match = re.match(r'^(.+?)\s*\(ID:\s*(\d+)\):\s*(\d+)\s*Matches?', line)
            if match:
                status_name, status_id_str, count_str = match.groups()
                status_id = int(status_id_str)
                count = int(count_str)
                status_counts[status_id] = count
        
        # Find timestamp from the content after the summary
        remaining_content = content[last_summary_start + len(summary_content):][:500]  # Look in next 500 chars
        time_match = re.search(r'Fetch Time:\s*([^T\n]+)', remaining_content)
        if time_match:
            timestamp = time_match.group(1).strip()
        
        return {
            "total_matches": total_matches,
            "timestamp": timestamp,
            "status_counts": status_counts,
            "status": "Filtered with environment data"
        }
        
    except Exception as e:
        return {"error": f"Error reading Step 6: {str(e)}"}

def extract_step7_status(step7_log):
    """Extract status information from Step 7 log"""
    try:
        if not step7_log.exists():
            return {"error": "Step 7 log not found"}
        
        # Read the last part of the log to get the most recent summary
        with open(step7_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Look for the most recent status summary
        status_counts = {}
        total_matches = 0
        timestamp = "Unknown"
        
        # Search backwards through the file for the most recent summary
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            
            # Look for timestamp
            if "Summary Time:" in line:
                timestamp = line.replace("Summary Time:", "").strip()
            
            # Look for total matches
            if "Total:" in line and total_matches == 0:
                import re
                total_match = re.search(r'Total:\s*(\d+)', line)
                if total_match:
                    total_matches = int(total_match.group(1))
            
            # Look for status breakdown - handle Step 7 format without "Matches"
            if "(ID:" in line and "):" in line and "STEP 7 - STATUS SUMMARY" not in line:
                import re
                # Step 7 format: "First half (ID: 2): 8" (no "Matches" word)
                status_match = re.match(r'^(.+?)\s*\(ID:\s*(\d+)\):\s*(\d+)\s*$', line.strip())
                if status_match and 'SUMMARY' not in line and '====' not in line and '---' not in line and 'Total:' not in line:
                    status_name = status_match.group(1).strip()
                    status_id = int(status_match.group(2))
                    count = int(status_match.group(3))
                    status_counts[status_id] = count
            
            # Stop when we find the start of a summary block
            if "STEP 7 - STATUS SUMMARY" in line:
                break
        
        return {
            "total_matches": total_matches,
            "timestamp": timestamp,
            "status_counts": status_counts,
            "status": "Final filtered (statuses 2-7)"
        }
        
    except Exception as e:
        return {"error": f"Error reading Step 7: {str(e)}"}

def log_consolidated_status():
    """Log consolidated status from all pipeline steps"""
    
    # Get current time
    current_time = get_eastern_time()
    
    # Extract data from all steps
    step1_data = extract_step1_status(STEP1_JSON)
    step2_data = extract_step2_status(STEP2_JSON)
    step5_data = extract_step5_status(STEP5_JSON)
    step6_data = extract_step6_status(STEP6_LOG)
    step7_data = extract_step7_status(STEP7_LOG)
    
    # Create consolidated log entry
    log_entry = f"""
{'='*80}
MAIN STATUS SUMMARY - FOOTBALL BOT PIPELINE
{'='*80}
Generated: {current_time}
{'='*80}

STEP 1 - RAW API DATA
{'─'*40}
Total Matches: {step1_data.get('total_matches', 'Error')}
Timestamp: {step1_data.get('timestamp', 'Error')}
Status: {step1_data.get('status', step1_data.get('error', 'Unknown'))}"""

    # Add Step 1 status breakdown if available
    if 'status_counts' in step1_data and step1_data['status_counts']:
        log_entry += f"\nStatus Breakdown:\n{format_status_breakdown(step1_data['status_counts'])}"
    
    # Add comprehensive summary info if available
    if 'comprehensive_summary' in step1_data and step1_data['comprehensive_summary']:
        comp_sum = step1_data['comprehensive_summary']
        if 'in_play_matches' in comp_sum:
            log_entry += f"\nIN-PLAY MATCHES: {comp_sum['in_play_matches']}"
        if 'matches_with_status' in comp_sum and 'matches_without_status' in comp_sum:
            log_entry += f"\nMatches with status: {comp_sum['matches_with_status']}"
            if comp_sum['matches_without_status'] > 0:
                log_entry += f"\nMatches without status: {comp_sum['matches_without_status']}"

    log_entry += f"""

STEP 2 - PROCESSED AND SUMMARIZED
{'─'*40}
Total Matches: {step2_data.get('total_matches', 'Error')}
Timestamp: {step2_data.get('timestamp', 'Error')}
Status: {step2_data.get('status', step2_data.get('error', 'Unknown'))}"""

    # Add Step 2 status breakdown if available
    if 'status_counts' in step2_data and step2_data['status_counts']:
        log_entry += f"\nStatus Breakdown:\n{format_status_breakdown(step2_data['status_counts'])}"
    
    # Add Step 2 comprehensive summary info if available
    if 'comprehensive_summary' in step2_data and step2_data['comprehensive_summary']:
        comp_sum = step2_data['comprehensive_summary']
        if 'in_play_matches' in comp_sum:
            log_entry += f"\nIN-PLAY MATCHES: {comp_sum['in_play_matches']}"
        if 'matches_with_status' in comp_sum and 'matches_without_status' in comp_sum:
            log_entry += f"\nMatches with status: {comp_sum['matches_with_status']}"
            if comp_sum['matches_without_status'] > 0:
                log_entry += f"\nMatches without status: {comp_sum['matches_without_status']}"

    log_entry += f"""

STEP 5 - PROCESSED WITH ODDS
{'─'*40}
Total Matches: {step5_data.get('total_matches', 'Error')}
Timestamp: {step5_data.get('timestamp', 'Error')}
Status: {step5_data.get('status', step5_data.get('error', 'Unknown'))}"""

    # Add Step 5 status breakdown if available
    if 'status_counts' in step5_data and step5_data['status_counts']:
        log_entry += f"\nStatus Breakdown:\n{format_status_breakdown(step5_data['status_counts'])}"

    log_entry += f"""

STEP 6 - FILTERED WITH ENVIRONMENT
{'─'*40}
Total Matches: {step6_data.get('total_matches', 'Error')}
Timestamp: {step6_data.get('timestamp', 'Error')}
Status: {step6_data.get('status', step6_data.get('error', 'Unknown'))}"""

    # Add Step 6 status breakdown if available
    if 'status_counts' in step6_data and step6_data['status_counts']:
        log_entry += f"\nStatus Breakdown:\n{format_status_breakdown(step6_data['status_counts'])}"

    log_entry += f"""

STEP 7 - FINAL FILTER (STATUSES 2-7)
{'─'*40}
Total Matches: {step7_data.get('total_matches', 'Error')}
Timestamp: {step7_data.get('timestamp', 'Error')}
Status: {step7_data.get('status', step7_data.get('error', 'Unknown'))}"""

    # Add Step 7 status breakdown if available
    if 'status_counts' in step7_data and step7_data['status_counts']:
        log_entry += f"\nStatus Breakdown:\n{format_status_breakdown(step7_data['status_counts'])}"

    log_entry += f"""

{'='*80}
END OF MAIN STATUS SUMMARY
{'='*80}
Report Generated: {current_time}
{'='*80}
"""

    # Write to log
    main_logger.info(log_entry)
    
    # Flush the handler
    for handler in main_logger.handlers:
        handler.flush()

if __name__ == "__main__":
    log_consolidated_status()
    print(f"Main status logged to: {MAIN_STATUS_LOG}")
