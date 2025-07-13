#!/usr/bin/env python3
"""Helper script to install dependencies."""

import subprocess
import sys

def run_command(command, description):
    """Run a command and report results."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout:
                print(f"Output: {result.stdout.strip()}")
        else:
            print(f"❌ {description} failed")
            print(f"Error: {result.stderr.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False

def main():
    print("Installing cmovies dependencies...")
    print("=" * 40)
    
    # Install Python dependencies
    success1 = run_command("uv sync", "Installing Python dependencies")
    
    # Install Playwright browsers
    success2 = run_command("playwright install chromium", "Installing Playwright browsers")
    
    if success1 and success2:
        print("\n🎉 All dependencies installed successfully!")
        print("\nYou can now run:")
        print("  python cli.py --search")
        print("  python cli.py --imdb-id tt0133093")
        print("  python simple_test.py")
    else:
        print("\n⚠️  Some installations failed. Please check the errors above.")
        print("\nManual installation:")
        print("  uv sync")
        print("  playwright install chromium")

if __name__ == "__main__":
    main()