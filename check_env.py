#!/usr/bin/env python3
"""
Environment Check and Installation Helper
Verifies all dependencies are installed and working
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print(f"❌ Python 3.7+ required (you have {version.major}.{version.minor})")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_module(module_name, pip_name=None):
    """Check if a module is installed"""
    try:
        __import__(module_name)
        print(f"✓ {module_name} installed")
        return True
    except ImportError:
        pip_name = pip_name or module_name
        print(f"❌ {module_name} not found")
        print(f"   Install with: pip install {pip_name}")
        return False


def check_directories():
    """Check if required directories exist"""
    required = ["data", "ga", "operators", "vrptw"]
    missing = []
    
    for directory in required:
        if not os.path.isdir(directory):
            missing.append(directory)
    
    if missing:
        print(f"❌ Missing directories: {', '.join(missing)}")
        return False
    
    print(f"✓ All required directories found")
    return True


def check_data_files():
    """Check if any data files exist"""
    data_dir = Path("data")
    if not data_dir.exists():
        print("❌ No data directory")
        return False
    
    txt_files = list(data_dir.glob("*.txt"))
    if not txt_files:
        print(f"⚠️  No data files found in data/")
        return False
    
    print(f"✓ Found {len(txt_files)} data files")
    return True


def main():
    """Run all checks"""
    print("\n" + "="*50)
    print("GA VRPTW - Environment Check")
    print("="*50 + "\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Core Modules", lambda: check_module("tkinter") and 
                                check_module("json")),
        ("Data Visualization", lambda: check_module("matplotlib") and
                                       check_module("numpy")),
        ("Project Structure", check_directories),
        ("Data Files", check_data_files),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append(False)
    
    print("\n" + "="*50)
    if all(results):
        print("✓ All checks passed! Ready to use.")
        print("\nQuick start:")
        print("  python run_ui.py              # Start UI")
        print("  python run_advanced_ui.py     # Advanced UI with comparisons")
        print("  python ga_cli.py run C101.txt # Command-line tool")
    else:
        print("❌ Some checks failed. See above for details.")
        print("\nTo install missing dependencies:")
        print("  pip install matplotlib numpy")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
