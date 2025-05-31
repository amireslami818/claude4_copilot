#!/usr/bin/env python3
"""
Test script to simulate how the orchestrator calls Step 6
This will help verify that our broken pipe fix works
"""

import sys
from pathlib import Path
import subprocess
import asyncio

# Add step6 to path
sys.path.append(str(Path(__file__).parent / 'step6'))

from step6 import pretty_print_matches

def test_direct_call():
    """Test calling step6 function directly like the orchestrator does"""
    print("Testing direct function call...")
    try:
        result = pretty_print_matches(pipeline_time=45.2)
        print(f"Direct call result: {result}")
        return True
    except Exception as e:
        print(f"Direct call failed: {e}")
        return False

async def test_subprocess_call():
    """Test calling step6 as subprocess with output capture like orchestrator might"""
    print("Testing subprocess call with output capture...")
    try:
        # Simulate how orchestrator captures output
        script_path = Path(__file__).parent / "step6" / "step6.py"
        process = await asyncio.create_subprocess_exec(
            sys.executable, str(script_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(Path(__file__).parent)
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            print("Subprocess call succeeded")
            print(f"Output length: {len(stdout)} bytes")
            return True
        else:
            print(f"Subprocess call failed with code {process.returncode}")
            print(f"Error: {stderr.decode('utf-8')}")
            return False
    except Exception as e:
        print(f"Subprocess call exception: {e}")
        return False

async def main():
    print("Testing Step 6 broken pipe fix...")
    
    # Test 1: Direct call (should work)
    success1 = test_direct_call()
    
    # Test 2: Subprocess call with output capture (this was causing broken pipe)
    success2 = await test_subprocess_call()
    
    print(f"\nResults:")
    print(f"Direct call: {'PASS' if success1 else 'FAIL'}")
    print(f"Subprocess call: {'PASS' if success2 else 'FAIL'}")
    
    if success1 and success2:
        print("✅ All tests passed - broken pipe fix appears to be working!")
    else:
        print("❌ Some tests failed")

if __name__ == "__main__":
    asyncio.run(main())
