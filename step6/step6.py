#!/usr/bin/env python3
"""
Step 6 - Pretty Print Match Display
Final step to format and display human-readable match summaries

This module processes Step 5 JSON data and:
1. Formats match information in a readable format
2. Displays betting odds in organized tables
3. Shows environment data with proper formatting
4. Provides comprehensive match summaries for display
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
STEP5_JSON = BASE_DIR.parent / "step5" / "step5.json"

# Setup logger
def setup_logger():
    """Setup logger to write formatted match summaries to file"""
    log_file = BASE_DIR / "step6_matches.log"
    
    # Create logger
    logger = logging.getLogger('step6_matches')
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create file handler
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
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
    
    lines = []
    
    # Use environment_summary if available, otherwise format raw data
    if "environment_summary" in env_data and env_data["environment_summary"]:
        return env_data["environment_summary"]
    
    # Fallback to raw environment data formatting
    if "weather_description" in env_data:
        lines.append(f"Weather: {env_data['weather_description']}")
    
    if "temperature" in env_data:
        temp_value = env_data['temperature']
        if temp_value and temp_value != "None":
            try:
                # Extract numeric value from temperature string (e.g., "16°C" -> 16)
                temp_celsius = float(str(temp_value).replace('°C', '').strip())
                # Convert Celsius to Fahrenheit: F = (C × 9/5) + 32
                temp_fahrenheit = (temp_celsius * 9/5) + 32
                lines.append(f"Temperature: {temp_fahrenheit:.1f}°F")
            except (ValueError, AttributeError):
                lines.append(f"Temperature: {temp_value}")
        else:
            lines.append(f"Temperature: None")
    
    if "wind_description" in env_data and "wind_value" in env_data:
        wind_desc = env_data["wind_description"]
        wind_val = env_data["wind_value"]
        wind_unit = env_data.get("wind_unit", "")
        lines.append(f"Wind: {wind_desc}, {wind_val} {wind_unit}")
    
    return lines if lines else ["No environment data available"]

def log_and_print(message):
    """Print message to console and log to file"""
    print(message)
    match_logger.info(message)

def write_main_header(fetch_count, total_matches, generated_at):
    """Write the main header for the fetch set"""
    current_time = get_eastern_time()
    
    # Center text within 80 character width
    log_and_print("\n" + "="*80)
    log_and_print(f"FOOTBALL BETTING DATA - SUMMARY FETCH: #{fetch_count}".center(80))
    log_and_print(f"Fetch Time: {current_time}".center(80))
    log_and_print(f"Total Matches: {total_matches}".center(80))
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

def pretty_print_matches():
    """Main function to load step5 data and display formatted matches"""
    print("Step 6: Starting pretty print match display...")
    
    # Load step5 data
    if not STEP5_JSON.exists():
        print("Step 6: Error - step5.json not found")
        return None
        
    try:
        with open(STEP5_JSON, 'r') as f:
            step5_data = json.load(f)
    except Exception as e:
        print(f"Step 6: Error loading step5.json: {e}")
        return None
    
    # Get the latest history entry
    if "history" in step5_data and step5_data["history"]:
        latest_data = step5_data["history"][-1]
        matches = latest_data.get("matches", {})
        generated_at = latest_data.get("generated_at", "Unknown")
    else:
        matches = step5_data.get("matches", {})
        generated_at = step5_data.get("generated_at", "Unknown")
    
    total_matches = len(matches)
    fetch_count = get_daily_fetch_count()
    
    print(f"Step 6: Processing {total_matches} matches for display")
    print(f"Data generated at: {generated_at}")
    print(f"This is fetch #{fetch_count} for today")
    
    # Write main header to log
    write_main_header(fetch_count, total_matches, generated_at)
    
    # Process each match
    match_num = 1
    for match_id, match_data in matches.items():
        process_match(match_data, match_num, total_matches)
        match_num += 1
        
        # Add separator between matches
        if match_num <= total_matches:
            print("\n" + "-"*80)
    
    print(f"\nStep 6: Successfully displayed {total_matches} matches")
    return True

if __name__ == "__main__":
    pretty_print_matches()
