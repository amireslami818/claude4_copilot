#!/usr/bin/env python3
"""
Step 6 - Pretty Print Match Display
Final step to format and display human-readable match summaries

This module processes Step 5 JSON data and:
1. Formats match information in a readable format
2. Displays betting odds in organized tables
3. Shows environment data with proper formatting
4. Provides comprehensive match summaries for display

IMPORTANT TERMINOLOGY:
- LIVE MATCHES = All matches from /match/detail_live API endpoint (broader category)
- IN-PLAY MATCHES = Only matches with status_id 2,3,4,5,6 (actively playing subset of live matches)
"""

import json
import os
import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# Use the same timezone as other modules
TZ = ZoneInfo("America/New_York")

# Path constants
BASE_DIR = Path(__file__).parent
STEP1_JSON = BASE_DIR.parent / "step1" / "step1.json"  # Changed to read from step1.json directly

# Setup logger
def setup_logger():
    """Setup logger to write formatted match summaries to file"""
    log_file = BASE_DIR / "step6_matches.log"  # Changed to write in step6 folder
    
    # Create logger
    logger = logging.getLogger('step6_matches')
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

def get_daily_fetch_count():
    """Get and increment the daily fetch counter"""
    counter_file = BASE_DIR / "daily_fetch_counter.txt"
    today = datetime.now(TZ).strftime("%Y-%m-%d")
    
    # Read existing counter data
    fetch_count = 1
    if counter_file.exists():
        try:
            with open(counter_file, 'r') as f:
                data = f.read().strip().split('|')
                if len(data) == 2:
                    last_date, last_count = data
                    if last_date == today:
                        fetch_count = int(last_count) + 1
        except (ValueError, FileNotFoundError):
            pass
    
    # Write updated counter
    with open(counter_file, 'w') as f:
        f.write(f"{today}|{fetch_count}")
    
    return fetch_count

def get_status_description(status_id):
    """Convert status ID to human readable description - Official API mapping"""
    status_map = {
        0: "Abnormal (suggest hiding)",
        1: "Not started",
        2: "First half",
        3: "Half-time",
        4: "Second half",
        5: "Overtime",
        6: "Overtime (deprecated)",
        7: "Penalty Shoot-out",
        8: "End",
        9: "Delay",
        10: "Interrupt",
        11: "Cut in half",
        12: "Cancel",
        13: "To be determined"
    }
    return status_map.get(status_id, f"Unknown ({status_id})")

def write_combined_match_summary(match, match_num, total_matches):
    """Write a formatted header for each match"""
    print("\n" + "="*80)
    print(f"MATCH {match_num} of {total_matches}")
    print(f"Match ID: {match.get('match_id', 'N/A')}")
    print(f"Competition ID: {match.get('competition_id', 'N/A')}")
    print("="*80)

def transform_odds(odds_data, odds_type):
    """Transform odds data based on type"""
    # Placeholder for odds transformation logic
    # Will be implemented based on the odds structure from step5
    return odds_data

def pick_best_entry(odds_list):
    """Pick the best entry from odds list (most recent or first available)"""
    if not odds_list:
        return {}
    if isinstance(odds_list, list) and len(odds_list) > 0:
        return odds_list[0]  # Return first entry
    if isinstance(odds_list, dict):
        return odds_list
    return {}

def hk_to_american(hk_odds):
    """Convert Hong Kong odds to American odds with proper +/- formatting"""
    try:
        hk_odds = float(hk_odds)
        if hk_odds >= 1:
            result = int(round(hk_odds * 100))
            return f"+{result}" if result > 0 else str(result)
        else:
            return str(int(round(-100 / hk_odds)))
    except (ValueError, ZeroDivisionError):
        return "0"

def decimal_to_american(decimal_odds):
    """Convert decimal odds to American odds with proper +/- formatting"""
    try:
        decimal_odds = float(decimal_odds)
        if decimal_odds == 0:
            return "0"
        
        if decimal_odds >= 2.0:
            result = int(round((decimal_odds - 1) * 100))
            return f"+{result}" if result > 0 else str(result)
        else:
            return str(int(round(-100 / (decimal_odds - 1))))
    except (ValueError, ZeroDivisionError):
        return "0"

def summarize_environment_step5_style(env):
    """Format environment data for display using Step 5 logic"""
    lines = []
    
    # Check if there's any data
    if not env:
        return ["No environment data available"]
        
    # Weather condition mapping
    weather_conditions = {
        "1": "Sunny",
        "2": "Partly Cloudy", 
        "3": "Cloudy",
        "4": "Overcast",
        "5": "Foggy",
        "6": "Light Rain",
        "7": "Rain",
        "8": "Heavy Rain",
        "9": "Snow",
        "10": "Thunder"
    }
    
    # Weather
    if "weather" in env and env["weather"]:
        weather_code = str(env["weather"])
        weather_desc = weather_conditions.get(weather_code, f"Unknown ({weather_code})")
        lines.append(f"Weather: {weather_desc}")
    
    # Temperature
    temp = env.get("temperature")
    if temp:
        try:
            # Check if it has °C marker
            if "\u00b0C" in temp:
                temp_val = float(temp.replace("\u00b0C", ""))
                temp_f = temp_val * 9/5 + 32
            else:
                # Try to extract numeric value
                temp_val = float(''.join(c for c in temp if c.isdigit() or c == '.'))
                # Assume Celsius if not specified
                temp_f = temp_val * 9/5 + 32 if env.get("temperature_unit") == "C" or "\u00b0C" in temp else temp_val
            
            lines.append(f"Temperature: {temp_f:.1f}°F")
        except (ValueError, TypeError):
            # If parsing fails, show the raw value
            lines.append(f"Temperature: {temp}")
    
    # Humidity 
    humidity = env.get("humidity")
    if humidity:
        try:
            # Handle if it's already a string with % sign
            if isinstance(humidity, str) and "%" in humidity:
                lines.append(f"Humidity: {humidity}")
            else:
                lines.append(f"Humidity: {int(float(humidity))}%")
        except (ValueError, TypeError):
            lines.append(f"Humidity: {humidity}")
    
    # Wind - handle both old format (wind as string) and new format (wind_value + wind_unit)
    wind = env.get("wind")
    wind_value = env.get("wind_value")
    wind_unit = env.get("wind_unit")
    
    mph = None
    
    if wind_value and wind_unit:
        try:
            if wind_unit == "mph":
                mph = float(wind_value)
            elif wind_unit == "m/s":
                mph = float(wind_value) * 2.237  # Convert m/s to mph
        except (ValueError, TypeError):
            pass
    elif wind:
        try:
            if isinstance(wind, str) and wind.endswith("m/s"):
                ms = float(wind.rstrip("m/s"))
                mph = ms * 2.237
            elif isinstance(wind, str) and wind.endswith("mph"):
                mph = float(wind.rstrip("mph"))
        except (ValueError, TypeError):
            pass
    
    if mph is not None:
        # Add wind strength descriptor
        if mph < 1:
            strength = "Calm"
        elif mph < 4:
            strength = "Light Air"
        elif mph < 8:
            strength = "Light Breeze"
        elif mph < 13:
            strength = "Gentle Breeze"
        elif mph < 19:
            strength = "Moderate Breeze"
        elif mph < 25:
            strength = "Fresh Breeze"
        elif mph < 32:
            strength = "Strong Breeze"
        elif mph < 39:
            strength = "Near Gale"
        elif mph < 47:
            strength = "Gale"
        elif mph < 55:
            strength = "Strong Gale"
        elif mph < 64:
            strength = "Storm"
        elif mph < 73:
            strength = "Violent Storm"
        else:
            strength = "Hurricane"
        
        lines.append(f"Wind: {strength}, {mph:.1f} mph")
    elif wind:
        lines.append(f"Wind: {wind}")
    elif wind_value and wind_unit:
        lines.append(f"Wind: {wind_value} {wind_unit}")
            
    return lines or ["No environment data available"]

def format_american_odds(odds_value, market_type):
    """Format odds value for display with proper +/- prefix"""
    if not odds_value or odds_value == 0:
        return "N/A"
    
    try:
        # Handle string odds that already have +/- formatting
        if isinstance(odds_value, str):
            if odds_value.startswith(('+', '-')):
                return odds_value
            # Try to convert to number for formatting
            try:
                num_val = float(odds_value)
                if num_val > 0:
                    return f"+{int(num_val)}"
                else:
                    return str(int(num_val))
            except ValueError:
                return odds_value
        
        # Handle numeric odds
        odds_num = float(odds_value)
        if odds_num > 0:
            return f"+{int(odds_num)}"
        else:
            return str(int(odds_num))
    except (ValueError, TypeError):
        return str(odds_value)

def format_odds_display(formatted_odds):
    """
    Return perfectly aligned betting-odds rows:
       │ Market │ Col1    │ Col2    │ Col3   │ Stamp  │
    """
    rows = []
    label_map = {"ML":"ML:", "SPREAD":"Spread:", "Over/Under":"O/U:"}

    for market in ("ML", "SPREAD", "Over/Under"):
        entry = pick_best_entry(formatted_odds.get(market, []))
        if not entry:
            continue
            
        time = entry.get("time_of_match", entry.get("time", "0"))
        stamp = f"(@{time}')"
        lab = label_map[market]
        
        if market == "ML":
            home_odds = format_american_odds(entry.get('home_win', entry.get('home', 0)), market)
            draw_odds = format_american_odds(entry.get('draw', 0), market)
            away_odds = format_american_odds(entry.get('away_win', entry.get('away', 0)), market)
            
            rows.append((lab, f"Home: {home_odds}", f"Draw: {draw_odds}", f"Away: {away_odds}", stamp))
            
        elif market == "SPREAD":
            home_odds = format_american_odds(entry.get('home_win', entry.get('home', 0)), market)
            handicap = entry.get('handicap', 0)
            away_odds = format_american_odds(entry.get('away_win', entry.get('away', 0)), market)
            
            rows.append((lab, f"Home: {home_odds}", f"Hcap: {handicap}", f"Away: {away_odds}", stamp))
            
        else:  # Over/Under
            over_odds = format_american_odds(entry.get('over', 0), market)
            line = entry.get('handicap', entry.get('line', 0))
            under_odds = format_american_odds(entry.get('under', 0), market)
            
            rows.append((lab, f"Over: {over_odds}", f"Line: {line}", f"Under: {under_odds}", stamp))
    
    if not rows:
        return "No betting odds available"
    
    # Process each column element to extract labels and values for precise alignment
    processed_rows = []
    
    for market, col1, col2, col3, stamp in rows:
        # Extract label and value from each column
        col1_parts = col1.split(": ", 1)
        col2_parts = col2.split(": ", 1)
        col3_parts = col3.split(": ", 1)
        
        if len(col1_parts) == 2 and len(col2_parts) == 2 and len(col3_parts) == 2:
            # Labels
            col1_label = col1_parts[0] + ":"
            col2_label = col2_parts[0] + ":"
            col3_label = col3_parts[0] + ":"
            
            # Values
            col1_value = col1_parts[1]
            col2_value = col2_parts[1]
            col3_value = col3_parts[1]
            
            processed_rows.append((market, col1_label, col1_value, col2_label, col2_value, col3_label, col3_value, stamp))
    
    if not processed_rows:
        return "No betting odds available"
    
    # Calculate max widths for precise alignment
    market_width = max(len(row[0]) for row in processed_rows)
    col1_label_width = max(len(row[1]) for row in processed_rows)
    col1_value_width = max(len(row[2]) for row in processed_rows)
    col2_label_width = max(len(row[3]) for row in processed_rows)
    col2_value_width = max(len(row[4]) for row in processed_rows)
    col3_label_width = max(len(row[5]) for row in processed_rows)
    col3_value_width = max(len(row[6]) for row in processed_rows)
    stamp_width = max(len(row[7]) for row in processed_rows)
    
    # Format rows with precise alignment of numeric values
    lines = []
    for market, c1_label, c1_val, c2_label, c2_val, c3_label, c3_val, stamp in processed_rows:
        # Format with precise right-alignment of values for perfect odds alignment
        line = f"│ {market:<{market_width}} │ {c1_label:<{col1_label_width}} {c1_val:>{col1_value_width}} │ "
        line += f"{c2_label:<{col2_label_width}} {c2_val:>{col2_value_width}} │ "
        line += f"{c3_label:<{col3_label_width}} {c3_val:>{col3_value_width}} │ {stamp}"
        lines.append(line)
    
    return "\n".join(lines)

def summarize_environment(env_data):
    """Format environment data for display"""
    if not env_data:
        return ["No environment data available"]
    
    # Use environment_summary if available, otherwise format raw data
    if "environment_summary" in env_data and env_data["environment_summary"]:
        return env_data["environment_summary"]
    
    # Fallback to Step 5 style formatting for raw environment data
    return summarize_environment_step5_style(env_data)

def log_and_print(message):
    """Print message to console and log to file"""
    print(message)
    match_logger.info(message)
    # Force flush to ensure immediate writing
    for handler in match_logger.handlers:
        handler.flush()

def write_main_header(fetch_count, total_matches, generated_at, pipeline_time=None):
    """Write the main header for the fetch set"""
    current_time = get_eastern_time()
    
    # Center text within 80 character width
    log_and_print("\n" + "="*80)
    log_and_print(f"FOOTBALL BETTING DATA - SUMMARY FETCH: #{fetch_count}".center(80))
    log_and_print(f"Fetch Time: {current_time}".center(80))
    log_and_print(f"Total Matches: {total_matches}".center(80))
    if pipeline_time is not None:
        log_and_print(f"Pipeline Execution Time: {pipeline_time:.2f}s".center(80))
    log_and_print("="*80)

def write_main_footer(fetch_count, total_matches, generated_at, pipeline_time=None):
    """Write the main footer for the fetch set"""
    current_time = get_eastern_time()
    
    # Center text within 80 character width
    log_and_print("\n" + "="*80)
    log_and_print(f"END OF SUMMARY FETCH: #{fetch_count}".center(80))
    log_and_print(f"Fetch Time: {current_time}".center(80))
    log_and_print(f"Total Matches: {total_matches}".center(80))
    if pipeline_time is not None:
        log_and_print(f"Pipeline Execution Time: {pipeline_time:.2f}s".center(80))
    log_and_print("="*80)

def process_match(match, match_num, total_matches):
    """Process and display a single match with all details"""
    # Header with timestamp
    log_and_print("\n" + "="*80)
    log_and_print(f"MATCH {match_num} of {total_matches}".center(80))
    log_and_print(f"Fetched: {get_eastern_time()}".center(80))
    log_and_print(f"Match ID: {match.get('match_id', 'N/A')}".center(80))
    log_and_print(f"Competition ID: {match.get('competition_id', 'N/A')}".center(80))
    log_and_print("="*80)
    log_and_print("")  # Add spacing between header and competition info
    
    log_and_print(f"Competition: {match.get('competition')} ({match.get('country')})")
    log_and_print(f"Match: {match.get('home_team')} vs {match.get('away_team')}")
    
    # Score - parse from step5 format
    score = match.get("score", "N/A")
    log_and_print(f"Score: {score}")
    
    # Status - Use detailed description with status ID if available
    status_id = match.get("status_id")
    if status_id is not None:
        status_description = get_status_description(status_id)
        status = f"{status_description} (ID: {status_id})"
    else:
        status = match.get("status", "Unknown")
    log_and_print(f"Status: {status}")
    
    # Betting Odds
    log_and_print("\n--- MATCH BETTING ODDS ---")
    
    # Prepare odds data for the new formatter
    formatted_odds = {}
    
    # Full Time Result -> ML
    ftr = match.get("full_time_result", {})
    if ftr and isinstance(ftr, dict):
        formatted_odds["ML"] = {
            "home": ftr.get("home"),
            "draw": ftr.get("draw"),
            "away": ftr.get("away"),
            "time": ftr.get("time", "0")
        }
    
    # Spread
    spread = match.get("spread", {})
    if spread and isinstance(spread, dict):
        formatted_odds["SPREAD"] = {
            "home": spread.get("home"),
            "handicap": spread.get("handicap"),
            "away": spread.get("away"),
            "time": spread.get("time", "0")
        }
    
    # Over/Under
    ou = match.get("over_under", {})
    if ou and isinstance(ou, dict):
        # Get the first available line
        for line, data in ou.items():
            if isinstance(data, dict):
                formatted_odds["Over/Under"] = {
                    "over": data.get("over"),
                    "line": data.get("line", line),
                    "under": data.get("under"),
                    "time": data.get("time", "0")
                }
                break  # Use first available line
    
    # Display using the new formatter
    odds_display = format_odds_display(formatted_odds)
    log_and_print(odds_display)
    
    # Environment
    log_and_print("\n--- MATCH ENVIRONMENT ---")
    env_data = match.get("environment", {})
    for line in summarize_environment(env_data):
        log_and_print(line)

# Status priority mapping for sorting (lower number = higher priority) - Updated for official API
STATUS_PRIORITY = {
    2: 1,   # First half (most urgent)
    3: 2,   # Half-time 
    4: 3,   # Second half
    5: 4,   # Overtime
    7: 5,   # Penalty Shoot-out
    6: 6,   # Overtime (deprecated)
    1: 7,   # Not started
    8: 8,   # End
    9: 9,   # Delay
    10: 10, # Interrupt
    11: 11, # Cut in half
    12: 12, # Cancel
    13: 13, # To be determined
    0: 14,  # Abnormal (suggest hiding) - lowest priority
}

def sort_matches_by_priority(matches):
    """
    Sort matches by status priority and recency.
    Returns list of (match_id, match_data) tuples sorted by:
    1. Status priority (first half, half-time, second half, etc.)
    2. Match start time (most recent first within same status)
    """
    match_list = list(matches.items())
    
    def get_sort_key(match_item):
        match_id, match_data = match_item
        
        # Get status ID for priority (handle both dict and direct value)
        status = match_data.get('status', {})
        if isinstance(status, dict):
            status_id = status.get('id', 999)
        else:
            status_id = status if isinstance(status, int) else 999
            
        priority = STATUS_PRIORITY.get(status_id, 999)
        
        # Get match start time for secondary sort (negative for reverse chronological)
        start_time = match_data.get('start_time', 0)
        if start_time is None:
            start_time = 0
            
        return (priority, -start_time)  # Negative start_time for most recent first
    
    return sorted(match_list, key=get_sort_key)

def pretty_print_matches(pipeline_time=None):
    """Main function to load step1 data and display formatted matches"""
    print("Step 6: Starting pretty print match display...")
    print(f"Step 6: Received pipeline_time: {pipeline_time}")
    
    # Load step1 data directly
    if not STEP1_JSON.exists():
        print("Step 6: Error - step1.json not found")
        return None
        
    try:
        with open(STEP1_JSON, 'r') as f:
            step1_data = json.load(f)
    except Exception as e:
        print(f"Step 6: Error loading step1.json: {e}")
        return None
    
    # Extract live matches from step1 data
    live_matches = step1_data.get("live_matches", {}).get("results", [])
    match_details = step1_data.get("match_details", {})
    team_info = step1_data.get("team_info", {})
    competition_info = step1_data.get("competition_info", {})
    match_odds = step1_data.get("match_odds", {})  # Extract betting odds data
    generated_at = step1_data.get("timestamp", "Unknown")
    
    # Convert step1 data to step6 expected format using proper merging
    matches = {}
    for match in live_matches:
        match_id = match.get("id")
        if match_id:
            merged_match = merge_match_data_from_step1(match, match_details, match_odds, team_info, competition_info)
            matches[match_id] = merged_match
    
    total_matches = len(matches)
    fetch_count = get_daily_fetch_count()
    
    print(f"Step 6: Processing {total_matches} matches for display")
    print(f"Data generated at: {generated_at}")
    print(f"This is fetch #{fetch_count} for today")
    print(f"Step 6: About to write header with pipeline_time: {pipeline_time}")
    
    # Write main header to log
    write_main_header(fetch_count, total_matches, generated_at, pipeline_time)
    
    # Sort matches by status priority and recency
    sorted_matches = sort_matches_by_priority(matches)
    
    # Process each match in sorted order with status group headers
    match_num = 1
    current_status = None
    
    for match_id, match_data in sorted_matches:
        # Check if we need a new status group header
        status = match_data.get('status', {})
        if isinstance(status, dict):
            match_status = status.get('id')
            status_desc = status.get('description', '')
        else:
            match_status = status if isinstance(status, int) else None
            status_desc = ''
            
        if match_status != current_status:
            current_status = match_status
            write_status_group_header(match_status, status_desc)
        
        process_match(match_data, match_num, total_matches)
        match_num += 1
        
        # Add separator between matches
        if match_num <= total_matches:
            print("\n" + "-"*80)
    
    print(f"\nStep 6: Successfully displayed {total_matches} matches")
    
    # Write status summary before footer
    write_status_summary(matches)
    
    # Write main footer to log
    write_main_footer(fetch_count, total_matches, generated_at, pipeline_time)
    
    # Ensure all log data is written to file
    for handler in match_logger.handlers:
        handler.flush()
    
    return True

def write_status_group_header(status_id, status_description):
    """Write a status group header to separate matches by status"""
    status_groups = {
        0: "❌ ABNORMAL (SUGGEST HIDING)",
        1: "⏰ NOT STARTED",
        2: "🔴 LIVE - FIRST HALF",
        3: "⏸️  HALF-TIME", 
        4: "🔴 LIVE - SECOND HALF",
        5: "⚡ OVERTIME",
        6: "⚡ OVERTIME (DEPRECATED)",
        7: "🥅 PENALTY SHOOT-OUT",
        8: "✅ END",
        9: "⏰ DELAY",
        10: "� INTERRUPT",
        11: "❌ CUT IN HALF",
        12: "🚫 CANCEL",
        13: "📅 TO BE DETERMINED"
    }
    
    group_name = status_groups.get(status_id, f"STATUS {status_id}")
    
    header = f"\n{'='*80}\n"
    header += f"                    {group_name}\n"
    header += f"{'='*80}\n"
    
    match_logger.info(header)

def count_matches_by_status(matches):
    """Count matches by status ID and return formatted summary"""
    # Create reverse mapping from description to ID - Official API mapping
    status_map = {
        "Abnormal (suggest hiding)": 0,
        "Not started": 1,
        "First half": 2,
        "Half-time": 3,
        "Second half": 4,
        "Overtime": 5,
        "Overtime (deprecated)": 6,
        "Penalty Shoot-out": 7,
        "End": 8,
        "Delay": 9,
        "Interrupt": 10,
        "Cut in half": 11,
        "Cancel": 12,
        "To be determined": 13
    }
    
    status_counts = {}
    
    for match_id, match_data in matches.items():
        # Extract status from match data - handle both string and dict formats
        status_value = match_data.get('status', '')
        
        if isinstance(status_value, dict):
            # New format: status is a dict with 'description' field
            status_str = status_value.get('description', '')
        else:
            # Old format: status is a string
            status_str = status_value
            
        status_id = status_map.get(status_str)
            
        if status_id is not None:
            status_counts[status_id] = status_counts.get(status_id, 0) + 1
    
    return status_counts

def write_status_summary(matches):
    """Write a summary of match counts by status to the log"""
    status_counts = count_matches_by_status(matches)
    
    if not status_counts:
        return
    
    # Calculate total matches
    total_matches = sum(status_counts.values())
    
    # Sort by status ID for consistent display
    sorted_statuses = sorted(status_counts.items())
    
    log_and_print("\n" + "="*80)
    log_and_print("MATCH STATUS SUMMARY".center(80))
    log_and_print("="*80)
    log_and_print(f"Total Matches: {total_matches}")
    log_and_print("-"*80)
    
    for status_id, count in sorted_statuses:
        status_desc = get_status_description(status_id)
        log_and_print(f"{status_desc} (ID: {status_id}): {count} Match{'es' if count != 1 else ''}")
    
    log_and_print("="*80)

def merge_match_data_from_step1(match, match_details, match_odds, team_info, competition_info):
    """
    Merge raw step1 data like Steps 2-5 do it.
    This replicates the merging logic from step2.py extract_summary_fields()
    """
    match_id = match.get("id")
    
    # Get match details
    match_detail = {}
    if match_id in match_details:
        detail_wrap = match_details[match_id]
        if isinstance(detail_wrap, dict):
            results = detail_wrap.get("results") or detail_wrap.get("result") or []
            if isinstance(results, list) and results:
                match_detail = results[0]
    
    # Get team names from team_info
    home_team_name = "Unknown Home Team"
    away_team_name = "Unknown Away Team"
    
    home_team_id = match_detail.get("home_team_id") or match.get("home_team_id")
    away_team_id = match_detail.get("away_team_id") or match.get("away_team_id")
    
    if home_team_id and str(home_team_id) in team_info:
        team_data = team_info[str(home_team_id)]
        if isinstance(team_data, dict):
            results = team_data.get("results") or team_data.get("result") or []
            if isinstance(results, list) and results:
                home_team_name = results[0].get("name", "Unknown Home Team")
    
    if away_team_id and str(away_team_id) in team_info:
        team_data = team_info[str(away_team_id)]
        if isinstance(team_data, dict):
            results = team_data.get("results") or team_data.get("result") or []
            if isinstance(results, list) and results:
                away_team_name = results[0].get("name", "Unknown Away Team")
    
    # Get competition name
    competition_name = "Unknown Competition"
    country = "Unknown Country"
    comp_id = match_detail.get("competition_id") or match.get("competition_id")
    if comp_id and str(comp_id) in competition_info:
        comp_data = competition_info[str(comp_id)]
        if isinstance(comp_data, dict):
            results = comp_data.get("results") or comp_data.get("result") or []
            if isinstance(results, list) and results:
                comp_result = results[0]
                competition_name = comp_result.get("name", "Unknown Competition")
                country = comp_result.get("country", "Unknown Country")
    
    # Extract scores like step2 does
    home_live = home_ht = away_live = away_ht = 0
    score_data = match.get("score", [])
    if isinstance(score_data, list) and len(score_data) > 3:
        hs, as_ = score_data[2], score_data[3]
        if isinstance(hs, list) and len(hs) > 1:
            home_live, home_ht = hs[0], hs[1]
        if isinstance(as_, list) and len(as_) > 1:
            away_live, away_ht = as_[0], as_[1]
    
    # Get status
    status_id = None
    if "status_id" in match:
        status_id = match["status_id"]
    elif isinstance(score_data, list) and len(score_data) > 1:
        status_id = score_data[1]
    
    # Extract betting odds from match_odds like step2 does
    betting_odds = {}
    if match_id in match_odds:
        odds_data = match_odds[match_id]
        if isinstance(odds_data, dict) and "results" in odds_data:
            odds_results = odds_data["results"]
            
            # Process different market types
            for market_id, market_data in odds_results.items():
                if isinstance(market_data, dict):
                    # Check for different odds types (asia, eu, bs, cr)
                    for odds_type in ["eu", "asia", "bs"]:
                        if odds_type in market_data and market_data[odds_type]:
                            odds_entries = market_data[odds_type]
                            if isinstance(odds_entries, list) and odds_entries:
                                # Filter by time like step2 does (3-6 minute window)
                                filtered_odds = filter_odds_by_time(odds_entries)
                                if filtered_odds:
                                    latest_odds = filtered_odds[0]
                                    
                                    # Convert to step2/step5 format based on market type
                                    if market_id == "1" and odds_type == "eu":  # Full Time Result (1x2)
                                        betting_odds["full_time_result"] = {
                                            "home": latest_odds[2] if len(latest_odds) > 2 else None,
                                            "draw": latest_odds[3] if len(latest_odds) > 3 else None,
                                            "away": latest_odds[4] if len(latest_odds) > 4 else None,
                                            "time": latest_odds[1] if len(latest_odds) > 1 else "0"
                                        }
                                    elif market_id == "2" and odds_type == "asia":  # Asian Handicap
                                        betting_odds["spread"] = {
                                            "home": latest_odds[2] if len(latest_odds) > 2 else None,
                                            "handicap": latest_odds[3] if len(latest_odds) > 3 else None,
                                            "away": latest_odds[4] if len(latest_odds) > 4 else None,
                                            "time": latest_odds[1] if len(latest_odds) > 1 else "0"
                                        }
                                    elif market_id == "3" and odds_type == "bs":  # Over/Under
                                        line = latest_odds[3] if len(latest_odds) > 3 else "0"
                                        betting_odds["over_under"] = {
                                            line: {
                                                "over": latest_odds[2] if len(latest_odds) > 2 else None,
                                                "line": line,
                                                "under": latest_odds[4] if len(latest_odds) > 4 else None,
                                                "time": latest_odds[1] if len(latest_odds) > 1 else "0"
                                            }
                                        }
                                        betting_odds["primary_over_under"] = betting_odds["over_under"][line]
    
    # Extract environment data like step2 does
    environment_data = {}
    if "environment" in match_detail:
        env = match_detail["environment"]
        if isinstance(env, dict):
            environment_data = process_environment_like_step2(env)
    
    # Create merged match data in step5 format
    merged_match = {
        "match_id": match_id,
        "competition_id": comp_id,
        "competition": competition_name,
        "country": country,
        "home_team": home_team_name,
        "away_team": away_team_name,
        "score": f"{home_live} - {away_live} (HT: {home_ht} - {away_ht})",
        "status": get_status_description(status_id),
        "status_id": status_id,
        "start_time": match_detail.get("start_time"),
        "venue": match_detail.get("venue_id"),
        "environment": environment_data
    }
    
    # Add converted betting odds
    if "full_time_result" in betting_odds:
        ftr = betting_odds["full_time_result"]
        merged_match["full_time_result"] = {
            "home": decimal_to_american(ftr.get("home")) if ftr.get("home") else None,
            "draw": decimal_to_american(ftr.get("draw")) if ftr.get("draw") else None,
            "away": decimal_to_american(ftr.get("away")) if ftr.get("away") else None,
            "time": ftr.get("time", "0")
        }
    
    if "spread" in betting_odds:
        spread = betting_odds["spread"]
        merged_match["spread"] = {
            "handicap": spread.get("handicap"),
            "home": hk_to_american(spread.get("home")) if spread.get("home") else None,
            "away": hk_to_american(spread.get("away")) if spread.get("away") else None,
            "time": spread.get("time", "0")
        }
    
    if "primary_over_under" in betting_odds:
        ou = betting_odds["primary_over_under"]
        line = ou.get("line", "0")
        merged_match["over_under"] = {
            line: {
                "line": float(line) if str(line).replace(".", "").isdigit() else 0,
                "over": hk_to_american(ou.get("over")) if ou.get("over") else None,
                "under": hk_to_american(ou.get("under")) if ou.get("under") else None,
                "time": ou.get("time", "0")
            }
        }
    
    return merged_match

def filter_odds_by_time(odds_entries):
    """Filter odds entries by time window like step2 does (3-6 minute window)"""
    import re
    
    def _safe_minute(v):
        if v is None:
            return None
        m = re.match(r"(\d+)", str(v))
        return int(m.group(1)) if m else None
    
    # Extract minute from each entry
    pts = [(_safe_minute(ent[1]), ent) for ent in odds_entries if isinstance(ent, (list, tuple)) and len(ent) > 1]
    pts = [(m, e) for m, e in pts if m is not None]
    
    # Prefer entries in 3-6 minute window
    in_window = [e for m, e in pts if 3 <= m <= 6]
    if in_window:
        return in_window
    
    # Fall back to entries under 10 minutes, closest to 4.5
    under_ten = [(m, e) for m, e in pts if m < 10]
    if under_ten:
        return [min(under_ten, key=lambda t: abs(t[0] - 4.5))[1]]
    
    return []

def process_environment_like_step2(env):
    """Process environment data like step2 does"""
    import re
    
    parsed = {"raw": env}
    
    # Weather code mapping
    wc = env.get("weather")
    parsed["weather"] = int(wc) if isinstance(wc, str) and wc.isdigit() else wc
    desc = {1:"Sunny",2:"Partly Cloudy",3:"Cloudy",4:"Overcast",5:"Foggy",6:"Light Rain",7:"Rain",8:"Heavy Rain",9:"Snow",10:"Thunder"}
    parsed["weather_description"] = desc.get(parsed["weather"], "Unknown")

    # Process temperature, wind, pressure, humidity
    for key in ("temperature","wind","pressure","humidity"): 
        val = env.get(key)
        parsed[key] = val
        m = re.match(r"([\d.-]+)\s*([^\d]*)", str(val)) if val else None
        num, unit = (float(m.group(1)), m.group(2).strip()) if m else (None, None)
        parsed[f"{key}_value"] = num
        parsed[f"{key}_unit"] = unit

    # Convert wind to mph if needed
    wv = parsed.get("wind_value") or 0
    mph = wv*2.237 if "m/s" in str(env.get("wind","")).lower() else wv
    
    # Wind classification
    if mph < 1: wd = "Calm"
    elif mph <= 3: wd = "Light Air" 
    elif mph <= 7: wd = "Light Breeze"
    elif mph <= 12: wd = "Gentle Breeze"
    elif mph <= 18: wd = "Moderate Breeze"
    elif mph <= 24: wd = "Fresh Breeze"
    elif mph <= 31: wd = "Strong Breeze"
    elif mph <= 38: wd = "Near Gale"
    elif mph <= 46: wd = "Gale"
    elif mph <= 54: wd = "Strong Gale"
    elif mph <= 63: wd = "Storm"
    elif mph <= 72: wd = "Violent Storm"
    else: wd = "Hurricane"
    
    parsed["wind_description"] = wd
    parsed["wind_value"] = mph
    parsed["wind_unit"] = "mph"
    
    # Temperature conversion
    temp_celsius = parsed.get("temperature_value")
    if temp_celsius is not None:
        temp_fahrenheit = (temp_celsius * 9/5) + 32
        parsed["temperature_fahrenheit"] = temp_fahrenheit
    
    # Create environment summary like step5 does
    summary_lines = []
    if temp_celsius is not None:
        temp_f = (temp_celsius * 9/5) + 32
        summary_lines.append(f"Temperature: {temp_f:.1f}°F")
    
    if mph > 0:
        summary_lines.append(f"Wind: {wd}, {mph:.1f} mph")
    
    if parsed.get("pressure"):
        summary_lines.append(f"Pressure: {parsed['pressure']}")
    
    if parsed.get("humidity"):
        summary_lines.append(f"Humidity: {parsed['humidity']}")
    
    parsed["environment_summary"] = summary_lines
    
    return parsed
    """Convert step1 data structure to the format expected by step6"""
    converted_matches = {}
    
    # Status mapping
    status_desc_map = {
        0: "Abnormal", 1: "Not started", 2: "First half", 3: "Half-time",
        4: "Second half", 5: "Overtime", 6: "Overtime (deprecated)",
        7: "Penalty Shoot-out", 8: "End", 9: "Delay", 10: "Interrupt",
        11: "Cut in half", 12: "Cancel", 13: "To be determined"
    }
    
    for match in live_matches:
        match_id = match.get("id")
        if not match_id:
            continue
            
        # Get status from score array or status_id field
        status_id = None
        if "status_id" in match:
            status_id = match["status_id"]
        elif "score" in match and isinstance(match["score"], list) and len(match["score"]) > 1:
            status_id = match["score"][1]
        
        # Get match details
        match_detail = {}
        if match_id in match_details:
            detail_wrap = match_details[match_id]
            if isinstance(detail_wrap, dict):
                results = detail_wrap.get("results") or detail_wrap.get("result") or []
                if isinstance(results, list) and results:
                    match_detail = results[0]
        
        # Get team names
        home_team_name = "Unknown Home Team"
        away_team_name = "Unknown Away Team"
        
        home_team_id = match_detail.get("home_team_id") or match.get("home_team_id")
        away_team_id = match_detail.get("away_team_id") or match.get("away_team_id")
        
        if home_team_id and str(home_team_id) in team_info:
            team_data = team_info[str(home_team_id)]
            if isinstance(team_data, dict):
                results = team_data.get("results") or team_data.get("result") or []
                if isinstance(results, list) and results:
                    home_team_name = results[0].get("name", "Unknown Home Team")
        
        if away_team_id and str(away_team_id) in team_info:
            team_data = team_info[str(away_team_id)]
            if isinstance(team_data, dict):
                results = team_data.get("results") or team_data.get("result") or []
                if isinstance(results, list) and results:
                    away_team_name = results[0].get("name", "Unknown Away Team")
        
        # Get current score
        current_score = [0, 0]
        if "score" in match and isinstance(match["score"], list) and len(match["score"]) >= 4:
            home_score = match["score"][2]
            away_score = match["score"][3]
            if isinstance(home_score, list) and isinstance(away_score, list):
                current_score = [
                    home_score[0] if home_score else 0,
                    away_score[0] if away_score else 0
                ]
        
        # Get competition name
        competition_name = "Unknown Competition"
        comp_id = match_detail.get("competition_id") or match.get("competition_id")
        if comp_id and str(comp_id) in competition_info:
            comp_data = competition_info[str(comp_id)]
            if isinstance(comp_data, dict):
                results = comp_data.get("results") or comp_data.get("result") or []
                if isinstance(results, list) and results:
                    competition_name = results[0].get("name", "Unknown Competition")
        
        # Extract betting odds data using Step 5 logic
        betting_odds = {}
        if match_id in match_odds:
            odds_data = match_odds[match_id]
            if isinstance(odds_data, dict) and "results" in odds_data:
                odds_results = odds_data["results"]
                
                # Extract different market types from the odds data
                for market_id, market_data in odds_results.items():
                    if isinstance(market_data, dict):
                        # Check for different odds types (asia, eu, bs, cr)
                        for odds_type in ["asia", "eu", "bs", "cr"]:
                            if odds_type in market_data and market_data[odds_type]:
                                odds_entries = market_data[odds_type]
                                if isinstance(odds_entries, list) and odds_entries:
                                    # Take the most recent odds entry (first in the list)
                                    latest_odds = odds_entries[0]
                                    
                                    # Convert to step6 format based on market type
                                    if market_id == "1":  # Full Time Result (1x2) - DECIMAL format
                                        betting_odds["full_time_result"] = {
                                            "home": decimal_to_american(latest_odds[2]) if len(latest_odds) > 2 else None,
                                            "draw": decimal_to_american(latest_odds[3]) if len(latest_odds) > 3 else None,
                                            "away": decimal_to_american(latest_odds[4]) if len(latest_odds) > 4 else None,
                                            "time": str(latest_odds[0]) if len(latest_odds) > 0 else "0"
                                        }
                                    elif market_id == "2":  # Asian Handicap - HONG KONG format
                                        betting_odds["spread"] = {
                                            "home": hk_to_american(latest_odds[2]) if len(latest_odds) > 2 else None,
                                            "handicap": latest_odds[1] if len(latest_odds) > 1 else None,
                                            "away": hk_to_american(latest_odds[4]) if len(latest_odds) > 4 else None,
                                            "time": str(latest_odds[0]) if len(latest_odds) > 0 else "0"
                                        }
                                    elif market_id == "3":  # Over/Under - HONG KONG format
                                        line = latest_odds[1] if len(latest_odds) > 1 else "0"
                                        betting_odds["over_under"] = {
                                            line: {
                                                "over": hk_to_american(latest_odds[2]) if len(latest_odds) > 2 else None,
                                                "line": line,
                                                "under": hk_to_american(latest_odds[4]) if len(latest_odds) > 4 else None,
                                                "time": str(latest_odds[0]) if len(latest_odds) > 0 else "0"
                                            }
                                        }
                                break  # Use first available odds type
        
        # Extract and format environment data from match details using Step 5 logic
        environment_data = {}
        environment_summary = []
        if "environment" in match_detail:
            env = match_detail["environment"]
            if isinstance(env, dict):
                # Store raw environment data
                environment_data = env.copy()
                
                # Convert wind speed from m/s to MPH and add Beaufort scale description
                if "wind" in env:
                    try:
                        if isinstance(env["wind"], str) and env["wind"].endswith("m/s"):
                            wind_ms = float(env["wind"].rstrip("m/s"))
                            wind_mph = wind_ms * 2.237  # Convert m/s to mph
                            environment_data["wind_value"] = round(wind_mph, 1)
                            environment_data["wind_unit"] = "mph"
                            
                            # Add wind description based on Beaufort scale
                            if wind_mph < 1:
                                environment_data["wind_description"] = "Calm"
                            elif wind_mph < 4:
                                environment_data["wind_description"] = "Light Air"
                            elif wind_mph < 8:
                                environment_data["wind_description"] = "Light Breeze"
                            elif wind_mph < 13:
                                environment_data["wind_description"] = "Gentle Breeze"
                            elif wind_mph < 19:
                                environment_data["wind_description"] = "Moderate Breeze"
                            elif wind_mph < 25:
                                environment_data["wind_description"] = "Fresh Breeze"
                            elif wind_mph < 32:
                                environment_data["wind_description"] = "Strong Breeze"
                            elif wind_mph < 39:
                                environment_data["wind_description"] = "Near Gale"
                            elif wind_mph < 47:
                                environment_data["wind_description"] = "Gale"
                            elif wind_mph < 55:
                                environment_data["wind_description"] = "Strong Gale"
                            elif wind_mph < 64:
                                environment_data["wind_description"] = "Storm"
                            elif wind_mph < 73:
                                environment_data["wind_description"] = "Violent Storm"
                            else:
                                environment_data["wind_description"] = "Hurricane"
                    except (ValueError, TypeError):
                        pass  # Keep original values if conversion fails
                
                # Generate environment summary using Step 5 logic
                environment_summary = summarize_environment_step5_style(environment_data)
        
        # Create match data in step6 expected format
        converted_matches[match_id] = {
            "match_id": match_id,
            "home_team": home_team_name,
            "away_team": away_team_name,
            "score": current_score,
            "competition": competition_name,
            "status": {
                "id": status_id,
                "description": status_desc_map.get(status_id, f"Unknown Status (ID: {status_id})")
            },
            "full_time_result": betting_odds.get("full_time_result", {}),
            "spread": betting_odds.get("spread", {}),
            "over_under": betting_odds.get("over_under", {}),
            "environment": environment_data,
            "environment_summary": environment_summary,
            "raw_match_data": match,
            "raw_match_details": match_detail
        }
    
    return converted_matches

if __name__ == "__main__":
    pretty_print_matches()
