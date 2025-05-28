#!/usr/bin/env python3
"""
Test Orchestrator - Football Bot
Test script to connect step1 → step2 → step3 → step4 pipeline
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo

# Add step2, step3, step4, and step5 to path so we can import them
sys.path.append(os.path.join(os.path.dirname(__file__), 'step2'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'step3'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'step4'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'step5'))
from step2 import extract_merge_summarize
from step3 import json_summary
from step4 import match_extracts
from step5 import odds_environment_converter

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
        
    except Exception as e:
        print(f"❌ Error in step3 processing: {e}")
        return False

    print("\n🔄 Running Step 4 processing...")
    print("-" * 30)
    
    # Run step4 processing
    try:
        extract_data = await match_extracts(summary_data)
        print(f"✅ Step 4 completed successfully")
        print(f"🏈 Generated match extracts for {extract_data.get('total_matches', 0)} matches")
        
        # Check if step4.json was created
        if os.path.exists("step4/step4.json"):
            print("✅ step4.json file created successfully")
        else:
            print("⚠️  step4.json file not found")
        
        # Show extract stats
        stats = extract_data.get('statistics', {})
        if stats:
            print(f"📊 Extract stats: {stats.get('matches_with_odds', 0)} with odds, {stats.get('matches_with_environment', 0)} with environment")
            status_breakdown = stats.get('by_status', {})
            if status_breakdown:
                status_summary = ", ".join([f"{status}: {count}" for status, count in status_breakdown.items()])
                print(f"📈 Status breakdown: {status_summary}")
        
    except Exception as e:
        print(f"❌ Error in step4 processing: {e}")
        return False

    print("\n🔄 Running Step 5 processing...")
    print("-" * 30)
    
    # Run step5 processing
    try:
        converted_data = odds_environment_converter()
        print(f"✅ Step 5 completed successfully")
        print(f"🎯 Converted odds and environment for {converted_data.get('total_matches', 0)} matches")
        
        # Check if step5.json was created
        if os.path.exists("step5/step5.json"):
            print("✅ step5.json file created successfully")
        else:
            print("⚠️  step5.json file not found")
        
        print("📊 Odds converted to American format")
        print("🌤️  Environment data formatted for display")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in step5 processing: {e}")
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
            print("✅ Step1 → Step2 → Step3 → Step4 → Step5 pipeline working")
        else:
            print("❌ Test orchestration failed")
            print("💡 Check the error messages above")
            
    except Exception as e:
        print(f"💥 Orchestrator crashed: {e}")
        
    print(f"🕒 Finished at: {datetime.now(ZoneInfo('America/New_York')).strftime('%m/%d/%Y %I:%M:%S %p %Z')}")

if __name__ == "__main__":
    main()
