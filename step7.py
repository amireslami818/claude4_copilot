#!/usr/bin/env python3
"""
Step 7 - Status Filter & Display (Statuses 2–7)
Filters matches whose status_id is one of {2,3,4,5,6,7}
Writes human-readable match summaries to step7_matches.log
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# Use the same timezone as other modules
TZ = ZoneInfo("America/New_York")

# Path constants - using absolute paths to avoid working directory issues
BASE_DIR = Path(__file__).resolve().parent  # Root directory for logs (same level as step7.py)
STEP5_JSON = Path(__file__).resolve().parent / "step5" / "step5.json"

# The new status set: 2,3,4,5,6,7 (First half, Half-time break, Second half, Extra time, Penalty shootout, Finished)
STATUS_FILTER = {2, 3, 4, 5, 6, 7}

def setup_logger():
    """Setup logger to write formatted match summaries to file"""
    log_file = BASE_DIR / "step7_matches.log"
    # Ensure step7 directory exists (in case pipeline runs from orchestrator)
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger('step7_matches')
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False  # Prevent double‐logging

    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# Global logger instance
match_logger = setup_logger()

def log_and_print(message: str):
    """Print message to console and also write to step7_matches.log"""
    print(message)
    match_logger.info(message)
    # Force flush
    for handler in match_logger.handlers:
        handler.flush()

def get_eastern_time() -> str:
    """Return current Eastern time as formatted string."""
    now = datetime.now(TZ)
    return now.strftime("%m/%d/%Y %I:%M:%S %p %Z")

def get_daily_fetch_count() -> int:
    """
    Read the counter file (step6/daily_fetch_counter.txt) and return
    the current count for today. If missing or unreadable, return 1.
    """
    counter_file = Path(__file__).resolve().parent / "step6" / "daily_fetch_counter.txt"
    try:
        if counter_file.exists():
            content = counter_file.read_text().strip()
            return int(content) if content else 1
        return 1
    except Exception:
        return 1

def get_status_description(status_id: int) -> str:
    """Map numeric status_id → human‐readable description."""
    status_map = {
        1: "Not started",
        2: "First half",
        3: "Half-time break",
        4: "Second half",
        5: "Extra time",
        6: "Penalty shootout",
        7: "Finished",
        8: "Finished",      # (just in case, but 8 is not in our filter)
        9: "Postponed",
        10: "Canceled",
        11: "To be announced",
        12: "Interrupted",
        13: "Abandoned",
        14: "Suspended",
    }
    return status_map.get(status_id, f"Unknown ({status_id})")

def sort_matches_by_competition_and_status(matches: dict) -> list[tuple[str, dict]]:
    """
    Sort matches first by competition name (alphabetically),
    then by status_id ascending, then by match_id to stabilize.
    """
    def keyfn(item):
        _match_id, data = item
        comp = data.get("competition", "ZZZ_Unknown")
        st   = data.get("status_id", 99)
        mid  = data.get("match_id", "")
        return (comp, st, mid)

    return sorted(matches.items(), key=keyfn)

def write_main_header(fetch_count: int, total: int, generated_at: str, pipeline_time=None):
    """Write the header block at the top of step7_matches.log."""
    header = (
        f"\n{'='*80}\n"
        f"🔥 STEP 7: STATUS FILTER (2–7)\n"
        f"{'='*80}\n"
        f"Filter Time: {get_eastern_time()}\n"
        f"Data Generated: {generated_at}\n"
        f"Pipeline Time: {pipeline_time or 'Not provided'}\n"
        f"Daily Fetch: #{fetch_count}\n"
        f"Statuses Filtered: {sorted(STATUS_FILTER)}\n"
        f"Included Matches Count: {total}\n"
        f"{'='*80}\n"
    )
    match_logger.info(header)
    for h in match_logger.handlers:
        h.flush()

def write_main_footer(fetch_count: int, total: int, generated_at: str, pipeline_time=None):
    """Write the footer block at the bottom of step7_matches.log."""
    footer = (
        f"\n{'='*80}\n"
        f"END OF STATUS FILTER – STEP 7\n"
        f"{'='*80}\n"
        f"Summary Time: {get_eastern_time()}\n"
        f"Total Matches (statuses 2–7): {total}\n"
        f"Daily Fetch: #{fetch_count}\n"
        f"{'='*80}\n"
    )
    match_logger.info(footer)
    for h in match_logger.handlers:
        h.flush()

def write_competition_group_header(competition: str, country: str):
    """Write a competition‐level separator header to both console + log."""
    header = (
        f"\n{'#'*80}\n"
        f"🏆 {competition.upper()}\n"
        f"📍 {country}\n"
        f"{'#'*80}\n"
    )
    log_and_print(header)

def write_status_group_header(status_id: int, status_desc: str):
    """
    Write a status group header (e.g. "FIRST HALF", "FINISHED") 
    above the matches of that status within a competition.
    """
    status_groups = {
        2: "🔴 FIRST HALF",
        3: "⏸️  HALF-TIME BREAK",
        4: "🔴 SECOND HALF",
        5: "⚡ EXTRA TIME",
        6: "🥅 PENALTY SHOOTOUT",
        7: "✅ FINISHED",
    }
    group_name = status_groups.get(status_id, f"STATUS {status_id}")
    header = (
        f"\n{'='*80}\n"
        f"                    {group_name}\n"
        f"{'='*80}\n"
    )
    log_and_print(header)

def process_match(match_data: dict, match_num: int, total_matches: int):
    """
    Given one match's data, print + log its details:
    - competition, teams, score, status text,
    (For brevity, we're only printing competition, teams, score, status here.)
    """
    blk = (
        f"\n{'='*80}\n"
        f"STATUS-FILTER MATCH {match_num} of {total_matches}\n"
        f"Match ID: {match_data.get('match_id', 'N/A')}\n"
        f"{'='*80}\n"
    )
    log_and_print(blk)

    comp_line = f"Competition: {match_data.get('competition', 'Unknown')} ({match_data.get('country', 'Unknown')})"
    teams_line = f"Match: {match_data.get('home_team', 'Unknown')} vs {match_data.get('away_team', 'Unknown')}"
    log_and_print(comp_line)
    log_and_print(teams_line)

    score = match_data.get("score", "N/A")
    status_id = match_data.get("status_id", None)
    status_desc = get_status_description(status_id)
    status_line = f"Score: {score}   |   Status: {status_desc} (ID: {status_id})"
    log_and_print(status_line)

    log_and_print("")  # blank line after each match

def live_match_filter(pipeline_time=None):
    """
    Filter function for the orchestrator to get live matches with status IDs 2-7.
    
    Args:
        pipeline_time: Optional pipeline timing info for orchestrator coordination
    
    Returns:
        dict: Contains filtered matches and metadata
    """
    try:
        # Load step5.json data
        if not STEP5_JSON.exists():
            return {
                "success": False,
                "error": f"Step5 file not found: {STEP5_JSON}",
                "filtered_matches": 0,
                "total_matches": 0
            }
        
        with STEP5_JSON.open("r", encoding="utf-8") as f:
            step5_data = json.load(f)
        
        # Extract matches from step5 data
        # The matches are in the latest history entry, not at the top level
        history = step5_data.get("history", [])
        if not history:
            return {
                "success": True,
                "filtered_matches": 0,
                "total_matches": 0,
                "matches": {}
            }
        
        # Get the latest entry from history
        latest_entry = history[-1]
        matches = latest_entry.get("matches", {})
        if not matches:
            return {
                "success": True,
                "filtered_matches": 0,
                "total_matches": 0,
                "matches": {}
            }
        
        # Filter matches by status IDs 2-7
        filtered_matches = {
            match_id: match_data
            for match_id, match_data in matches.items()
            if match_data.get("status_id") in STATUS_FILTER
        }
        
        filtered_count = len(filtered_matches)
        total_count = len(matches)
        
        # Log the filtering activity using the existing logger
        log_and_print(f"Live match filter: {filtered_count} matches found (from {total_count} total)")
        
        return {
            "success": True,
            "filtered_matches": filtered_count,
            "total_matches": total_count,
            "matches": filtered_matches,
            "status_filter": list(STATUS_FILTER),
            "timestamp": get_eastern_time(),
            "pipeline_time": pipeline_time
        }
        
    except Exception as e:
        error_msg = f"Error in live_match_filter: {str(e)}"
        log_and_print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "filtered_matches": 0,
            "total_matches": 0
        }

def run_status_filter(pipeline_time=None):
    """
    Main filtering logic that loads step5.json, filters matches by status 2-7,
    and writes detailed output to step7_matches.log.
    
    Returns:
        dict: Contains filtered matches and metadata
    """
    fetch_count = get_daily_fetch_count()
    generated_at = get_eastern_time()
    
    # Load and filter the matches
    result = live_match_filter(pipeline_time)
    
    if not result.get("success", False):
        # Handle error case
        log_and_print(f"❌ Error: {result.get('error', 'Unknown error')}")
        write_main_header(fetch_count, 0, generated_at, pipeline_time)
        log_and_print("No matches found due to error.")
        write_main_footer(fetch_count, 0, generated_at, pipeline_time)
        return result
    
    matches = result.get("matches", {})
    total_filtered = result.get("filtered_matches", 0)
    
    # Write the main header
    write_main_header(fetch_count, total_filtered, generated_at, pipeline_time)
    
    if total_filtered == 0:
        log_and_print("No matches found for the given status filter (2-7).")
    else:
        log_and_print(f"Processing {total_filtered} matches with statuses {sorted(STATUS_FILTER)}...\n")
        
        # Sort matches by competition and status for organized output
        sorted_matches = sort_matches_by_competition_and_status(matches)
        
        current_competition = None
        current_status = None
        match_num = 0
        
        for match_id, match_data in sorted_matches:
            # Check if we need a new competition header
            competition = match_data.get("competition", "Unknown")
            country = match_data.get("country", "Unknown")
            if competition != current_competition:
                if current_competition is not None:
                    log_and_print("")  # Blank line between competitions
                write_competition_group_header(competition, country)
                current_competition = competition
                current_status = None  # Reset status tracking for new competition
            
            # Check if we need a new status header
            status_id = match_data.get("status_id")
            if status_id != current_status:
                write_status_group_header(status_id, get_status_description(status_id))
                current_status = status_id
            
            # Process the individual match
            match_num += 1
            process_match(match_data, match_num, total_filtered)
    
    # Write the main footer
    write_main_footer(fetch_count, total_filtered, generated_at, pipeline_time)
    
    return result

def main():
    """Main function to execute the script logic."""
    log_and_print(f"🚀 Starting Step 7: Status Filter (2-7) at {get_eastern_time()}")
    result = run_status_filter()
    
    if result.get("success", False):
        filtered_count = result.get("filtered_matches", 0)
        total_count = result.get("total_matches", 0)
        log_and_print(f"✅ Step 7 completed: {filtered_count} matches filtered from {total_count} total matches")
    else:
        log_and_print(f"❌ Step 7 failed: {result.get('error', 'Unknown error')}")
    
    return result

if __name__ == "__main__":
    main()
