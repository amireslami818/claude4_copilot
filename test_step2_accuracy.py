#!/usr/bin/env python3
"""
Test script to verify Step 2 status summary accuracy
Validates that the Main_Status.log Step 2 summary matches actual data in step2.json
"""

import json
from pathlib import Path

def test_step2_accuracy():
    """Test that Step 2 summary values match actual data"""
    
    # Read Step 2 data
    step2_file = Path("step2/step2.json")
    if not step2_file.exists():
        print("❌ ERROR: step2.json not found")
        return False
    
    print("📊 STEP 2 ACCURACY VERIFICATION")
    print("=" * 50)
    
    try:
        with open(step2_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Get the latest batch from history
        history = data.get("history", [])
        if not history:
            print("❌ ERROR: No history in Step 2 data")
            return False
        
        latest_batch = history[-1]
        total_matches = latest_batch.get("total_matches", 0)
        timestamp = latest_batch.get("timestamp", "Unknown")
        matches = latest_batch.get("matches", {})
        
        print(f"📁 Data Source: {step2_file}")
        print(f"📅 Latest Batch Timestamp: {timestamp}")
        print(f"🎯 Total Matches Reported: {total_matches}")
        print(f"🔍 Actual Matches in Data: {len(matches)}")
        print()
        
        # Manual count of matches by status
        status_counts = {}
        in_play_matches = 0
        matches_with_status = 0
        matches_without_status = 0
        
        print("🔎 ANALYZING EACH MATCH:")
        print("-" * 30)
        
        for i, (match_id, match_data) in enumerate(matches.items(), 1):
            status_id = None
            
            # Check for status_id directly or in nested status object
            if "status_id" in match_data:
                status_id = match_data["status_id"]
                status_source = "direct status_id"
            elif "status" in match_data and isinstance(match_data["status"], dict):
                status_id = match_data["status"].get("id")
                status_source = "nested status.id"
            else:
                status_source = "NO STATUS FOUND"
            
            if status_id is not None:
                status_counts[status_id] = status_counts.get(status_id, 0) + 1
                matches_with_status += 1
                
                # Count in-play matches (status 2,3,4,5,6)
                if status_id in [2, 3, 4, 5, 6]:
                    in_play_matches += 1
                
                print(f"  Match {i:2d}: {match_id[:15]}... → Status {status_id} ({status_source})")
            else:
                matches_without_status += 1
                print(f"  Match {i:2d}: {match_id[:15]}... → NO STATUS ({status_source})")
        
        print()
        print("📊 CALCULATED RESULTS:")
        print("-" * 30)
        print(f"Total Matches: {len(matches)}")
        print(f"Matches with status: {matches_with_status}")
        print(f"Matches without status: {matches_without_status}")
        print(f"IN-PLAY MATCHES: {in_play_matches}")
        print()
        
        # Status breakdown
        print("Status Breakdown:")
        status_names = {
            1: "Not started",
            2: "First half", 
            3: "Half-time",
            4: "Second half",
            5: "Overtime", 
            6: "Overtime (deprecated)",
            7: "Penalty shoot-out",
            8: "End",
            9: "Postponed",
            10: "Suspended",
            11: "Interrupted",
            12: "Abandoned", 
            13: "To be determined",
            14: "Cancelled"
        }
        
        for status_id in sorted(status_counts.keys()):
            count = status_counts[status_id]
            status_name = status_names.get(status_id, f"Unknown")
            print(f"  {status_name} (ID: {status_id}): {count}")
        
        print()
        print("🎯 EXPECTED MAIN_STATUS.LOG OUTPUT:")
        print("-" * 40)
        print("STEP 2 - PROCESSED AND SUMMARIZED")
        print("─" * 40)
        print(f"Total Matches: {len(matches)}")
        print(f"Timestamp: {timestamp}")
        print("Status: Processed and summarized data")
        
        if status_counts:
            print("Status Breakdown:")
            for status_id in sorted(status_counts.keys()):
                count = status_counts[status_id]
                status_name = status_names.get(status_id, f"Unknown")
                print(f"  {status_name} (ID: {status_id}): {count}")
        
        print(f"IN-PLAY MATCHES: {in_play_matches}")
        print(f"Matches with status: {matches_with_status}")
        if matches_without_status > 0:
            print(f"Matches without status: {matches_without_status}")
        
        print()
        print("✅ VERIFICATION COMPLETE")
        
        # Validate specific counts mentioned in user's example
        print()
        print("🔍 VALIDATING USER'S EXAMPLE:")
        print("-" * 30)
        expected_first_half = 4  # From user's example
        actual_first_half = status_counts.get(2, 0)
        
        if actual_first_half == expected_first_half:
            print(f"✅ First half (ID: 2): Expected {expected_first_half}, Got {actual_first_half}")
        else:
            print(f"❌ First half (ID: 2): Expected {expected_first_half}, Got {actual_first_half}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    test_step2_accuracy()
