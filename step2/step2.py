#!/usr/bin/env python3
# Renamed from step2_extract_merge_summarize.py

"""Step 2 – Extract, Merge, Summarize
This module consumes raw match payloads and produces cleaned-up summary dictionaries.
"""

from datetime import datetime
from zoneinfo import ZoneInfo
import re
import json
import os

# Timezone constant for Eastern Time
TZ = ZoneInfo("America/New_York")


def get_eastern_time():
    now = datetime.now(TZ)
    return now.strftime("%m/%d/%Y %I:%M:%S %p %Z")


# ---------------------------------------------------------------------------
# Field-extraction helpers
# ---------------------------------------------------------------------------

def extract_summary_fields(match: dict) -> dict:
    """Return a compact summary structure for a single match."""
    home_live = home_ht = away_live = away_ht = 0
    sd = match.get("score", [])
    if isinstance(sd, list) and len(sd) > 3:
        hs, as_ = sd[2], sd[3]
        if isinstance(hs, list) and len(hs) > 1:
            home_live, home_ht = hs[0], hs[1]
        if isinstance(as_, list) and len(as_) > 1:
            away_live, away_ht = as_[0], as_[1]

    home_scores = match.get("home_scores", [])
    away_scores = match.get("away_scores", [])
    if home_scores and home_live == 0:
        home_live = sum(home_scores)
    if away_scores and away_live == 0:
        away_live = sum(away_scores)

    return {
        "match_id": match.get("match_id") or match.get("id"),
        "status": {
            "id": match.get("status_id"),
            "description": match.get("status", ""),
            "match_time": match.get("match_time", 0),
        },
        "teams": {
            "home": {
                "name": match.get("home_team", "Unknown"),
                "score": {"current": home_live, "halftime": home_ht, "detailed": home_scores},
                "position": match.get("home_position"),
                "country": match.get("home_country"),
                "logo_url": match.get("home_logo"),
            },
            "away": {
                "name": match.get("away_team", "Unknown"),
                "score": {"current": away_live, "halftime": away_ht, "detailed": away_scores},
                "position": match.get("away_position"),
                "country": match.get("away_country"),
                "logo_url": match.get("away_logo"),
            },
        },
        "competition": {
            "name": match.get("competition", "Unknown"),
            "id": match.get("competition_id"),
            "country": match.get("country"),
            "logo_url": match.get("competition_logo"),
        },
        "round": match.get("round", {}),
        "venue": match.get("venue_id"),
        "referee": match.get("referee_id"),
        "neutral": match.get("neutral") == 1,
        "coverage": match.get("coverage", {}),
        "start_time": match.get("scheduled"),
        "odds": extract_odds(match),
        "environment": extract_environment(match),
        "events": extract_events(match),
        "fetched_at": get_eastern_time(),
    }


def extract_odds(match: dict) -> dict:
    raw_odds = match.get("odds", {}) or {}
    data = {"full_time_result": {}, "both_teams_to_score": {}, "over_under": {}, "spread": {}, "raw": raw_odds}

    def _safe_minute(v):
        if v is None:
            return None
        m = re.match(r"(\d+)", str(v))
        return int(m.group(1)) if m else None

    def filter_by_time(entries):
        pts = [( _safe_minute(ent[1]), ent) for ent in entries if isinstance(ent, (list, tuple)) and len(ent) > 1]
        pts = [(m, e) for m, e in pts if m is not None]
        in_window = [e for m, e in pts if 3 <= m <= 6]
        if in_window:
            return in_window
        under_ten = [(m, e) for m, e in pts if m < 10]
        return [] if not under_ten else [min(under_ten, key=lambda t: abs(t[0] - 4.5))[1]]

    for key, idxs in [("eu", (2,3,4)), ("asia", (2,3,4)), ("bs", (2,3,4))]:
        entry = (filter_by_time(raw_odds.get(key, [])) or [None])[0]
        if entry and len(entry) >= max(idxs)+1:
            if key == "eu":
                data["full_time_result"] = {"home": entry[2], "draw": entry[3], "away": entry[4], "timestamp": entry[0], "match_time": entry[1]}
            elif key == "asia":
                data["spread"] = {"handicap": entry[3], "home": entry[2], "away": entry[4], "timestamp": entry[0], "match_time": entry[1]}
            else:
                line = entry[3]
                data["over_under"][str(line)] = {"line": line, "over": entry[2], "under": entry[4], "timestamp": entry[0], "match_time": entry[1]}
                data["primary_over_under"] = data["over_under"][str(line)]

    for m in match.get("betting", {}).get("markets", []):
        if m.get("name") == "Both Teams to Score":
            for sel in m.get("selections", []):
                nm = sel.get("name", "").lower()
                if nm in ("yes","no"):
                    data["both_teams_to_score"][nm] = sel.get("odds")
    return data


def extract_environment(match: dict) -> dict:
    env = match.get("environment", {}) or {}
    parsed = {"raw": env}
    wc = env.get("weather")
    parsed["weather"] = int(wc) if isinstance(wc, str) and wc.isdigit() else wc
    desc = {1:"Sunny",2:"Partly Cloudy",3:"Cloudy",4:"Overcast",5:"Foggy",6:"Light Rain",7:"Rain",8:"Heavy Rain",9:"Snow",10:"Thunder"}
    parsed["weather_description"] = desc.get(parsed["weather"], "Unknown")

    for key in ("temperature","wind","pressure","humidity"): 
        val = env.get(key)
        parsed[key] = val
        m = re.match(r"([\d.-]+)\s*([^\d]*)", str(val))
        num, unit = (float(m.group(1)), m.group(2).strip()) if m else (None, None)
        parsed[f"{key}_value"] = num
        parsed[f"{key}_unit"] = unit

    wv = parsed.get("wind_value") or 0
    mph = wv*2.237 if "m/s" in str(env.get("wind","")).lower() else wv
    descs = [(1,"Calm"),(4,"Light Air"),(8,"Light Breeze"),(13,"Gentle Breeze"),(19,"Moderate Breeze"),(25,"Fresh Breeze"),(32,"Strong Breeze"),(39,"Near Gale"),(47,"Gale"),(55,"Strong Gale"),(64,"Storm"),(73,"Violent Storm")]
    parsed["wind_description"] = next((label for lim,label in descs if mph < lim), "Hurricane")
    return parsed


def extract_events(match: dict) -> list:
    return [{"type": ev.get("type"),"time":ev.get("time"),"team":ev.get("team"),"player":ev.get("player"),"detail":ev.get("detail")} for ev in match.get("events",[]) if ev.get("type") in {"goal","yellowcard","redcard","penalty","substitution"}]


def save_match_summaries(summaries: list, output_file: str = "step2.json") -> bool:
    grouped = {str(s.get("match_id")): s for s in summaries if s.get("match_id")}
    batch = {"timestamp": datetime.now(TZ).isoformat(), "total_matches": len(grouped), "matches": grouped}
    path = os.path.join(os.path.dirname(__file__), output_file)
    try:
        data = {"history": []}
        if os.path.exists(path): data = json.load(open(path)) if isinstance(json.load(open(path)), dict) and json.load(open(path)).get("history") else {"history": [json.load(open(path))]}
        data["history"].append(batch)
        data.update({"last_updated": batch["timestamp"], "total_entries": len(data["history"]), "latest_match_count": batch["total_matches"]})
        
        # Add NY timestamp at the end like step1
        data["ny_timestamp"] = get_eastern_time()
        
        with open(path, "w") as f: json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except:
        return False


def first_result(mapping: dict, key):
    wrap = mapping.get(str(key)) if key is not None else None
    if isinstance(wrap, dict):
        res = wrap.get("results") or wrap.get("result") or []
        return res[0] if isinstance(res, list) and res else {}
    return {}


def merge_and_summarize(live: dict, payload: dict) -> dict:
    mid = live.get("id") or live.get("match_id")
    dm, om, tm, cm = payload.get("match_details",{}), payload.get("match_odds",{}), payload.get("team_info",{}), payload.get("competition_info",{})
    cw = payload.get("countries",{}); cl = cw.get("results") or cw.get("result") or []; countries={c.get("id"):c.get("name") for c in cl if isinstance(c,dict)}
    detail, odds_wrap = first_result(dm,mid), om.get(mid,{})
    odds_struct = {mt:od for mk in odds_wrap.get("results",{}).values() for mt,od in mk.items() if isinstance(mk,dict)}
    home, away = first_result(tm, live.get("home_team_id") or detail.get("home_team_id")), first_result(tm, live.get("away_team_id") or detail.get("away_team_id"))
    comp = first_result(cm, live.get("competition_id") or detail.get("competition_id"))
    merged = {**live,**detail, "odds": odds_struct, "environment": detail.get("environment", live.get("environment",{})), "events": detail.get("events", live.get("events",[])),
              "home_team": home.get("name") or live.get("home_name"), "home_logo": home.get("logo"), "home_country": home.get("country") or countries.get(home.get("country_id")),
              "away_team": away.get("name") or live.get("away_name"), "away_logo": away.get("logo"), "away_country": away.get("country") or countries.get(away.get("country_id")),
              "competition": comp.get("name") or live.get("competition_name"), "competition_logo": comp.get("logo"), "country": comp.get("country") or countries.get(comp.get("country_id")),
              "odds_raw": odds_wrap}
    return extract_summary_fields(merged)

async def extract_merge_summarize(data: dict):
    print("Step 2: Starting extract_merge_summarize...")
    matches = (data.get("live_matches",{}).get("results") or data.get("live_matches",{}).get("matches") or [])
    print(f"Step 2: Found {len(matches)} matches to process")
    summaries = [merge_and_summarize(m, data) for m in matches]
    print(f"Step 2: Created {len(summaries)} summaries")
    if summaries:
        if save_match_summaries(summaries):
            print(f"Step 2 produced {len(summaries)} summaries and saved to step2.json")
        else:
            print(f"Step 2 produced {len(summaries)} summaries but failed to save JSON file")
    else:
        print("Step 2 processed payload but found no matches to summarize")
    print("Step 2: Processing completed")
    return summaries

if __name__ == "__main__":
    print("Step 2: This module should be called from orchestrator.py")
