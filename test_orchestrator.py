#!/usr/bin/env python3
"""
Test Orchestrator - Football Bot
Test script to connect step1 → step2 → step3 pipeline
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo

# Add step2 and step3 to path so we can import them
sys.path.append(os.path.join(os.path.dirname(__file__), 'step2'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'step3'))
from step2 import extract_merge_summarize
from step3 import json_summary

async def test_orchestrator():
    print("🤖 Test Orchestrator Starting...")
    print("=" * 50)
    
    # Check if step1.json exists
    step1_file = "step1.json"
    if not os.path.exists(step1_file):
        print(f"❌ Error: {step1_file} not found!")
        print("💡 Run step1.py first to generate the data file")
        return False
    
    print(f"✅ Found {step1_file}")
    
    # Load step1 data
    try:
        with open(step1_file, 'r') as f:
            step1_data = json.load(f)
        print(f"✅ Loaded step1 data successfully")
        print(f"📊 Data timestamp: {step1_data.get('ny_timestamp', 'Unknown')}")
        
        # Show some basic stats
        live_matches = step1_data.get('live_matches', {})
        match_count = len(live_matches.get('results', []))
        print(f"⚽ Found {match_count} matches in data")
        
    except Exception as e:
        print(f"❌ Error loading {step1_file}: {e}")
        return False
    
    print("\n🔄 Running Step 2 processing...")
    print("-" * 30)
    
    # Run step2 processing
    try:
        summaries = await extract_merge_summarize(step1_data)
        print(f"✅ Step 2 completed successfully")
        print(f"📝 Generated {len(summaries)} match summaries")
        
        # Check if step2.json was created
        if os.path.exists("step2/step2.json"):
            print("✅ step2.json file created successfully")
        else:
            print("⚠️  step2.json file not found (might be saved elsewhere)")
            
    except Exception as e:
        print(f"❌ Error in step2 processing: {e}")
        return False

    print("\n🔄 Running Step 3 processing...")
    print("-" * 30)
    
    # Run step3 processing
    try:
        summary_data = await json_summary(summaries)
        print(f"✅ Step 3 completed successfully")
        print(f"📊 Generated summary with {summary_data.get('match_count', 0)} matches")
        print(f"🗂️  Categorized matches by status, competition, and venue")
        
        # Check if step3.json was created
        if os.path.exists("step3/step3.json"):
            print("✅ step3.json file created successfully")
        else:
            print("⚠️  step3.json file not found")
        
        # Show category stats
        categories = summary_data.get('categories', {})
        if categories:
            stats = categories.get('statistics', {})
            print(f"📈 Stats: {stats.get('with_odds', 0)} with odds, {stats.get('with_events', 0)} with events")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in step3 processing: {e}")
        return False

def main():
    print("🚀 Football Bot Test Orchestrator")
    print(f"🕒 Started at: {datetime.now(ZoneInfo('America/New_York')).strftime('%m/%d/%Y %I:%M:%S %p %Z')}")
    print("=" * 60)
    
    try:
        success = asyncio.run(test_orchestrator())
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 Test orchestration completed successfully!")
            print("✅ Step1 → Step2 → Step3 pipeline working")
        else:
            print("❌ Test orchestration failed")
            print("💡 Check the error messages above")
            
    except Exception as e:
        print(f"💥 Orchestrator crashed: {e}")
        
    print(f"🕒 Finished at: {datetime.now(ZoneInfo('America/New_York')).strftime('%m/%d/%Y %I:%M:%S %p %Z')}")

if __name__ == "__main__":
    main()
