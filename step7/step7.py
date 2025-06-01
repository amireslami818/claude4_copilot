#!/usr/bin/env python3
"""
Step 7 - Status Filter & Display (Statuses 2–7)
Filters matches whose status_id is one of {2,3,4,5,6,7}
Writes human-readable match summaries to step7_matches.log
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import fcntl

# Use the same timezone as other modules
TZ = ZoneInfo("America/New_York")

# Path constants - using absolute paths to avoid working directory issues
BASE_DIR = Path(__file__).resolve().parent  # step7 directory for logs
STEP5_JSON = Path(__file__).resolve().parent.parent / "step5" / "step5.json"  # Go up to Football_bot, then to step5

# The new status set: 2,3,4,5,6,7 (First half, Half-time, Second half, Overtime, Overtime (deprecated), Penalty Shoot-out)
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
    """Map numeric status_id → human‐readable description - Official API mapping."""
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

def sort_matches_by_competition_and_time(matches: dict) -> dict:
    """
    Group matches by competition and sort within each competition by 
    most recently started (Status 2) to longest running (Status 7).
    
    Returns dict: {competition: [list of (match_id, match_data) tuples]}
    """
    # Group matches by competition
    competition_groups = {}
    
    for match_id, match_data in matches.items():
        comp = match_data.get("competition", "Unknown Competition")
        # PRIMARY: Use the country field from JSON data
        country = match_data.get("country", "Unknown") or "Unknown"  # Handle None values
        
        # FALLBACK: If country is Unknown/None, try to infer from team names as backup
        if country in ["Unknown", "None", None]:
            country = infer_country_from_teams(match_data)
        
        # Create a sorting key that includes country for alphabetization
        # but still group by the original competition name
        if comp not in competition_groups:
            competition_groups[comp] = {
                'country': country,
                'matches': []
            }
        competition_groups[comp]['matches'].append((match_id, match_data))
    
    # Sort each competition group by status (most recent to longest running)
    # Status 2 (First half) = most recent, Status 7 (Penalty) = longest running
    status_order = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6}
    
    for comp in competition_groups:
        competition_groups[comp]['matches'].sort(key=lambda item: (
            status_order.get(item[1].get("status_id", 99), 99),  # Status progression
            item[1].get("match_id", "")  # Stabilize sort
        ))
    
    # Sort competitions alphabetically by country first, then by competition name
    sorted_competitions = sorted(
        competition_groups.items(),
        key=lambda item: (item[1]['country'] or "Unknown", item[0])  # Sort by country first, then competition
    )
    
    # Convert back to the expected format: {competition: [matches]}
    result = {}
    for comp, data in sorted_competitions:
        result[comp] = data['matches']
    
    return result

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

def write_main_footer(fetch_count: int, total: int, generated_at: str, pipeline_time=None, matches=None):
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
    
    # Add status summary at the end if matches data is available
    if matches and total > 0:
        # Count matches by status
        status_counts = {}
        for match_data in matches.values():
            status_id = match_data.get("status_id")
            if status_id in STATUS_FILTER:
                status_counts[status_id] = status_counts.get(status_id, 0) + 1
        
        # Write status summary footer
        summary_footer = (
            f"\nSTEP 7 - STATUS SUMMARY\n"
            f"{'='*60}\n"
        )
        
        # Write simple status lines
        for status_id in sorted(status_counts.keys()):
            count = status_counts[status_id]
            desc = get_status_description(status_id)
            summary_footer += f"{desc} (ID: {status_id}): {count}\n"
        
        summary_footer += f"Total: {total}\n"
        summary_footer += f"{'='*60}\n"
        
        match_logger.info(summary_footer)
    
    for h in match_logger.handlers:
        h.flush()

def write_competition_group_header(competition: str, country: str, match_count: int):
    """Write a competition‐level header with match count to both console + log."""
    # Center the competition info within 100-character borders
    comp_line = f"🏆 {competition.upper()}"
    info_line = f"📍 {country} | 📊 {match_count} Matches"
    
    header = (
        f"\n{'='*100}\n"
        f"{'='*100}\n"
        f"{comp_line.center(100)}\n"
        f"{info_line.center(100)}\n"
        f"{'='*100}\n"
        f"{'='*100}\n"
    )
    log_and_print(header)



def format_american_odds(odds_value):
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
        return str(odds_value) if odds_value else "N/A"

def format_betting_odds(match_data: dict) -> str:
    """Format betting odds display for ML, Spread, and O/U"""
    odds_lines = []
    
    # Money Line (ML) odds
    full_time = match_data.get("full_time_result")
    if full_time and isinstance(full_time, dict):
        home_ml = format_american_odds(full_time.get('home'))
        draw_ml = format_american_odds(full_time.get('draw'))
        away_ml = format_american_odds(full_time.get('away'))
        time_stamp = full_time.get('time', '0')
        odds_lines.append(f"│ ML:     │ Home: {home_ml:>6} │ Draw: {draw_ml:>6} │ Away: {away_ml:>7} │ (@{time_stamp}')")
    
    # Spread odds
    spread = match_data.get("spread")
    if spread and isinstance(spread, dict):
        home_spread = format_american_odds(spread.get('home'))
        handicap = spread.get('handicap', 0)
        away_spread = format_american_odds(spread.get('away'))
        time_stamp = spread.get('time', '0')
        odds_lines.append(f"│ Spread: │ Home: {home_spread:>6} │ Hcap: {handicap:>6} │ Away: {away_spread:>7} │ (@{time_stamp}')")
    
    # Over/Under odds
    over_under = match_data.get("over_under")
    if over_under and isinstance(over_under, dict):
        # Get the first (and typically only) line
        for line_value, line_data in over_under.items():
            if isinstance(line_data, dict):
                over_odds = format_american_odds(line_data.get('over'))
                line_num = line_data.get('line', line_value)
                under_odds = format_american_odds(line_data.get('under'))
                time_stamp = line_data.get('time', '0')
                odds_lines.append(f"│ O/U:    │ Over: {over_odds:>6} │ Line: {line_num:>6} │ Under: {under_odds:>6} │ (@{time_stamp}')")
                break  # Only show first line
    
    if not odds_lines:
        return "No betting odds available"
    
    return "\n".join(odds_lines)

def format_environment_data(match_data: dict) -> str:
    """Format match environment data"""
    environment = match_data.get("environment", {})
    if not environment:
        return "No environment data available"
    
    # Extract environment data with safe defaults
    weather = environment.get("weather_description", "Unknown")
    temp_c = environment.get("temperature_value", 0)
    temp_unit = environment.get("temperature_unit") or "°C"
    wind_desc = environment.get("wind_description", "Unknown")
    wind_value = environment.get("wind_value", 0)
    wind_unit = environment.get("wind_unit") or "m/s"
    
    # Convert temperature to Fahrenheit if needed
    if temp_unit == "°C" and temp_c:
        temp_f = (temp_c * 9/5) + 32
        temp_display = f"{temp_f:.1f}°F"
    else:
        temp_display = f"{temp_c}°{temp_unit.replace('°', '') if temp_unit else 'C'}"
    
    # Convert wind to mph if needed
    if wind_unit == "m/s" and wind_value:
        wind_mph = wind_value * 2.237
        wind_display = f"{wind_desc}, {wind_mph:.1f} mph"
    else:
        wind_display = f"{wind_desc}, {wind_value} {wind_unit}"
    
    return f"Weather: {weather}\nTemperature: {temp_display}\nWind: {wind_display}"

def infer_country_from_teams(match_data):
    """
    FALLBACK ONLY: Infer country from team names when the country field is None/missing.
    This function is only used when the primary JSON country field is not available.
    
    Args:
        match_data: Match dictionary containing team names
        
    Returns:
        str: Inferred country name or "International" for mixed/unknown countries
    """
    home_team = match_data.get('home_team', '').lower()
    away_team = match_data.get('away_team', '').lower()
    competition = match_data.get('competition', '').lower()
    
    # Country indicators in team names
    country_indicators = {
        'australia': ['australia', 'aussie', 'socceroos', 'matildas'],
        'argentina': ['argentina', 'boca', 'river plate', 'racing club'],
        'brazil': ['brazil', 'sao paulo', 'flamengo', 'corinthians', 'palmeiras'],
        'england': ['england', 'manchester', 'liverpool', 'chelsea', 'arsenal', 'tottenham'],
        'spain': ['spain', 'real madrid', 'barcelona', 'atletico', 'sevilla', 'valencia'],
        'germany': ['germany', 'bayern', 'borussia', 'schalke', 'hamburg'],
        'france': ['france', 'psg', 'marseille', 'lyon', 'monaco', 'saint-etienne'],
        'italy': ['italy', 'juventus', 'inter', 'milan', 'roma', 'napoli', 'lazio'],
        'netherlands': ['netherlands', 'ajax', 'psv', 'feyenoord'],
        'portugal': ['portugal', 'porto', 'benfica', 'sporting'],
        'mexico': ['mexico', 'america', 'guadalajara', 'cruz azul', 'pumas'],
        'usa': ['usa', 'united states', 'la galaxy', 'seattle sounders', 'new york'],
        'south korea': ['korea', 'seoul', 'busan', 'daegu'],
        'japan': ['japan', 'tokyo', 'osaka', 'yokohama', 'kashima'],
        'china': ['china', 'beijing', 'shanghai', 'guangzhou'],
        'russia': ['russia', 'moscow', 'spartak', 'cska', 'dynamo', 'zenit'],
        'norway': ['norway', 'oslo', 'bergen'],
        'czech republic': ['czech', 'praha', 'prague', 'brno'],
        'austria': ['austria', 'vienna', 'salzburg']
    }
    
    # Check if this is an international friendly with multiple countries
    if 'international' in competition and 'friendly' in competition:
        home_countries = []
        away_countries = []
        
        # Look for country indicators in team names
        for country, indicators in country_indicators.items():
            for indicator in indicators:
                if indicator in home_team:
                    home_countries.append(country)
                if indicator in away_team:
                    away_countries.append(country)
        
        # If teams are from different countries, mark as International
        if home_countries and away_countries and home_countries[0] != away_countries[0]:
            return "International"
        
        # If only one team has identifiable country, use that
        if home_countries and not away_countries:
            return home_countries[0].title()
        elif away_countries and not home_countries:
            return away_countries[0].title()
        elif home_countries and away_countries and home_countries[0] == away_countries[0]:
            return home_countries[0].title()
    
    # For non-international competitions, try to infer from team names
    team_text = f"{home_team} {away_team}"
    for country, indicators in country_indicators.items():
        for indicator in indicators:
            if indicator in team_text:
                return country.title()
    
    # Default fallback
    return "Unknown"

def process_match(match_data: dict, comp_match_num: int, comp_total_matches: int):
    """
    Given one match's data, print + log its comprehensive details:
    - competition, teams, score, status
    - competition ID
    - betting odds (ML, Spread, O/U)
    - match environment (Weather, Temperature, Wind)
    
    Args:
        match_data: Dictionary containing match information
        comp_match_num: Match number within this competition group (1, 2, 3, etc.)
        comp_total_matches: Total matches in this competition group
    """
    # Match header - make match numbering more prominent
    blk = (
        f"\n{'-'*60}\n"
        f"⚽ *** MATCH {comp_match_num} of {comp_total_matches} *** ⚽ | {get_eastern_time()}\n"
        f"Match ID: {match_data.get('match_id', 'N/A')}\n"
        f"{'-'*60}"
    )
    log_and_print(blk)

    # Basic match information
    comp_line = f"Competition: {match_data.get('competition', 'Unknown')} ({match_data.get('country', 'Unknown')})"
    teams_line = f"Match: {match_data.get('home_team', 'Unknown')} vs {match_data.get('away_team', 'Unknown')}"
    score = match_data.get("score", "N/A")
    status_id = match_data.get("status_id", None)
    status_desc = get_status_description(status_id)
    status_line = f"Score: {score}\nStatus: {status_desc} (ID: {status_id})"
    
    log_and_print(comp_line)
    log_and_print(teams_line)
    log_and_print(status_line)

    # Betting odds section
    log_and_print("\n--- MATCH BETTING ODDS ---")
    betting_odds = format_betting_odds(match_data)
    log_and_print(betting_odds)

    # Environment section
    log_and_print("\n--- MATCH ENVIRONMENT ---")
    environment_data = format_environment_data(match_data)
    log_and_print(environment_data)

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
        
        # Load step5.json data with retry logic
        try:
            step5_data = safe_load_json_with_retry(STEP5_JSON)
        except Exception as e:
            log_and_print(f"❌ Error loading step5.json: {e}")
            return {
                "success": False,
                "error": f"Failed to load step5.json: {e}",
                "filtered_matches": 0,
                "total_matches": 0
            }
        
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
        write_main_footer(fetch_count, 0, generated_at, pipeline_time, None)
        return result
    
    matches = result.get("matches", {})
    total_filtered = result.get("filtered_matches", 0)
    
    # Write the main header
    write_main_header(fetch_count, total_filtered, generated_at, pipeline_time)
    
    if total_filtered == 0:
        log_and_print("No matches found for the given status filter (2-7).")
    else:
        log_and_print(f"Processing {total_filtered} matches with statuses {sorted(STATUS_FILTER)}...\n")
        
        # Group matches by competition and sort within each competition
        competition_groups = sort_matches_by_competition_and_time(matches)
        
        # Process each competition group
        for competition, competition_matches in competition_groups.items():
            # Get country from first match in the competition
            country = competition_matches[0][1].get("country", "Unknown") if competition_matches else "Unknown"
            match_count = len(competition_matches)
            
            # Write competition header with match count
            write_competition_group_header(competition, country, match_count)
            
            # Process matches in this competition with competition-specific numbering
            for comp_match_num, (match_id, match_data) in enumerate(competition_matches, 1):
                process_match(match_data, comp_match_num, match_count)
    
    # Write the main footer with status summary
    write_main_footer(fetch_count, total_filtered, generated_at, pipeline_time, matches)
    
    return result

def safe_load_json_with_retry(file_path, max_retries=3, retry_delay=0.5):
    """
    Safely load JSON with file locking and retry logic to handle concurrent access.
    
    Args:
        file_path: Path to JSON file
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
    
    Returns:
        dict: Loaded JSON data
    
    Raises:
        Exception: If all retries fail
    """
    for attempt in range(max_retries):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                # Try to acquire a shared lock (multiple readers allowed)
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
                except IOError:
                    # If we can't get a lock immediately, wait and retry
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    raise Exception(f"Could not acquire file lock after {max_retries} attempts")
                
                # Read and parse JSON
                data = json.load(f)
                
                # Release lock (automatically released when file closes, but explicit is better)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                return data
                
        except json.JSONDecodeError as e:
            error_msg = f"JSON parsing error (attempt {attempt + 1}/{max_retries}): {e}"
            if attempt < max_retries - 1:
                log_and_print(f"⚠️ {error_msg}, retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                continue
            # Don't raise exception, return empty data instead
            log_and_print(f"❌ JSON parsing failed after {max_retries} attempts: {e}")
            return {}
        except Exception as e:
            if attempt < max_retries - 1:
                log_and_print(f"⚠️ File access error (attempt {attempt + 1}/{max_retries}): {e}, retrying...")
                time.sleep(retry_delay)
                continue
            # Don't raise exception, return empty data instead  
            log_and_print(f"❌ File access failed after {max_retries} attempts: {e}")
            return {}
    
    # If we get here, all retries failed
    log_and_print(f"❌ Failed to load JSON after {max_retries} attempts, returning empty data")
    return {}

def create_step7_status_summary(filtered_matches: dict) -> dict:
    """
    Create a status summary for Step 7 filtered matches (status IDs 2, 3, 4, 5, 6, 7).
    Returns formatted summary similar to Step 1 but only for the filtered status IDs.
    """
    if not filtered_matches:
        return {
            "total_filtered_matches": 0,
            "status_breakdown": {},
            "formatted_summary": [],
            "step7_filter_ids": list(STATUS_FILTER)
        }
    
    # Count matches by status_id (only for our filtered statuses)
    status_counts = {}
    total_matches = len(filtered_matches)
    
    for match_id, match_data in filtered_matches.items():
        status_id = match_data.get("status_id")
        if status_id in STATUS_FILTER:  # Only count our filtered status IDs
            status_desc = get_status_description(status_id)
            if status_id not in status_counts:
                status_counts[status_id] = {
                    "description": status_desc,
                    "count": 0
                }
            status_counts[status_id]["count"] += 1
    
    # Create formatted summary lines like "First half (ID: 2): 23"
    formatted_summary = []
    status_breakdown = {}
    
    # Sort by status ID for consistent ordering
    for status_id in sorted(status_counts.keys()):
        data = status_counts[status_id]
        description = data["description"]
        count = data["count"]
        
        # Create formatted line
        formatted_line = f"{description} (ID: {status_id}): {count}"
        formatted_summary.append(formatted_line)
        
        # Store in structured format
        status_breakdown[f"status_{status_id}"] = {
            "id": status_id,
            "description": description,
            "count": count,
            "formatted": formatted_line
        }
    
    # Calculate total in-play matches (all matches with status IDs 2-7)
    total_in_play = sum(data["count"] for data in status_counts.values())
    
    # Add total in-play matches line
    formatted_summary.append(f"Total In-Play Matches: {total_in_play}")
    
    # Add total filtered matches line
    formatted_summary.append(f"Total Filtered Matches: {total_matches}")
    
    return {
        "total_filtered_matches": total_matches,
        "total_in_play_matches": total_in_play,
        "status_breakdown": status_breakdown,
        "formatted_summary": formatted_summary,
        "step7_filter_ids": list(STATUS_FILTER)
    }

def write_step7_status_summary(filtered_matches: dict):
    """Write Step 7 status summary to both console and log file"""
    summary = create_step7_status_summary(filtered_matches)
    
    if summary["total_filtered_matches"] == 0:
        message = "No matches found for Step 7 status filter"
        log_and_print(message)
        return summary
    
    # Write simple, clean status summary
    log_and_print(f"\n{'='*60}")
    log_and_print("STEP 7 - STATUS SUMMARY")
    log_and_print(f"{'='*60}")
    
    # Count matches by status
    status_counts = {}
    for match_data in filtered_matches.values():
        status_id = match_data.get("status_id")
        if status_id in STATUS_FILTER:
            status_counts[status_id] = status_counts.get(status_id, 0) + 1
    
    # Write simple status lines
    for status_id in sorted(status_counts.keys()):
        count = status_counts[status_id]
        desc = get_status_description(status_id)
        log_and_print(f"{desc} (ID: {status_id}): {count}")
    
    total = len(filtered_matches)
    log_and_print(f"Total: {total}")
    log_and_print(f"{'='*60}\n")
    
    return summary

def write_enhanced_status_visualization(summary: dict):
    """Write enhanced visual status distribution with ASCII charts"""
    if not summary.get("status_breakdown"):
        return
    
    # Extract counts for visualization
    status_counts = {}
    for status_key, data in summary["status_breakdown"].items():
        status_id = data["id"]
        count = data["count"]
        status_counts[status_id] = count
    
    # Write visual distribution chart
    log_and_print("\n" + "="*80)
    log_and_print("                     VISUAL STATUS DISTRIBUTION                     ")
    log_and_print("="*80)
    
    # Generate horizontal bar chart
    if status_counts:
        max_count = max(status_counts.values())
        total_matches = sum(status_counts.values())
        
        for status_id in sorted(status_counts.keys()):
            count = status_counts[status_id]
            desc = get_status_description(status_id)
            percentage = (count / total_matches) * 100 if total_matches > 0 else 0
            
            # Create visual bar (scaled to 50 characters max)
            bar_length = int((count / max_count) * 50) if max_count > 0 else 0
            bar = "█" * bar_length
            
            # Format with emoji indicators
            status_emojis = {
                2: "🔴", 3: "⏸️", 4: "🔴", 5: "⚡", 6: "⚡", 7: "🥅"
            }
            emoji = status_emojis.get(status_id, "⚽")
            
            log_and_print(f"{emoji} Status {status_id}: {desc}")
            log_and_print(f"   {bar} {count} matches ({percentage:.1f}%)")
            log_and_print("")
    
    # Add status timing insights
    write_status_timing_insights(status_counts)

def write_status_timing_insights(status_counts: dict):
    """Provide insights about match timing based on status distribution"""
    if not status_counts:
        return
    
    log_and_print("="*80)
    log_and_print("                        TIMING INSIGHTS                            ")
    log_and_print("="*80)
    
    total_matches = sum(status_counts.values())
    
    # Calculate in-play statistics
    first_half = status_counts.get(2, 0)
    half_time = status_counts.get(3, 0)
    second_half = status_counts.get(4, 0)
    overtime = status_counts.get(5, 0) + status_counts.get(6, 0)
    penalty = status_counts.get(7, 0)
    
    regular_time = first_half + half_time + second_half
    extended_time = overtime + penalty
    
    log_and_print(f"📊 MATCH FLOW ANALYSIS:")
    log_and_print(f"   Regular Time Matches: {regular_time} ({(regular_time/total_matches)*100:.1f}%)")
    log_and_print(f"   Extended Time Matches: {extended_time} ({(extended_time/total_matches)*100:.1f}%)")
    log_and_print("")
    
    if first_half > 0:
        log_and_print(f"⚽ {first_half} matches currently in FIRST HALF")
    if half_time > 0:
        log_and_print(f"☕ {half_time} matches at HALF-TIME (break)")
    if second_half > 0:
        log_and_print(f"⚽ {second_half} matches currently in SECOND HALF")
    if overtime > 0:
        log_and_print(f"⚡ {overtime} matches in OVERTIME/EXTRA TIME")
    if penalty > 0:
        log_and_print(f"🥅 {penalty} matches in PENALTY SHOOTOUT")
    
    log_and_print("")
    
    # Add peak activity indicator
    peak_status = max(status_counts.items(), key=lambda x: x[1])
    peak_desc = get_status_description(peak_status[0])
    log_and_print(f"🔥 PEAK ACTIVITY: {peak_desc} ({peak_status[1]} matches)")

def write_match_timeline_projection(status_counts: dict):
    """Project when matches might finish based on current status"""
    if not status_counts:
        return
    
    log_and_print("="*80)
    log_and_print("                      TIMELINE PROJECTION                          ")
    log_and_print("="*80)
    
    # Estimated remaining time for each status (in minutes)
    time_estimates = {
        2: "20-45 minutes",  # First half
        3: "50-75 minutes",  # Half-time + second half
        4: "0-45 minutes",   # Second half only
        5: "0-30 minutes",   # Overtime
        6: "0-30 minutes",   # Overtime (deprecated)
        7: "0-15 minutes"    # Penalty shootout
    }
    
    for status_id in sorted(status_counts.keys()):
        count = status_counts[status_id]
        if count > 0:
            desc = get_status_description(status_id)
            estimate = time_estimates.get(status_id, "Unknown")
            log_and_print(f"⏱️  {count} matches in {desc}: ~{estimate} remaining")

def create_status_trend_analysis(filtered_matches: dict) -> dict:
    """Analyze status trends and provide insights"""
    if not filtered_matches:
        return {}
    
    # Group by competition to analyze patterns
    competition_analysis = {}
    
    for match_id, match_data in filtered_matches.items():
        comp_name = match_data.get("competition", "Unknown")
        status_id = match_data.get("status_id")
        
        if comp_name not in competition_analysis:
            competition_analysis[comp_name] = {
                "total_matches": 0,
                "status_distribution": {},
                "country": match_data.get("country", "Unknown")
            }
        
        competition_analysis[comp_name]["total_matches"] += 1
        
        if status_id not in competition_analysis[comp_name]["status_distribution"]:
            competition_analysis[comp_name]["status_distribution"][status_id] = 0
        competition_analysis[comp_name]["status_distribution"][status_id] += 1
    
    return competition_analysis

def write_competition_analysis(filtered_matches: dict):
    """Write detailed analysis by competition"""
    analysis = create_status_trend_analysis(filtered_matches)
    
    if not analysis:
        return
    
    log_and_print("="*80)
    log_and_print("                     COMPETITION BREAKDOWN                         ")
    log_and_print("="*80)
    
    # Sort competitions by total matches (descending)
    sorted_comps = sorted(analysis.items(), key=lambda x: x[1]["total_matches"], reverse=True)
    
    for comp_name, data in sorted_comps:
        total = data["total_matches"]
        country = data["country"]
        status_dist = data["status_distribution"]
        
        log_and_print(f"🏆 {comp_name} ({country}): {total} matches")
        
        # Show status breakdown for this competition
        for status_id in sorted(status_dist.keys()):
            count = status_dist[status_id]
            desc = get_status_description(status_id)
            percentage = (count / total) * 100
            log_and_print(f"   └─ {desc}: {count} ({percentage:.0f}%)")
        log_and_print("")

def write_status_key_reference():
    """Write a reference guide for status ID meanings at the top of the log"""
    status_key = (
        f"\n{'='*80}\n"
        f"                      STEP 7 - STATUS ID REFERENCE KEY                      \n"
        f"{'='*80}\n"
        f"0: Abnormal (suggest hiding)     ⟹ NOT INCLUDED\n"
        f"1: Not started                   ⟹ NOT INCLUDED\n" 
        f"2: First half                    ⟹ INCLUDED (IN-PLAY)\n"
        f"3: Half-time                     ⟹ INCLUDED (IN-PLAY)\n"
        f"4: Second half                   ⟹ INCLUDED (IN-PLAY)\n"
        f"5: Overtime                      ⟹ INCLUDED (IN-PLAY)\n"
        f"6: Overtime (deprecated)         ⟹ INCLUDED (IN-PLAY)\n"
        f"7: Penalty Shoot-out             ⟹ INCLUDED (IN-PLAY)\n"
        f"8: End                           ⟹ NOT INCLUDED\n"
        f"9: Delay                         ⟹ NOT INCLUDED\n"
        f"10: Interrupt                    ⟹ NOT INCLUDED\n"
        f"11: Cut in half                  ⟹ NOT INCLUDED\n"
        f"12: Cancel                       ⟹ NOT INCLUDED\n"
        f"13: To be determined             ⟹ NOT INCLUDED\n"
        f"{'='*80}\n"
        f"NOTE: Status IDs 2-7 are considered 'IN-PLAY' matches and are included in Step 7 output\n"
        f"{'='*80}\n"
    )
    log_and_print(status_key)

class StatusMonitor:
    """Monitor status changes and provide alerts"""
    
    def __init__(self):
        self.previous_status = {}
        self.status_history = {}
        self.alert_thresholds = {
            'mass_transition': 5,  # Alert if 5+ matches change status at once
            'unusual_status': [0, 9, 10, 11, 12, 13],  # Alert on unusual statuses
            'extended_time': [5, 6, 7]  # Alert on overtime/penalties
        }
    
    def check_status_changes(self, current_matches: dict) -> dict:
        """
        Check for status changes and generate alerts
        
        Returns:
            dict: Contains alerts and status change information
        """
        alerts = []
        changes = []
        
        current_time = get_eastern_time()
        
        for match_id, match_data in current_matches.items():
            current_status = match_data.get("status_id")
            competition = match_data.get("competition", "Unknown")
            teams = f"{match_data.get('home_team', 'Unknown')} vs {match_data.get('away_team', 'Unknown')}"
            
            # Check if we've seen this match before
            if match_id in self.previous_status:
                prev_status = self.previous_status[match_id]
                
                if current_status != prev_status:
                    change_info = {
                        'match_id': match_id,
                        'competition': competition,
                        'teams': teams,
                        'from_status': prev_status,
                        'to_status': current_status,
                        'from_desc': get_status_description(prev_status),
                        'to_desc': get_status_description(current_status),
                        'timestamp': current_time
                    }
                    changes.append(change_info)
                    
                    # Track in history
                    if match_id not in self.status_history:
                        self.status_history[match_id] = []
                    self.status_history[match_id].append(change_info)
                    
                    # Generate specific alerts
                    if current_status in self.alert_thresholds['extended_time']:
                        alerts.append({
                            'type': 'extended_time',
                            'message': f"🚨 EXTENDED TIME: {teams} ({competition}) moved to {get_status_description(current_status)}",
                            'match_info': change_info
                        })
                    
                    if current_status in self.alert_thresholds['unusual_status']:
                        alerts.append({
                            'type': 'unusual_status',
                            'message': f"⚠️ UNUSUAL STATUS: {teams} ({competition}) moved to {get_status_description(current_status)}",
                            'match_info': change_info
                        })
            
            # Update previous status
            self.previous_status[match_id] = current_status
        
        # Check for mass transitions
        if len(changes) >= self.alert_thresholds['mass_transition']:
            alerts.append({
                'type': 'mass_transition',
                'message': f"📊 MASS STATUS CHANGE: {len(changes)} matches changed status simultaneously",
                'change_count': len(changes)
            })
        
        return {
            'alerts': alerts,
            'changes': changes,
            'total_changes': len(changes),
            'timestamp': current_time
        }
    
    def get_status_summary_report(self) -> str:
        """Generate a summary report of all status changes"""
        if not self.status_history:
            return "No status changes recorded yet."
        
        report = f"\n{'='*80}\n"
        report += "                    STATUS CHANGE HISTORY REPORT                   \n"
        report += f"{'='*80}\n"
        
        # Count transitions by type
        transition_counts = {}
        for match_id, history in self.status_history.items():
            for change in history:
                transition_key = f"{change['from_desc']} → {change['to_desc']}"
                transition_counts[transition_key] = transition_counts.get(transition_key, 0) + 1
        
        report += "Most Common Status Transitions:\n"
        for transition, count in sorted(transition_counts.items(), key=lambda x: x[1], reverse=True):
            report += f"  • {transition}: {count} times\n"
        
        report += f"\nTotal Matches Tracked: {len(self.status_history)}\n"
        report += f"Total Status Changes: {sum(len(h) for h in self.status_history.values())}\n"
        report += f"{'='*80}\n"
        
        return report

def write_status_alerts(monitor_result: dict):
    """Write status alerts to log if any are present"""
    if not monitor_result.get('alerts'):
        return
    
    log_and_print("="*80)
    log_and_print("                         STATUS ALERTS                             ")
    log_and_print("="*80)
    
    for alert in monitor_result['alerts']:
        log_and_print(alert['message'])
        if 'match_info' in alert:
            match_info = alert['match_info']
            log_and_print(f"   Match: {match_info['teams']}")
            log_and_print(f"   Competition: {match_info['competition']}")
            log_and_print(f"   Status Change: {match_info['from_desc']} → {match_info['to_desc']}")
        log_and_print("")

def create_detailed_statistics_report(filtered_matches: dict) -> dict:
    """Create comprehensive statistics about the filtered matches"""
    if not filtered_matches:
        return {}
    
    stats = {
        'total_matches': len(filtered_matches),
        'by_status': {},
        'by_competition': {},
        'by_country': {},
        'score_analysis': {
            'draws': 0,
            'home_leading': 0,
            'away_leading': 0,
            'high_scoring': 0  # 3+ goals
        },
        'betting_analysis': {
            'with_odds': 0,
            'without_odds': 0
        }
    }
    
    for match_id, match_data in filtered_matches.items():
        # Status breakdown
        status_id = match_data.get("status_id")
        if status_id not in stats['by_status']:
            stats['by_status'][status_id] = {
                'count': 0,
                'description': get_status_description(status_id)
            }
        stats['by_status'][status_id]['count'] += 1
        
        # Competition breakdown
        competition = match_data.get("competition", "Unknown")
        stats['by_competition'][competition] = stats['by_competition'].get(competition, 0) + 1
        
        # Country breakdown
        country = match_data.get("country", "Unknown")
        stats['by_country'][country] = stats['by_country'].get(country, 0) + 1
        
        # Score analysis
        score = match_data.get("score", "")
        if " - " in score:
            try:
                home_score, away_score = score.split(" - ")
                # Extract just the current score (before HT info)
                if "(" in home_score:
                    home_score = home_score.split("(")[0].strip()
                if "(" in away_score:
                    away_score = away_score.split("(")[0].strip()
                
                home_goals = int(home_score)
                away_goals = int(away_score)
                
                if home_goals == away_goals:
                    stats['score_analysis']['draws'] += 1
                elif home_goals > away_goals:
                    stats['score_analysis']['home_leading'] += 1
                else:
                    stats['score_analysis']['away_leading'] += 1
                
                if (home_goals + away_goals) >= 3:
                    stats['score_analysis']['high_scoring'] += 1
                    
            except (ValueError, IndexError):
                pass  # Skip malformed scores
        
        # Betting analysis
        if match_data.get("full_time_result") or match_data.get("spread") or match_data.get("over_under"):
            stats['betting_analysis']['with_odds'] += 1
        else:
            stats['betting_analysis']['without_odds'] += 1
    
    return stats

def write_detailed_statistics_report(filtered_matches: dict):
    """Write comprehensive statistics report"""
    stats = create_detailed_statistics_report(filtered_matches)
    
    if not stats:
        return
    
    log_and_print("="*80)
    log_and_print("                      DETAILED STATISTICS REPORT                   ")
    log_and_print("="*80)
    
    total = stats['total_matches']
    
    # Geographic distribution
    log_and_print("🌍 GEOGRAPHIC DISTRIBUTION:")
    for country, count in sorted(stats['by_country'].items(), key=lambda x: x[1], reverse=True)[:5]:
        percentage = (count / total) * 100
        log_and_print(f"   {country}: {count} matches ({percentage:.1f}%)")
    log_and_print("")
    
    # Score analysis
    score_stats = stats['score_analysis']
    log_and_print("⚽ SCORE ANALYSIS:")
    log_and_print(f"   Draws: {score_stats['draws']} ({(score_stats['draws']/total)*100:.1f}%)")
    log_and_print(f"   Home Leading: {score_stats['home_leading']} ({(score_stats['home_leading']/total)*100:.1f}%)")
    log_and_print(f"   Away Leading: {score_stats['away_leading']} ({(score_stats['away_leading']/total)*100:.1f}%)")
    log_and_print(f"   High Scoring (3+ goals): {score_stats['high_scoring']} ({(score_stats['high_scoring']/total)*100:.1f}%)")
    log_and_print("")
    
    # Betting coverage
    betting_stats = stats['betting_analysis']
    log_and_print("💰 BETTING ODDS COVERAGE:")
    log_and_print(f"   Matches with odds: {betting_stats['with_odds']} ({(betting_stats['with_odds']/total)*100:.1f}%)")
    log_and_print(f"   Matches without odds: {betting_stats['without_odds']} ({(betting_stats['without_odds']/total)*100:.1f}%)")

def generate_live_dashboard_summary(filtered_matches: dict) -> str:
    """Generate a compact live dashboard summary for real-time monitoring"""
    if not filtered_matches:
        return "📊 LIVE DASHBOARD: No active matches"
    
    total = len(filtered_matches)
    status_counts = {}
    
    for match_data in filtered_matches.values():
        status_id = match_data.get("status_id")
        if status_id in STATUS_FILTER:
            status_counts[status_id] = status_counts.get(status_id, 0) + 1
    
    # Create compact dashboard
    dashboard = f"📊 LIVE DASHBOARD ({get_eastern_time()})\n"
    dashboard += f"{'='*60}\n"
    dashboard += f"🔥 Total Active Matches: {total}\n"
    
    # Status breakdown with emojis
    status_emojis = {2: "🔴", 3: "⏸️", 4: "🔴", 5: "⚡", 6: "⚡", 7: "🥅"}
    for status_id in sorted(status_counts.keys()):
        count = status_counts[status_id]
        emoji = status_emojis.get(status_id, "⚽")
        desc = get_status_description(status_id)
        dashboard += f"{emoji} {desc}: {count}\n"
    
    dashboard += f"{'='*60}"
    return dashboard

def create_exportable_summary(filtered_matches: dict) -> dict:
    """Create a structured summary suitable for export/API consumption"""
    current_time = get_eastern_time()
    
    summary = {
        "generated_at": current_time,
        "step": "7",
        "filter_criteria": {
            "status_ids": list(STATUS_FILTER),
            "description": "In-play matches (First half, Half-time, Second half, Overtime, Penalty shootout)"
        },
        "totals": {
            "filtered_matches": len(filtered_matches),
            "active_competitions": len(set(m.get("competition", "Unknown") for m in filtered_matches.values())),
            "active_countries": len(set(m.get("country", "Unknown") for m in filtered_matches.values()))
        },
        "status_breakdown": {},
        "competition_summary": {},
        "insights": {}
    }
    
    # Status breakdown
    for match_data in filtered_matches.values():
        status_id = match_data.get("status_id")
        if status_id not in summary["status_breakdown"]:
            summary["status_breakdown"][status_id] = {
                "description": get_status_description(status_id),
                "count": 0,
                "percentage": 0
            }
        summary["status_breakdown"][status_id]["count"] += 1
    
    # Calculate percentages
    total = len(filtered_matches)
    if total > 0:
        for status_data in summary["status_breakdown"].values():
            status_data["percentage"] = (status_data["count"] / total) * 100
    
    # Competition summary
    comp_counts = {}
    for match_data in filtered_matches.values():
        comp = match_data.get("competition", "Unknown")
        comp_counts[comp] = comp_counts.get(comp, 0) + 1
    
    summary["competition_summary"] = {
        comp: {"match_count": count, "percentage": (count/total)*100 if total > 0 else 0}
        for comp, count in comp_counts.items()
    }
    
    # Generate insights
    if summary["status_breakdown"]:
        peak_status = max(summary["status_breakdown"].items(), key=lambda x: x[1]["count"])
        summary["insights"]["peak_activity_status"] = {
            "status_id": peak_status[0],
            "description": peak_status[1]["description"],
            "count": peak_status[1]["count"]
        }
    
    if comp_counts:
        busiest_comp = max(comp_counts.items(), key=lambda x: x[1])
        summary["insights"]["busiest_competition"] = {
            "name": busiest_comp[0],
            "match_count": busiest_comp[1]
        }
    
    return summary

def save_summary_to_json(filtered_matches: dict):
    """Save structured summary to JSON file for external consumption"""
    try:
        summary = create_exportable_summary(filtered_matches)
        
        # Save to step7 directory
        json_file = BASE_DIR / "step7_summary.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        log_and_print(f"📄 Summary exported to: {json_file}")
        return True
        
    except Exception as e:
        log_and_print(f"❌ Failed to save summary JSON: {e}")
        return False

def run_batch_analysis(filtered_matches: dict):
    """Run a comprehensive batch analysis of all filtered matches"""
    if not filtered_matches:
        return
    
    log_and_print("="*80)
    log_and_print("                       BATCH ANALYSIS REPORT                       ")
    log_and_print("="*80)
    
    # Generate live dashboard
    dashboard = generate_live_dashboard_summary(filtered_matches)
    log_and_print(dashboard)
    log_and_print("")
    
    # Save exportable summary
    save_summary_to_json(filtered_matches)
    
    # Generate status monitoring report
    if hasattr(status_monitor, 'status_history') and status_monitor.status_history:
        history_report = status_monitor.get_status_summary_report()
        log_and_print(history_report)

def write_performance_metrics(start_time: float, filtered_matches: dict):
    """Write performance metrics for the filtering operation"""
    end_time = time.time()
    processing_time = end_time - start_time
    
    total_matches = len(filtered_matches)
    
    log_and_print("="*80)
    log_and_print("                      PERFORMANCE METRICS                          ")
    log_and_print("="*80)
    log_and_print(f"⏱️  Processing Time: {processing_time:.3f} seconds")
    log_and_print(f"📊 Matches Processed: {total_matches}")
    if total_matches > 0:
        log_and_print(f"🚀 Processing Rate: {total_matches/processing_time:.1f} matches/second")
    log_and_print(f"💾 Memory Footprint: Estimated {total_matches * 2}KB")
    log_and_print(f"📁 Output Files Generated: step7_matches.log, step7_summary.json")

# Global status monitor instance
status_monitor = StatusMonitor()

def main():
    """Main function to execute the script logic."""
    log_and_print(f"🚀 Starting Step 7: Status Filter (2-7) at {get_eastern_time()}")
    
    # Write status key reference at the top for clarity
    write_status_key_reference()
    
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