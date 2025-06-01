#!/usr/bin/env python3
"""
Quick test for step5 status summary functionality
"""
import sys
import os
sys.path.append('/root/CascadeProjects/Football_bot/step5')

from step5 import odds_environment_converter

if __name__ == "__main__":
    print("Testing step5 status summary functionality...")
    result = odds_environment_converter()
    if result:
        print(f"✓ Test completed successfully!")
        print(f"✓ Processed {result['total_matches']} matches")
    else:
        print("✗ Test failed")
