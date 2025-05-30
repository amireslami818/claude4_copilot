#!/usr/bin/env python3
"""
Step 7 - Live Match Filter & Display
Filters and displays only active/upcoming matches (status 1-6)

This module processes Step 5 JSON data and:
1. Filters matches to show only active games (status 1-6)
2. Groups matches by competition
3. Sorts within each competition by status (1,2,3,4,5,6)
4. Provides organized display of live/upcoming matches
"""

import json
import os
import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from collections import defaultdict

# Use the same timezone as other modules
TZ = ZoneInfo("America/New_York")

# Path constants
BASE_DIR = Path(__file__).parent
STEP5_JSON = BASE_DIR.parent / "step5" / "step5.json"

# Active status IDs (filter criteria)
ACTIVE_STATUS_IDS = {1, 2, 3, 4, 5, 6}

# Setup logger
def setup_logger():
    """Setup logger to write filtered match summaries to file"""
    log_file = BASE_DIR / "step7_matches.log"
    
    # Create logger
    logger = logging.getLogger('step7_matches')
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create file handler with append mode to preserve previous runs
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Create formatter (just the message, no timestamp prefix)
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    return logger

# Global logger instance
match_logger = setup_logger()

def get_eastern_time():
    """Get current Eastern time formatted string"""
    now = datetime.now(TZ)
    return now.strftime("%m/%d/%Y %I:%M:%S %p %Z")

def get_status_description(status_id):
    """Convert status ID to human readable description"""
    status_map = {
        1: "Not started",
        2: "First half", 
        3: "Half-time break",
        4: "Second half",
        5: "Extra time",
        6: "Penalty shootout",
        7: "Finished",
        8: "Finished",
        9: "Postponed",
        10: "Canceled",
        11: "To be announced",
        12: "Interrupted",
        13: "Abandoned",
        14: "Suspended"
    }
    return status_map.get(status_id, f"Unknown ({status_id})")

def log_and_print(message):
    """Log message to file and print to console"""
    print(message)
    match_logger.info(message)

def filter_active_matches(step5_data):
    """Filter matches to only include active/upcoming games (status 1-6)"""
    if not step5_data or "history" not in step5_data:
        return {}
    
    latest_entry = step5_data["history"][0] if step5_data["history"] else {}
    all_matches = latest_entry.get("matches", {})
    
    active_matches = {}
    for match_id, match_data in all_matches.items():
        # Extract status ID from the match data
        status_id = None
        
        # Try to get status ID from various possible locations
        if "status_id" in match_data:
            status_id = match_data["status_id"]
        elif "status" in match_data and isinstance(match_data["status"], dict):
            status_id = match_data["status"].get("id")
        elif "status" in match_data:
            # If status is a string, try to reverse lookup
            status_str = match_data["status"].lower()
            if "not started" in status_str or status_str == "upcoming":
                status_id = 1
            elif "first half" in status_str or "1st half" in status_str:
                status_id = 2
            elif "half" in status_str and "time" in status_str:
                status_id = 3
            elif "second half" in status_str or "2nd half" in status_str:
                status_id = 4
            elif "extra" in status_str:
                status_id = 5
            elif "penalty" in status_str:
                status_id = 6
            elif "live" in status_str:
                # Default live to first half if unclear
                status_id = 2
        
        # Include match if it has an active status
        if status_id in ACTIVE_STATUS_IDS:
            # Add status_id to match data for sorting
            match_data["_status_id"] = status_id
            active_matches[match_id] = match_data
    
    return active_matches

def group_matches_by_competition(matches):
    """Group matches by competition and sort by status within each group"""
    competitions = defaultdict(list)
    
    for match_id, match_data in matches.items():
        competition = match_data.get("competition", "Unknown Competition")
        competitions[competition].append((match_id, match_data))
    
    # Sort matches within each competition by status ID
    for competition in competitions:
        competitions[competition].sort(key=lambda x: x[1].get("_status_id", 99))
    
    # Sort competitions alphabetically
    return dict(sorted(competitions.items()))

def write_competition_header(competition, match_count):
    """Write formatted competition header"""
    log_and_print("\n" + "="*100)
    log_and_print(f"🏆 COMPETITION: {competition}")
    log_and_print(f"📊 Active Matches: {match_count}")
    log_and_print("="*100)

def write_match_summary(match_id, match_data, match_num_in_comp):
    """Write formatted match summary"""
    status_id = match_data.get("_status_id")
    status_desc = get_status_description(status_id)
    
    log_and_print(f"\n🔸 Match #{match_num_in_comp}")
    log_and_print(f"Match ID: {match_id}")
    log_and_print(f"Status: {status_desc} (ID: {status_id})")
    log_and_print(f"Teams: {match_data.get('home_team', 'Unknown')} vs {match_data.get('away_team', 'Unknown')}")
    log_and_print(f"Score: {match_data.get('score', 'N/A')}")
    
    # Show odds if available
    if "full_time_result" in match_data:
        odds = match_data["full_time_result"]
        if isinstance(odds, dict) and any(odds.values()):
            log_and_print(f"Odds - Home: {odds.get('home', 'N/A')} | Draw: {odds.get('draw', 'N/A')} | Away: {odds.get('away', 'N/A')}")
    
    log_and_print("-" * 50)

def write_summary_stats(total_active, competitions_count):
    """Write overall summary statistics"""
    log_and_print("\n" + "🎯" * 50)
    log_and_print(f"📈 SUMMARY: {total_active} active matches across {competitions_count} competitions")
    log_and_print(f"🕐 Generated at: {get_eastern_time()}")
    log_and_print("🎯" * 50 + "\n")

def live_match_filter(pipeline_time=None):
    """
    Main entry point for Step 7 - called from orchestrator
    
    Args:
        pipeline_time: Optional pipeline execution time for performance tracking
    
    Returns:
        Dictionary containing filtered match data and statistics
    """
    log_and_print(f"\n{'='*60}")
    log_and_print("🔥 STEP 7: LIVE MATCH FILTER - ACTIVE GAMES ONLY")
    log_and_print(f"{'='*60}")
    
    if not STEP5_JSON.exists():
        log_and_print("❌ Error: step5.json not found")
        return {"success": False, "error": "step5.json not found"}
    
    try:
        # Load step5 data
        with open(STEP5_JSON, 'r') as f:
            step5_data = json.load(f)
        
        # Filter to only active matches
        active_matches = filter_active_matches(step5_data)
        
        if not active_matches:
            log_and_print("📭 No active matches found (status 1-6)")
            return {"success": True, "active_matches": 0, "competitions": 0}
        
        # Group by competition and sort
        competitions = group_matches_by_competition(active_matches)
        
        total_active = len(active_matches)
        competitions_count = len(competitions)
        
        log_and_print(f"🎮 Found {total_active} active matches in {competitions_count} competitions")
        log_and_print(f"🔍 Filtering for status IDs: {sorted(ACTIVE_STATUS_IDS)}")
        
        # Display matches grouped by competition
        for competition, matches in competitions.items():
            write_competition_header(competition, len(matches))
            
            for match_num, (match_id, match_data) in enumerate(matches, 1):
                write_match_summary(match_id, match_data, match_num)
        
        # Write summary
        write_summary_stats(total_active, competitions_count)
        
        # Add pipeline timing if provided
        if pipeline_time:
            log_and_print(f"⏱️  Total pipeline time: {pipeline_time:.2f} seconds")
        
        return {
            "success": True,
            "active_matches": total_active,
            "competitions": competitions_count,
            "data": {
                "matches": active_matches,
                "competitions": competitions
            }
        }
        
    except Exception as e:
        error_msg = f"❌ Error in Step 7: {str(e)}"
        log_and_print(error_msg)
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    print("Step 7: Live Match Filter - Use from orchestrator or call live_match_filter() directly")
    # For testing, run the filter
    result = live_match_filter()
    print(f"Result: {result}")
