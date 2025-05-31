#!/usr/bin/env python3
"""
Step 3 - JSON Summary Generator
Generates JSON summaries of matches with structured field organization

This module creates a structured representation of all match data, making it
easier to:
1. Reference exact field paths for alert criteria
2. Debug which fields are available for scanning
3. Ensure consistent data representation between steps

The original version wrote the generated summaries to ``step3.json`` and a
separate log file.  This lightweight version simply returns the summary data
without any logging or file output.

IMPORTANT TERMINOLOGY:
- LIVE MATCHES = All matches from /match/detail_live API endpoint (broader category)
- IN-PLAY MATCHES = Only matches with status_id 2,3,4,5,6 (actively playing subset of live matches)
"""

import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# Use the same timezone as other modules
TZ = ZoneInfo("America/New_York")

# Path constant used in __main__ for loading step2.json
BASE_DIR = Path(__file__).parent

def get_eastern_time():
    """Get current time in Eastern timezone with MM/DD/YYYY format"""
    now = datetime.now(TZ)
    return now.strftime("%m/%d/%Y %I:%M:%S %p %Z")

def extract_odds_summary(odds):
    """Extract a summary of the most important odds"""
    summary = {
        "has_odds": False,
        "full_time_result": odds.get("full_time_result", {}),
        "primary_over_under": odds.get("primary_over_under", {}),
        "spread": odds.get("spread", {}),
        "both_teams_to_score": odds.get("both_teams_to_score", {})
    }
    
    # Check if we have any odds data
    if (summary["full_time_result"].get("home") is not None or
        summary["primary_over_under"].get("line") is not None or
        summary["spread"].get("handicap") is not None):
        summary["has_odds"] = True
    
    return summary

def organize_match_summary(match):
    """
    Organize match data into a clean, structured format
    This takes the already processed data from step2 and reorganizes it
    """
    # The match data from step2 is already well-structured, so we'll enhance it
    summary = {
        "match_id": match.get("match_id"),
        "fetched_at": match.get("fetched_at"),
        
        # Basic match info
        "match_info": {
            "status": match.get("status", {}),
            "venue": match.get("venue"),
            "referee": match.get("referee"),
            "neutral": match.get("neutral"),
            "start_time": match.get("start_time"),
        },
        
        # Competition/league info
        "competition": {
            "id": match.get("competition", {}).get("id"),
            "name": match.get("competition", {}).get("name"),
            "country": match.get("competition", {}).get("country"),
            "season": match.get("competition", {}).get("season")
        },
        
        # Team information
        "teams": {
            "home": match.get("teams", {}).get("home", {}),
            "away": match.get("teams", {}).get("away", {})
        },
        
        # Scores and statistics
        "scores": match.get("scores", {}),
        "statistics": match.get("statistics", {}),
        
        # Betting data
        "odds": extract_odds_summary(match.get("odds", {})),
        
        # Match events
        "events": match.get("events", []),
        
        # Additional metadata
        "environment": match.get("environment", {}),
        "lineups": match.get("lineups", {}),
        "injuries": match.get("injuries", {})
    }
    
    return summary

def categorize_matches(matches):
    """Categorize matches by status and competition"""
    categories = {
        "by_status": {
            "live": [],
            "upcoming": [],
            "finished": [],
            "other": []
        },
        "by_competition": {},
        "statistics": {
            "total": len(matches),
            "with_odds": 0,
            "with_events": 0,
            "by_weather": {}
        }
    }
    
    for match_id, match in matches.items():
        # Categorize by status using comprehensive mapping
        status_id = match.get("status", {}).get("id")
        if status_id in [2, 3, 4, 5, 6]:  # Live statuses (First half, Half-time, Second half, Extra time, Penalty shootout)
            categories["by_status"]["live"].append(match_id)
        elif status_id == 1:  # Not started
            categories["by_status"]["upcoming"].append(match_id)
        elif status_id in [7, 8]:  # Finished statuses
            categories["by_status"]["finished"].append(match_id)
        elif status_id in [9, 10, 11, 12, 13, 14]:  # Postponed, Canceled, TBA, Interrupted, Abandoned, Suspended
            categories["by_status"]["other"].append(match_id)
        else:
            categories["by_status"]["other"].append(match_id)
        
        # Categorize by competition
        comp_name = match.get("competition", {}).get("name", "Unknown")
        if comp_name not in categories["by_competition"]:
            categories["by_competition"][comp_name] = []
        categories["by_competition"][comp_name].append(match_id)
        
        # Statistics
        if match.get("odds", {}).get("full_time_result", {}).get("home") is not None:
            categories["statistics"]["with_odds"] += 1
        
        if match.get("events", []):
            categories["statistics"]["with_events"] += 1
        
        # Weather statistics
        weather_desc = match.get("environment", {}).get("weather_description", "Unknown")
        if weather_desc not in categories["statistics"]["by_weather"]:
            categories["statistics"]["by_weather"][weather_desc] = 0
        categories["statistics"]["by_weather"][weather_desc] += 1
    
    return categories

def generate_summary_json(step2_data):
    """Generate comprehensive summary JSON data"""
    matches = step2_data.get("matches", {})
    
    # Process each match
    processed_matches = {}
    for match_id, match in matches.items():
        processed_matches[match_id] = organize_match_summary(match)
    
    # Generate categories and statistics
    categories = categorize_matches(matches)
    
    # Create the final summary structure
    summary_data = {
        "generated_at": get_eastern_time(),
        "source_timestamp": step2_data.get("timestamp"),
        "match_count": len(matches),
        "categories": categories,
        "matches": processed_matches
    }
    
    return summary_data

def save_summary_json(summary_data):
    """Save the summary data to step3.json file"""
    import os
    from pathlib import Path
    
    # Create step3 directory if it doesn't exist
    step3_dir = Path(__file__).parent
    step3_dir.mkdir(exist_ok=True)
    
    # Define the output file path
    output_file = step3_dir / "step3.json"
    
    try:
        # Load existing data if file exists
        existing_data = {"history": []}
        if output_file.exists():
            try:
                with open(output_file, 'r') as f:
                    existing_data = json.load(f)
                    if "history" not in existing_data:
                        existing_data = {"history": [existing_data] if existing_data else []}
            except (json.JSONDecodeError, Exception):
                existing_data = {"history": []}
        
        # Add current summary to history
        existing_data["history"].append(summary_data)
        
        # Update metadata
        existing_data["last_updated"] = summary_data.get("generated_at")
        existing_data["total_entries"] = len(existing_data["history"])
        existing_data["latest_match_count"] = summary_data.get("match_count", 0)
        existing_data["ny_timestamp"] = get_eastern_time()
        
        # Save updated data
        with open(output_file, 'w') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        
        print(f"Step 3: Summary saved to {output_file}")
        return True
        
    except Exception as e:
        print(f"Step 3: Error saving summary JSON: {e}")
        return False

def generate_summary(step2_data):
    """Generate the summary JSON data and save to disk"""
    summary_data = generate_summary_json(step2_data)
    save_summary_json(summary_data)
    return summary_data

# Main async function to be called from orchestrator
async def json_summary(summaries):
    """
    Main entry point for Step 3 - called from orchestrator
    
    Args:
        summaries: List of match summaries from Step 2
    
    Returns:
        Dictionary containing the processed summary data
    """
    print("Step 3: Starting json_summary...")
    
    # Since we receive summaries as a list, we need to check if it's already
    # the step2 data structure or if we need to load it
    if isinstance(summaries, list):
        # If it's a list, we need to load the step2.json file
        step2_file = Path(__file__).parent.parent / "step2" / "step2.json"
        
        try:
            with open(step2_file, 'r') as f:
                file_data = json.load(f)
            
            # Handle history structure - get the latest entry
            if isinstance(file_data, dict) and "history" in file_data:
                if file_data["history"]:
                    step2_data = file_data["history"][-1]  # Get latest entry
                    print(f"Step 3: Loaded latest step2 entry with {step2_data.get('total_matches', 0)} matches")
                else:
                    print("Step 3: No history entries found in step2.json")
                    return {}
            else:
                # Legacy format without history
                step2_data = file_data
                print(f"Step 3: Loaded step2.json with {step2_data.get('total_matches', 0)} matches")
        except Exception as e:
            print(f"Step 3: Error loading step2.json: {e}")
            return {}
    else:
        # It's already the data structure we need
        step2_data = summaries
    
    # Process the summary
    try:
        result = generate_summary(step2_data)
        if result:
            print(f"Step 3: Successfully generated summary with {result['match_count']} matches")
        else:
            print("Step 3: Failed to generate summary")
        
        return result or {}
    except Exception as e:
        print(f"Step 3: Error in json_summary: {e}")
        return {}

if __name__ == "__main__":
    # For testing directly
    import sys
    import asyncio
    
    print("Step 3 - Standalone Test")
    print("=" * 25)
    
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        print(f"Loading data from: {sys.argv[1]}")
        with open(sys.argv[1], 'r') as f:
            data = json.load(f)
            result = asyncio.run(json_summary(data))
            print(f"Generated summary JSON with {result.get('match_count', 0)} matches")
    else:
        # Try to load step2.json from default location
        step2_file = Path(__file__).parent.parent / "step2" / "step2.json"
        print(f"Looking for step2.json at: {step2_file}")
        
        if step2_file.exists():
            print("✅ Found step2.json")
            with open(step2_file, 'r') as f:
                file_data = json.load(f)
                
            # Handle history structure - get the latest entry
            if isinstance(file_data, dict) and "history" in file_data:
                if file_data["history"]:
                    data = file_data["history"][-1]  # Get latest entry
                    print(f"✅ Loaded latest step2 entry with {data.get('total_matches', 0)} matches")
                else:
                    print("❌ No history entries found in step2.json")
                    data = {}
            else:
                # Legacy format without history
                data = file_data
                print(f"✅ Loaded step2.json with {data.get('total_matches', 0)} matches")
                
            result = asyncio.run(json_summary(data))
            print(f"🎉 Generated summary JSON with {result.get('match_count', 0)} matches")
        else:
            print("❌ step2.json not found")
            print("💡 Run the pipeline first or provide a file path as argument")
