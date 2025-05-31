#!/usr/bin/env python3
"""
Step 5 - Odds & Environment Converter
Converts decimal odds to American format and formats environment data for display

This module processes Step 4 JSON data and:
1. Converts decimal odds to American format for betting markets
2. Formats temperature data from Celsius to Fahrenheit  
3. Summarizes environment data with detailed wind classifications
4. Prepares data for final display/print step

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

# Path constants
BASE_DIR = Path(__file__).parent
STEP4_JSON = BASE_DIR.parent / "step4" / "step4.json"

def get_eastern_time():
    """Get current Eastern time formatted string"""
    now = datetime.now(TZ)
    return now.strftime("%m/%d/%Y %I:%M:%S %p %Z")

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

def summarize_environment(env):
    """Format environment data for display"""
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
            
    # Note: We're explicitly not including pressure as requested
    return lines or ["No environment data available"]

def save_step5_json(step5_data, output_file="step5.json"):
    """Save the step5 data to step5.json file"""
    path = os.path.join(os.path.dirname(__file__), output_file)
    try:
        data = {"history": []}
        if os.path.exists(path): 
            with open(path, 'r') as f:
                existing = json.load(f)
                data = existing if isinstance(existing, dict) and existing.get("history") else {"history": [existing]}
        data["history"].append(step5_data)
        data.update({
            "last_updated": step5_data["generated_at"], 
            "total_entries": len(data["history"]), 
            "latest_match_count": step5_data["total_matches"]
        })
        data["ny_timestamp"] = get_eastern_time()
        
        with open(path, "w") as f: 
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving step5.json: {e}")
        return False

def odds_environment_converter():
    """Main function to process step4 data and convert odds/environment"""
    print("Step 5: Starting odds_environment_converter...")
    
    # Load step4 data
    if not STEP4_JSON.exists():
        print("Step 5: Error - step4.json not found")
        return None
        
    try:
        with open(STEP4_JSON, 'r') as f:
            step4_data = json.load(f)
    except Exception as e:
        print(f"Step 5: Error loading step4.json: {e}")
        return None
    
    # Get the latest history entry
    if "history" in step4_data and step4_data["history"]:
        latest_data = step4_data["history"][-1]
        matches = latest_data.get("matches", {})
    else:
        matches = step4_data.get("matches", {})
    
    print(f"Step 5: Processing {len(matches)} matches for odds/environment conversion")
    
    # Process each match - convert odds and environment data
    converted_matches = {}
    
    for match_id, match_data in matches.items():
        converted_match = match_data.copy()
        
        # Convert odds to American format with correct format detection
        # full_time_result: DECIMAL format -> decimal_to_american()
        if "full_time_result" in converted_match and converted_match["full_time_result"]:
            ftr = converted_match["full_time_result"]
            if isinstance(ftr, dict):
                for key, value in ftr.items():
                    if key != "time" and value is not None:
                        try:
                            converted_match["full_time_result"][key] = decimal_to_american(value)
                        except:
                            pass
        
        # spread: HONG KONG format -> hk_to_american()  
        if "spread" in converted_match and converted_match["spread"]:
            spread = converted_match["spread"]
            if isinstance(spread, dict):
                for key, value in spread.items():
                    if key not in ["time", "handicap", "line"] and value is not None:
                        try:
                            converted_match["spread"][key] = hk_to_american(value)
                        except:
                            pass
        
        # over_under: HONG KONG format -> hk_to_american()
        if "over_under" in converted_match and converted_match["over_under"]:
            ou = converted_match["over_under"]
            if isinstance(ou, dict):
                for line_key, line_data in ou.items():
                    if isinstance(line_data, dict):
                        for key, value in line_data.items():
                            if key not in ["time", "line"] and value is not None:
                                try:
                                    converted_match["over_under"][line_key][key] = hk_to_american(value)
                                except:
                                    pass
        
        # Convert environment data - wind from m/s to MPH
        if "environment" in converted_match and converted_match["environment"]:
            env = converted_match["environment"]
            
            # Convert wind speed from m/s to MPH and add Beaufort scale description
            if "wind_value" in env and "wind_unit" in env and env["wind_unit"] == "m/s":
                try:
                    wind_ms = float(env["wind_value"])
                    wind_mph = wind_ms * 2.237  # Convert m/s to mph
                    converted_match["environment"]["wind_value"] = round(wind_mph, 1)
                    converted_match["environment"]["wind_unit"] = "mph"
                    
                    # Add wind description based on Beaufort scale
                    if wind_mph < 1:
                        converted_match["environment"]["wind_description"] = "Calm"
                    elif wind_mph < 4:
                        converted_match["environment"]["wind_description"] = "Light Air"
                    elif wind_mph < 8:
                        converted_match["environment"]["wind_description"] = "Light Breeze"
                    elif wind_mph < 13:
                        converted_match["environment"]["wind_description"] = "Gentle Breeze"
                    elif wind_mph < 19:
                        converted_match["environment"]["wind_description"] = "Moderate Breeze"
                    elif wind_mph < 25:
                        converted_match["environment"]["wind_description"] = "Fresh Breeze"
                    elif wind_mph < 32:
                        converted_match["environment"]["wind_description"] = "Strong Breeze"
                    elif wind_mph < 39:
                        converted_match["environment"]["wind_description"] = "Near Gale"
                    elif wind_mph < 47:
                        converted_match["environment"]["wind_description"] = "Gale"
                    elif wind_mph < 55:
                        converted_match["environment"]["wind_description"] = "Strong Gale"
                    elif wind_mph < 64:
                        converted_match["environment"]["wind_description"] = "Storm"
                    elif wind_mph < 73:
                        converted_match["environment"]["wind_description"] = "Violent Storm"
                    else:
                        converted_match["environment"]["wind_description"] = "Hurricane"
                        
                except (ValueError, TypeError):
                    pass  # Keep original values if conversion fails
            
            env_summary = summarize_environment(converted_match["environment"])
            converted_match["environment_summary"] = env_summary
        
        converted_matches[match_id] = converted_match
    
    # Create step5 output structure
    step5_output = {
        "generated_at": get_eastern_time(),
        "total_matches": len(converted_matches),
        "matches": converted_matches
    }
    
    # Save to file
    if save_step5_json(step5_output):
        print(f"Step 5: Data saved to step5.json")
        print(f"Step 5: Successfully processed {len(converted_matches)} matches")
    else:
        print("Step 5: Failed to save JSON file")
    
    return step5_output

if __name__ == "__main__":
    print("Step 5: This module should be called from orchestrator.py")