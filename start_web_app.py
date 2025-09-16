#!/usr/bin/env python3
"""
Startup script for P&ID Diff Finder web application.
This script provides an easy way to start the web server.
"""

import sys
import subprocess
import webbrowser
import time
from pathlib import Path


def main() -> None:
    """Start the P&ID Diff Finder web application."""
    print("🚀 Starting P&ID Diff Finder Web Application...")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("app.py").exists():
        print(
            "❌ Error: app.py not found. Please run this script from the project root directory."
        )
        sys.exit(1)

    # Check if poetry is available
    try:
        subprocess.run(["poetry", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: Poetry not found. Please install Poetry first.")
        print("   Visit: https://python-poetry.org/docs/#installation")
        sys.exit(1)

    print("📦 Installing dependencies...")
    try:
        subprocess.run(["poetry", "install"], check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Error: Failed to install dependencies")
        sys.exit(1)

    print("\n🌐 Starting web server...")
    print("   Server will be available at: http://localhost:8000")
    print("   Press Ctrl+C to stop the server")
    print("-" * 50)

    # Start the server in a separate process
    try:
        # Give the server a moment to start
        import threading

        def open_browser() -> None:
            time.sleep(3)  # Wait 3 seconds for server to start
            webbrowser.open("http://localhost:8000")

        # Start browser opening in background
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()

        # Start the server
        subprocess.run(["poetry", "run", "python", "app.py"], check=True)

    except KeyboardInterrupt:
        print("\n\n👋 Shutting down P&ID Diff Finder...")
        print("Thank you for using P&ID Diff Finder!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
