#!/usr/bin/env python3
"""
Test script to verify step7 path resolution
"""
from pathlib import Path

# Test path resolution
FOOTBALL_BOT_DIR = Path("/root/CascadeProjects/Football_bot")
STEP5_JSON = FOOTBALL_BOT_DIR / "step5" / "step5.json"

print(f"FOOTBALL_BOT_DIR: {FOOTBALL_BOT_DIR}")
print(f"STEP5_JSON: {STEP5_JSON}")
print(f"STEP5_JSON exists: {STEP5_JSON.exists()}")

if STEP5_JSON.exists():
    print("✅ Path resolution working correctly!")
else:
    print("❌ Path resolution failed!")
