#!/usr/bin/env python3
"""
Advanced GA VRPTW UI Application Launcher
Includes operator comparison features
Usage: python run_advanced_ui.py
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
from vrptw.view.advanced_app import AdvancedGAApp

if __name__ == "__main__":
    try:
        app = AdvancedGAApp()
        app.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
