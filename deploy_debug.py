#!/usr/bin/env python3
"""
Deploy Debug Version Script
Creates a separate Fly.io deployment for testing volume issues
"""

import os
import subprocess
import sys
import time

def run_command(cmd, description):
    """Run a command and handle output"""
    print(f"\n{description}...")
    print(f"Command: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
            
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
        if result.returncode == 0:
            print(f"SUCCESS: {description}")
            return True
        else:
            print(f"FAILED: {description} (Exit code: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT: {description} took too long")
        return False
    except Exception as e:
        print(f"ERROR: {description} - {e}")
        return False

def main():
    print("Fly.io Debug Deployment Script")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists("fly.toml"):
        print("ERROR: fly.toml not found. Run this from the project root.")
        sys.exit(1)
    
    # Verify fly.toml has debug app name
    with open("fly.toml", "r") as f:
        content = f.read()
        if "pharmacy-finder-debug" not in content:
            print("ERROR: fly.toml should contain 'pharmacy-finder-debug' as app name")
            sys.exit(1)
    
    print("Configuration verified:")
    print("  App name: pharmacy-finder-debug")
    print("  URL will be: https://pharmacy-finder-debug.fly.dev")
    
    # Step 1: Create the app (might already exist)
    print(f"\nStep 1: Create/verify Fly.io app")
    run_command("fly apps create pharmacy-finder-debug --org personal", "Create debug app")
    
    # Step 2: Create volume for the debug app
    print(f"\nStep 2: Create volume for debug app")
    run_command("fly volumes create pharmacy_data --region mia --size 1 --app pharmacy-finder-debug", "Create volume")
    
    # Step 3: Deploy
    print(f"\nStep 3: Deploy debug application")
    success = run_command("fly deploy --app pharmacy-finder-debug", "Deploy debug app")
    
    if success:
        print(f"\n" + "=" * 50)
        print("DEPLOYMENT SUCCESS!")
        print(f"Debug app URL: https://pharmacy-finder-debug.fly.dev")
        print(f"Debug endpoints:")
        print(f"  Volume check: https://pharmacy-finder-debug.fly.dev/admin/volume-debug")
        print(f"  Force update: https://pharmacy-finder-debug.fly.dev/admin/force-volume-update")
        print(f"  Database status: https://pharmacy-finder-debug.fly.dev/admin/database-status")
        print(f"\nTest commands:")
        print(f'curl "https://pharmacy-finder-debug.fly.dev/admin/volume-debug"')
        print(f'curl -X POST "https://pharmacy-finder-debug.fly.dev/admin/force-volume-update"')
    else:
        print(f"\nDEPLOYMENT FAILED!")
        print("Check the error messages above")

if __name__ == "__main__":
    main()