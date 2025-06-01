#!/usr/bin/env python3
"""
STEP 1 – DATA FETCHER
--------------------
Fetches data from TheSports API and returns it as a dictionary.
No loops, no queues, no scheduling - runs once and exits.

IMPORTANT TERMINOLOGY:
- LIVE MATCHES = All matches from /match/detail_live API endpoint (broader category)
- IN-PLAY MATCHES = Only matches with status_id 2,3,4,5,6 (actively playing subset of live matches)
"""

import asyncio
import aiohttp
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)8s] %(message)s',
    handlers=[
        logging.FileHandler('step1.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Hard-coded credentials (consider moving to env-vars)
USER = "thenecpt"
SECRET = "0c55322e8e196d6ef9066fa4252cf386"

# API base and endpoints
BASE_URL = "https://api.thesports.com/v1/football"
URLS = {
    "live":        f"{BASE_URL}/match/detail_live",
    "details":     f"{BASE_URL}/match/recent/list",
    "odds":        f"{BASE_URL}/odds/history",
    "team":        f"{BASE_URL}/team/additional/list",
    "competition": f"{BASE_URL}/competition/additional/list",
    "country":     f"{BASE_URL}/country/list",
}

async def fetch_json(session: aiohttp.ClientSession, url: str, params: dict) -> dict:
    async with session.get(url, params=params) as response:
        response.raise_for_status()
        return await response.json()

async def fetch_live_matches(session):
    return await fetch_json(session, URLS["live"], {"user": USER, "secret": SECRET})

async def fetch_match_details(session, match_id):
    return await fetch_json(session, URLS["details"], {"user": USER, "secret": SECRET, "uuid": match_id})

async def fetch_match_odds(session, match_id):
    return await fetch_json(session, URLS["odds"], {"user": USER, "secret": SECRET, "uuid": match_id})

async def fetch_team_info(session, team_id):
    return await fetch_json(session, URLS["team"], {"user": USER, "secret": SECRET, "uuid": team_id})

async def fetch_competition_info(session, comp_id):
    return await fetch_json(session, URLS["competition"], {"user": USER, "secret": SECRET, "uuid": comp_id})

async def fetch_country_list(session):
    return await fetch_json(session, URLS["country"], {"user": USER, "secret": SECRET})

async def step1_main():
    """Fetch data once and return the data dict."""
    all_data = {
        "timestamp": datetime.now().isoformat(),
        "live_matches": {},
        "match_details": {},
        "match_odds": {},
        "team_info": {},
        "competition_info": {},
        "countries": {},
    }

    async with aiohttp.ClientSession() as session:
        live = await fetch_live_matches(session)
        all_data["live_matches"] = live

        matches = live.get("results", [])
        for match in matches:
            mid = match.get("id")

            detail_wrap = await fetch_match_details(session, mid)
            all_data["match_details"][mid] = detail_wrap

            all_data["match_odds"][mid] = await fetch_match_odds(session, mid)

            detail = {}
            if isinstance(detail_wrap, dict):
                res = detail_wrap.get("results") or detail_wrap.get("result") or []
                if isinstance(res, list) and res:
                    detail = res[0]

            home_id = detail.get("home_team_id") or match.get("home_team_id")
            away_id = detail.get("away_team_id") or match.get("away_team_id")
            comp_id = detail.get("competition_id") or match.get("competition_id")
            
            # Extract status_id from match details and add it to the main match object
            if detail.get("status_id") is not None:
                match["status_id"] = detail.get("status_id")

            if home_id and str(home_id) not in all_data["team_info"]:
                all_data["team_info"][str(home_id)] = await fetch_team_info(session, home_id)
            if away_id and str(away_id) not in all_data["team_info"]:
                all_data["team_info"][str(away_id)] = await fetch_team_info(session, away_id)
            if comp_id and str(comp_id) not in all_data["competition_info"]:
                all_data["competition_info"][str(comp_id)] = await fetch_competition_info(session, comp_id)

        all_data["countries"] = await fetch_country_list(session)

    return all_data

def save_to_json(data, filename):
    """Save data to a JSON file with pretty printing"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Data saved to {filename}")

def get_ny_time():
    """Get current time in New York timezone"""
    return datetime.now(ZoneInfo('America/New_York')).strftime('%m/%d/%Y %I:%M:%S %p')

def count_matches_by_status(live_matches_data):
    """Count matches by status from live matches data"""
    if not live_matches_data or "results" not in live_matches_data:
        print("DEBUG: No live_matches_data or no 'results' key")
        return {}, 0
    
    matches = live_matches_data["results"]
    total_matches = len(matches)
    status_counts = {}
    
    print(f"DEBUG: Found {total_matches} matches to analyze")
    
    # Get status ID to description mapping
    status_desc_map = {
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
    
    # Count matches by status_id
    status_found_count = 0
    for i, match in enumerate(matches):
        status_id = match.get("status_id")
        if status_id is not None:
            status_found_count += 1
            status_desc = status_desc_map.get(status_id, f"Unknown Status (ID: {status_id})")
            status_counts[status_desc] = status_counts.get(status_desc, 0) + 1
            if i < 3:  # Debug first 3 matches
                print(f"DEBUG: Match {i+1} has status_id: {status_id} -> {status_desc}")
    
    print(f"DEBUG: Found status_id in {status_found_count} out of {total_matches} matches")
    print(f"DEBUG: Status counts: {status_counts}")
    
    return status_counts, total_matches

def print_status_summary(live_matches_data):
    """Print and log a formatted summary of match counts by status"""
    status_counts, total_matches = count_matches_by_status(live_matches_data)
    
    if not status_counts:
        message = "Step 1: No match data available for status summary"
        print(message)
        logger.info(message)
        return
    
    # Create the summary lines
    summary_lines = [
        "=" * 80,
        "                        STEP 1 - MATCH STATUS SUMMARY                        ",
        "=" * 80,
        f"Total Matches: {total_matches}",
        "-" * 80
    ]
    
    # Sort by count (descending) for better readability
    sorted_statuses = sorted(status_counts.items(), key=lambda x: x[1], reverse=True)
    
    for status, count in sorted_statuses:
        summary_lines.append(f"{status}: {count} Matches")
    
    summary_lines.append("=" * 80)
    
    # Print to console
    for line in summary_lines:
        print(line)
    
    # Log to file
    logger.info("STEP 1 - MATCH STATUS SUMMARY")
    logger.info(f"Total Matches: {total_matches}")
    for status, count in sorted_statuses:
        logger.info(f"{status}: {count} Matches")

if __name__ == "__main__":
    try:
        # Run the main function
        result = asyncio.run(step1_main())
        
        # Get match count for the console output
        match_count = len(result.get('live_matches', {}).get('results', []))
        print(f"Step 1: Fetched data with {match_count} matches")
        
        # Generate status summary
        status_counts, total_matches = count_matches_by_status(result.get("live_matches", {}))
        
        # Add New York Eastern time timestamp to data
        ny_time = datetime.now(ZoneInfo("America/New_York"))
        result["ny_timestamp"] = ny_time.strftime("%m/%d/%Y %I:%M:%S %p")
        
        # Add status summary to JSON
        result["status_summary"] = status_counts
        result["total_matches_fetched"] = total_matches
        
        # Save to standard pipeline filename for compatibility
        save_to_json(result, 'step1.json')
        
        # Print completion time in New York time
        print(f"Data saved to step1.json at {get_ny_time()} (New York Time)")
        
        # Print status summary
        print_status_summary(result.get("live_matches", {}))
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise
