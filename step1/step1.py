#!/usr/bin/env python3
"""
STEP 1 – DATA FETCHER
--------------------
Fetches data from TheSports API and returns it as a dictionary.
No loops, no queues, no scheduling - runs once and exits.
"""

import asyncio
import aiohttp
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo

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

if __name__ == "__main__":
    try:
        # Run the main function
        result = asyncio.run(step1_main())
        
        # Get match count for the console output
        match_count = len(result.get('live_matches', {}).get('results', []))
        print(f"Step 1: Fetched data with {match_count} matches")
        
        # Create a timestamp for the filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'step1_output_{timestamp}.json'
        
        # Save the complete data to a JSON file
        save_to_json(result, output_file)
        
        # Print completion time in New York time
        print(f"Process completed at {get_ny_time()} (New York Time)")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise
