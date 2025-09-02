#!/usr/bin/env python3
"""
Development helper script for Pharmacy Finder
Run common development tasks from one place
"""
import argparse
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a shell command"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {cmd}")
        print(f"Error: {e}")
        return False

def start_server(host="0.0.0.0", port=8000, reload=True):
    """Start the FastAPI server"""
    print(f"🚀 Starting server on http://{host}:{port}")
    cmd = f"uvicorn app.main:app --host {host} --port {port}"
    if reload:
        cmd += " --reload"
    run_command(cmd)

def import_data():
    """Import pharmacy data from MINSAL"""
    print("📥 Importing pharmacy data...")
    run_command("python data/import_data.py")

def run_tests():
    """Run all tests"""
    print("🧪 Running tests...")
    test_files = [
        "tests/test_villa_alemana.py",
        "tests/test_web.py"
    ]
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"Running {test_file}...")
            run_command(f"python {test_file}")
        else:
            print(f"⚠️  Test file not found: {test_file}")

def explore_data():
    """Explore the MINSAL data structure"""
    print("🔍 Exploring data structure...")
    run_command("python data/explore_data.py")

def check_health():
    """Check if the server is running"""
    print("🏥 Checking server health...")
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running!")
            return True
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False

def show_stats():
    """Show database statistics"""
    print("📊 Database Statistics:")
    try:
        from app.database import PharmacyDatabase
        db = PharmacyDatabase()
        stats = db.get_pharmacy_count()
        print(f"   Total pharmacies: {stats['total']}")
        print(f"   Currently on duty: {stats['turno']}")
        print(f"   Regular pharmacies: {stats['regular']}")

        communes = db.get_all_communes()
        print(f"   Communes covered: {len(communes)}")
    except Exception as e:
        print(f"❌ Error getting stats: {e}")

def main():
    parser = argparse.ArgumentParser(description="Pharmacy Finder Development Helper")
    parser.add_argument("command", choices=[
        "start", "import", "test", "explore", "health", "stats", "setup"
    ], help="Command to run")

    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")

    args = parser.parse_args()

    if args.command == "start":
        start_server(args.host, args.port, not args.no_reload)
    elif args.command == "import":
        import_data()
    elif args.command == "test":
        run_tests()
    elif args.command == "explore":
        explore_data()
    elif args.command == "health":
        check_health()
    elif args.command == "stats":
        show_stats()
    elif args.command == "setup":
        print("🔧 Setting up Pharmacy Finder...")
        print("1. Installing dependencies...")
        run_command("pip install -r requirements.txt")
        print("2. Importing data...")
        import_data()
        print("3. Starting server...")
        start_server()

if __name__ == "__main__":
    main()
