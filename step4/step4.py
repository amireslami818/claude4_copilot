#!/usr/bin/env python3
"""
Step 4 - Match Summary Extractor
Extracts specific match fields for structured output and analysis

This module processes the Step 3 JSON summaries and extracts key match information
including scores, odds, status, and environment data in a simplified format.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# Use the same timezone as other modules
TZ = ZoneInfo("America/New_York")

# Path constants - Updated for our project structure
BASE_DIR = Path(__file__).parent
STEP3_JSON = BASE_DIR.parent / "step3" / "step3.json"
STEP4_JSON = BASE_DIR / "step4.json"

def get_eastern_time():
    """Get current time in Eastern timezone with MM/DD/YYYY format"""
    now = datetime.now(TZ)
    return now.strftime("%m/%d/%Y %I:%M:%S %p %Z")

def format_score(home_current, away_current, home_halftime=0, away_halftime=0):
    """Format score in the requested format"""
    return f"{home_current} - {away_current} (HT: {home_halftime} - {away_halftime})"

def extract_match_summary(match_id, match_data):
    """Extract the specific fields requested for each match"""
    
    # Basic match information
    summary = {
        "match_id": match_id,
        "competition_id": match_data.get("competition", {}).get("id", ""),
        "competition": match_data.get("competition", {}).get("name", ""),
        "country": match_data.get("competition", {}).get("country", ""),
        "home_team": match_data.get("teams", {}).get("home", {}).get("name", ""),
        "away_team": match_data.get("teams", {}).get("away", {}).get("name", ""),
    }
    
    # Calculate score using the provided logic
    home_score = match_data.get("teams", {}).get("home", {}).get("score", {})
    away_score = match_data.get("teams", {}).get("away", {}).get("score", {})
    
    home_current = home_score.get("current", 0)
    home_halftime = home_score.get("halftime", 0)
    away_current = away_score.get("current", 0)
    away_halftime = away_score.get("halftime", 0)
    
    summary["score"] = format_score(home_current, away_current, home_halftime, away_halftime)
    
    # Status - Updated to match our step3 structure
    match_info = match_data.get("match_info", {})
    status_info = match_info.get("status", {})
    status_id = status_info.get("id", 0)
    
    # Determine status based on ID
    if status_id == 1:
        status = "Upcoming"
    elif 2 <= status_id <= 7:
        status = "Live"
    elif status_id >= 8:
        status = "Finished"
    else:
        status = "Unknown"
    
    summary["status"] = status
    
    # Odds fields - Updated for our step3 odds structure
    odds = match_data.get("odds", {})
    
    # Full time result odds
    full_time_result = odds.get("full_time_result", {})
    if full_time_result and full_time_result.get("home") is not None:
        summary["full_time_result"] = {
            "home": full_time_result.get("home"),
            "draw": full_time_result.get("draw"),
            "away": full_time_result.get("away")
        }
        # Add time only if it exists
        if full_time_result.get("match_time"):
            summary["full_time_result"]["time"] = full_time_result.get("match_time")
    else:
        summary["full_time_result"] = None
    
    # Spread odds
    spread = odds.get("spread", {})
    if spread and spread.get("handicap") is not None:
        summary["spread"] = {
            "handicap": spread.get("handicap"),
            "home": spread.get("home"),
            "away": spread.get("away"),
            "time": spread.get("match_time")
        }
    else:
        summary["spread"] = None
    
    # Over/Under odds - Updated for our structure
    primary_ou = odds.get("primary_over_under", {})
    
    if primary_ou and primary_ou.get("line") is not None:
        line = primary_ou.get("line")
        summary["over_under"] = {
            str(line): {
                "line": line,
                "over": primary_ou.get("over"),
                "under": primary_ou.get("under"),
                "time": primary_ou.get("match_time")
            }
        }
    else:
        summary["over_under"] = None
    
    # Both teams to score
    btts = odds.get("both_teams_to_score", {})
    if btts and btts.get("yes") is not None:
        summary["both_teams_to_score"] = {
            "yes": btts.get("yes"),
            "no": btts.get("no"),
            "time": btts.get("match_time")
        }
    else:
        summary["both_teams_to_score"] = None
    
    # Environment data
    env = match_data.get("environment", {})
    if env:
        summary["environment"] = {
            "weather_description": env.get("weather_description", "Unknown"),
            "temperature": env.get("temperature"),
            "temperature_value": env.get("temperature_value"),
            "temperature_unit": env.get("temperature_unit"),
            "wind_description": env.get("wind_description", "Calm"),
            "wind_value": env.get("wind_value"),
            "wind_unit": env.get("wind_unit"),
            "pressure_value": env.get("pressure_value"),
            "pressure_unit": env.get("pressure_unit"),
            "humidity_value": env.get("humidity_value")
        }
    else:
        summary["environment"] = None
    
    # Venue information
    venue = match_data.get("match_info", {}).get("venue")
    if venue:
        summary["venue"] = venue
    else:
        summary["venue"] = None
    
    # Start time
    start_time = match_data.get("match_info", {}).get("start_time")
    if start_time:
        summary["start_time"] = start_time
    else:
        summary["start_time"] = None
    
    return summary

def get_snapshot_matches(step3_snapshot):
    """Return list of per-match dicts from a single Step-3 snapshot"""
    matches_dict = step3_snapshot.get("matches", {})
    return list(matches_dict.values())

def process_step3_data(step3_data):
    """Process Step 3 data and extract match summaries"""
    
    # Handle history structure - get the latest entry
    if isinstance(step3_data, dict) and "history" in step3_data:
        if step3_data["history"]:
            latest_snapshot = step3_data["history"][-1]
            print(f"Step 4: Processing latest Step 3 snapshot with {latest_snapshot.get('match_count', 0)} matches")
        else:
            print("Step 4: No history entries found in Step 3 data")
            return {}
    else:
        # Legacy format without history
        latest_snapshot = step3_data
        print(f"Step 4: Processing Step 3 data with {latest_snapshot.get('match_count', 0)} matches")
    
    # Extract matches from the snapshot
    matches = get_snapshot_matches(latest_snapshot)
    
    # Process each match
    processed_matches = {}
    for match in matches:
        match_id = match.get("match_id")
        if match_id:
            processed_matches[match_id] = extract_match_summary(match_id, match)
    
    # Create summary statistics
    total_matches = len(processed_matches)
    matches_with_odds = sum(1 for m in processed_matches.values() if m.get("full_time_result"))
    matches_with_environment = sum(1 for m in processed_matches.values() if m.get("environment"))
    
    # Categorize by status
    status_counts = {}
    for match in processed_matches.values():
        status = match.get("status", "Unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Create the final structure
    result = {
        "generated_at": get_eastern_time(),
        "source_timestamp": latest_snapshot.get("generated_at"),
        "total_matches": total_matches,
        "statistics": {
            "matches_with_odds": matches_with_odds,
            "matches_with_environment": matches_with_environment,
            "by_status": status_counts
        },
        "matches": processed_matches
    }
    
    return result

def save_step4_json(step4_data):
    """Save the step4 data to step4.json file"""
    try:
        # Load existing data if file exists
        existing_data = {"history": []}
        if STEP4_JSON.exists():
            try:
                with open(STEP4_JSON, 'r') as f:
                    existing_data = json.load(f)
                    if "history" not in existing_data:
                        existing_data = {"history": [existing_data] if existing_data else []}
            except (json.JSONDecodeError, Exception):
                existing_data = {"history": []}
        
        # Add current data to history
        existing_data["history"].append(step4_data)
        
        # Update metadata
        existing_data["last_updated"] = step4_data.get("generated_at")
        existing_data["total_entries"] = len(existing_data["history"])
        existing_data["latest_match_count"] = step4_data.get("total_matches", 0)
        existing_data["ny_timestamp"] = get_eastern_time()
        
        # Save updated data
        with open(STEP4_JSON, 'w') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        
        print(f"Step 4: Data saved to {STEP4_JSON}")
        return True
        
    except Exception as e:
        print(f"Step 4: Error saving step4.json: {e}")
        return False

def generate_match_extracts(step3_data):
    """Generate the match extracts and save to disk"""
    step4_data = process_step3_data(step3_data)
    save_step4_json(step4_data)
    return step4_data

# Main async function to be called from orchestrator
async def match_extracts(step3_data):
    """
    Main entry point for Step 4 - called from orchestrator
    
    Args:
        step3_data: Step 3 summary data
    
    Returns:
        Dictionary containing the processed match extracts
    """
    print("Step 4: Starting match_extracts...")
    
    # Check if we need to load step3.json file
    if isinstance(step3_data, list) or not step3_data:
        # Load from file
        if STEP3_JSON.exists():
            try:
                with open(STEP3_JSON, 'r') as f:
                    file_data = json.load(f)
                
                # Handle history structure - get the latest entry
                if isinstance(file_data, dict) and "history" in file_data:
                    if file_data["history"]:
                        step3_data = file_data["history"][-1]
                        print(f"Step 4: Loaded latest Step 3 entry with {step3_data.get('match_count', 0)} matches")
                    else:
                        print("Step 4: No history entries found in step3.json")
                        return {}
                else:
                    # Legacy format without history
                    step3_data = file_data
                    print(f"Step 4: Loaded step3.json with {step3_data.get('match_count', 0)} matches")
            except Exception as e:
                print(f"Step 4: Error loading step3.json: {e}")
                return {}
        else:
            print("Step 4: step3.json not found")
            return {}
    
    # Process the data
    try:
        result = generate_match_extracts(step3_data)
        if result:
            print(f"Step 4: Successfully processed {result['total_matches']} matches")
            print(f"Step 4: {result['statistics']['matches_with_odds']} matches have odds data")
        else:
            print("Step 4: Failed to process match extracts")
        
        return result or {}
    except Exception as e:
        print(f"Step 4: Error in match_extracts: {e}")
        return {}

if __name__ == "__main__":
    # For testing directly
    import sys
    import asyncio
    
    print("Step 4 - Standalone Test")
    print("=" * 25)
    
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        print(f"Loading data from: {sys.argv[1]}")
        with open(sys.argv[1], 'r') as f:
            data = json.load(f)
            result = asyncio.run(match_extracts(data))
            print(f"🎉 Generated match extracts for {result.get('total_matches', 0)} matches")
    else:
        # Try to load step3.json from default location
        print(f"Looking for step3.json at: {STEP3_JSON}")
        
        if STEP3_JSON.exists():
            print("✅ Found step3.json")
            with open(STEP3_JSON, 'r') as f:
                data = json.load(f)
                
            result = asyncio.run(match_extracts(data))
            print(f"🎉 Generated match extracts for {result.get('total_matches', 0)} matches")
        else:
            print("❌ step3.json not found")
            print("💡 Run the pipeline first or provide a file path as argument")
