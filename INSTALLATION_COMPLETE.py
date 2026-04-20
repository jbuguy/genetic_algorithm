#!/usr/bin/env python3
"""
Installation and Verification Complete
Summary of all created files and how to use them
"""

import os
from pathlib import Path

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_file_info(path, description):
    exists = "✓" if os.path.exists(path) else "✗"
    print(f"{exists} {path:<50} {description}")

print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║        GA VRPTW OPTIMIZER - APPLICATION SUITE CREATED               ║
║                                                                      ║
║              Your easy-to-use GUI and CLI application               ║
║              for genetic algorithm VRPTW experiments                ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
""")

print_section("🚀 QUICK START")
print("""
1. Start the Basic UI (easiest):
   $ python run_ui.py

2. Or start the Advanced UI (with comparisons):
   $ python run_advanced_ui.py

3. Or use the command-line tool:
   $ python ga_cli.py run C101.txt

4. Check your environment:
   $ python check_env.py
""")

print_section("📁 FILES CREATED")

files = [
    ("run_ui.py", "Main GUI launcher (RECOMMENDED)"),
    ("run_advanced_ui.py", "Advanced UI with comparisons"),
    ("ga_cli.py", "Command-line interface tool"),
    ("check_env.py", "Environment verification"),
    ("examples.py", "7 code usage examples"),
    ("vrptw/view/app.py", "Core GUI application code"),
    ("vrptw/view/advanced_app.py", "Advanced UI code"),
]

print("\n📍 Application Files:")
for file_path, desc in files:
    print_file_info(file_path, desc)

docs = [
    ("QUICK_START.md", "Step-by-step guide (READ FIRST!)"),
    ("UI_README.md", "Detailed UI documentation"),
    ("README_APP.md", "Complete reference guide"),
    ("IMPLEMENTATION_SUMMARY.md", "Implementation overview"),
    ("_THIS_FILE_.md", "How to verify installation"),
]

print("\n📚 Documentation Files:")
for file_path, desc in docs:
    if "_THIS_FILE_" not in file_path:
        print_file_info(file_path, desc)

print_section("⚙️ HOW TO USE")

print("""
╔─ Option 1: GUI (Graphical Interface) ─────────────────────╗
│                                                             │
│  Command: python run_ui.py                               │
│                                                             │
│  Features:                                                │
│  • Select data files by clicking                          │
│  • Choose operators with checkboxes                       │
│  • Set parameters with spinboxes                          │
│  • View progress with live updates                        │
│  • See results in real-time plots                         │
│                                                             │
│  Perfect for: Interactive experimentation                │
╚─────────────────────────────────────────────────────────────╝

╔─ Option 2: Advanced GUI (With Analysis) ──────────────────╗
│                                                             │
│  Command: python run_advanced_ui.py                       │
│                                                             │
│  Additional Features:                                     │
│  • Operator comparison tools                              │
│  • Multi-instance performance charts                      │
│  • Statistical analysis                                   │
│                                                             │
│  Perfect for: Detailed analysis & comparisons             │
╚─────────────────────────────────────────────────────────────╝

╔─ Option 3: Command-Line (CLI) ────────────────────────────╗
│                                                             │
│  Command: python ga_cli.py run C101.txt                   │
│                                                             │
│  Features:                                                │
│  • Full parameter control                                 │
│  • Batch processing                                       │
│  • Scriptable automation                                  │
│                                                             │
│  Perfect for: Batch runs & automation                     │
│                                                             │
│  More examples:                                           │
│  $ python ga_cli.py run R101.txt --runs 5                │
│  $ python ga_cli.py list instances                        │
│  $ python ga_cli.py list operators                        │
╚─────────────────────────────────────────────────────────────╝
""")

print_section("📋 AVAILABLE OPERATORS")

print("""
INITIALIZATION FUNCTIONS (5 options):
  • Random        - Greedy random insertion
  • Solomon       - Nearest neighbor insertion  
  • Cluster First - Cluster-first route-second
  • Savings       - Clarke-Wright savings
  • Mixed         - Random combination

CROSSOVER OPERATORS (5 options):
  • PMX           - Partially Mapped Crossover
  • Order (OX)    - Order Crossover
  • Cycle (CX)    - Cycle Crossover
  • Edge Assembly - Route-based (VRPTW optimized)
  • Route-Based   - Route-level operations

MUTATION OPERATORS (4 options):
  • Or-Opt        - Move/rotate segments
  • Scramble      - Shuffle subsequences
  • 2-Opt         - Swap edge pairs
  • Insert        - Random insertion

SELECTION METHODS (3 options):
  • Tournament    - Tournament selection
  • Roulette      - Fitness-proportionate
  • Truncation    - Best individual selection

DATA FILES (56 benchmark instances):
  • C101-C109     - 9 Clustered instances
  • R101-R112     - 12 Random instances  
  • RC101-RC108   - 8 Mixed instances
  • ... and more!
""")

print_section("📖 DOCUMENTATION GUIDE")

print("""
START HERE (Choose one):
  1. GUI Users     → Read QUICK_START.md (5 min read)
  2. CLI Users     → Read QUICK_START.md (10 min read)  
  3. Developers    → Read README_APP.md + examples.py

DETAILED RESOURCES:
  • QUICK_START.md           - Step-by-step guide
  • UI_README.md             - UI feature details
  • README_APP.md            - Complete reference
  • IMPLEMENTATION_SUMMARY.md - What was created
  • examples.py              - Code examples

HOW THEY CONNECT:
  QUICK_START.md
     ↓ (want more detail?)
  QUICK_START.md mentions → UI_README.md
     ↓ (want full reference?)
  UI_README.md mentions → README_APP.md
     ↓ (want code examples?)
  README_APP.md section → examples.py
""")

print_section("🎯 NEXT STEPS")

print("""
1. VERIFY INSTALLATION:
   $ python check_env.py

2. READ QUICK START (takes 5 minutes):
   Open: QUICK_START.md

3. START WITH GUI (most intuitive):
   $ python run_ui.py
   
4. FOLLOW THE WORKFLOW:
   • Click "📁 Browse Data Folder"
   • Select an instance (e.g., C101.txt)
   • Check operators you want to use
   • Set parameters
   • Click "▶️ Run Experiment"
   • View results in "Results" tab

5. EXPLORE MORE:
   • Try different operators
   • Read UI_README.md for advanced features
   • Use Advanced UI for comparisons
   • Try CLI for batch experiments
""")

print_section("🔍 FILE CHECKLIST")

essential_files = [
    "run_ui.py",
    "vrptw/view/app.py",
    "data/C101.txt",
    "ga/genetic_algorithm.py",
    "QUICK_START.md",
]

print("Essential files:")
for f in essential_files:
    exists = "✓" if os.path.exists(f) else "✗"
    print(f"  {exists} {f}")

print_section("⚡ PERFORMANCE TIPS")

print("""
For Quick Testing (5-10 minutes):
  Population: 20-30
  Generations: 50-100
  Mutation Rate: 0.2
  Runs: 1
  Instances: 1-2 small (C101, R101)

For Moderate Analysis (20-40 minutes):
  Population: 50
  Generations: 100-150
  Mutation Rate: 0.2
  Runs: 3
  Instances: 3-5 mixed

For Thorough Comparison (1-2 hours):
  Population: 100
  Generations: 200-300
  Mutation Rate: 0.2
  Runs: 5-10
  Instances: All or subset
""")

print_section("❓ TROUBLESHOOTING")

print("""
❌ "ModuleNotFoundError: No module named 'tkinter'"
   Solution: tkinter is usually pre-installed with Python
   Try: python3 --version && python3 -c "import tkinter"

❌ "Module matplotlib not found"
   Solution: pip install matplotlib
   Then: python check_env.py

❌ "Instance file not found"
   Solution: Use "Add Custom File" button in UI
   Or: Check that data/ folder exists and has .txt files

❌ UI doesn't start
   Solution: Run python check_env.py to diagnose
   Check: You're in the project root directory

❌ Results not showing
   Solution: Click "Refresh" in Results tab
   Check: results/ folder exists with JSON files
   Try: Run an experiment first

For more help:
  • Run: python check_env.py
  • Read: QUICK_START.md
  • Check: README_APP.md Troubleshooting section
""")

print_section("✅ YOU'RE ALL SET!")

print("""
Your GA VRPTW Optimizer is ready to use!

Three ways to proceed:

┌─ IF YOU PREFER GRAPHICAL INTERFACE ──────────────────┐
│ Run:  python run_ui.py                              │
│ Then: Click buttons, no code needed!                │
└──────────────────────────────────────────────────────┘

┌─ IF YOU PREFER COMMAND-LINE ─────────────────────────┐
│ Run:  python ga_cli.py run C101.txt                 │
│ Then: Check: python ga_cli.py --help               │
└──────────────────────────────────────────────────────┘

┌─ IF YOU WANT ADVANCED COMPARISON TOOLS ──────────────┐
│ Run:  python run_advanced_ui.py                      │
│ Then: Use comparison tab for analysis               │
└──────────────────────────────────────────────────────┘

FIRST-TIME USER RECOMMENDATION:
  1. python check_env.py       (verify everything works)
  2. python run_ui.py          (start GUI)
  3. Select C101.txt           (pick a small instance)
  4. Check Random, Edge Assembly, 2-Opt
  5. Click "Run Experiment"    (should take 1-2 minutes)
  6. View "Results" tab        (see the plots!)

Questions? Check the documentation:
  • QUICK_START.md    ← Read this first!
  • UI_README.md      ← For UI details
  • README_APP.md     ← For complete reference
  • examples.py       ← For code examples

Happy optimizing! 🚀
""")

print("="*70)
print("Created files are ready in the project directory.")
print("Start with: python run_ui.py")
print("="*70 + "\n")
