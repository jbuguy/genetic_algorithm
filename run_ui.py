#!/usr/bin/env python3
"""
GA VRPTW UI Application Launcher
Usage: python run_ui.py
"""

import sys
import os
from pathlib import Path

# Change to the script directory
script_dir = Path(__file__).parent.absolute()
os.chdir(script_dir)

# Add to path
sys.path.insert(0, str(script_dir))

# Import and run
from vrptw.view.app import GAApp

if __name__ == "__main__":
    try:
        app = GAApp()
        app.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
