#!/usr/bin/env python3
"""
Advanced GA VRPTW UI - Enhanced version with detailed Operator Dashboards
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import json
import threading
from pathlib import Path
from collections import defaultdict

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, '../..'))

from vrptw.view.app import GAApp
from stats import StatsManager
from compare_operators import OperatorComparator, OperatorPlotter
from vrptw.instance import Instance
import logging

logger = logging.getLogger(__name__)


class AdvancedGAApp(GAApp):
    """Extended GA App with advanced comparison features"""
    
    def setup_ui(self):
        """Override to add additional tabs"""
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Configuration
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="Configuration")
        self.setup_config_tab(config_frame)
        
        # Tab 2: Results
        results_frame = ttk.Frame(notebook)
        notebook.add(results_frame, text="Results")
        self.setup_results_tab(results_frame)
        
        # Tab 3: Comparison
        comparison_frame = ttk.Frame(notebook)
        notebook.add(comparison_frame, text="Operator Comparison")
        self.setup_comparison_tab(comparison_frame)
    
    def setup_comparison_tab(self, parent):
        """Setup operator comparison tab"""
        frame = ttk.LabelFrame(parent, text="Compare Operators", padding=15)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Info label
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill='x', pady=(0, 10))
        ttk.Label(info_frame, text="Run operator comparisons on selected instances", 
                 foreground="gray").pack(anchor='w')
        
        # Instance Selection Section
        ttk.Label(frame, text="1. Select Instance:", font=("TkDefaultFont", 10, "bold")).pack(anchor='w', pady=(10, 5))
        self.setup_comparison_instance_section(frame)
        
        ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=10)
        
        # Parameters Section
        ttk.Label(frame, text="2. Configure Parameters:", font=("TkDefaultFont", 10, "bold")).pack(anchor='w', pady=(10, 5))
        self.setup_comparison_params_section(frame)
        
        ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=10)
        
        # Analysis Options
        ttk.Label(frame, text="3. Analysis Type:", font=("TkDefaultFont", 10, "bold")).pack(anchor='w', pady=(10, 5))
        analysis_frame = ttk.Frame(frame)
        analysis_frame.pack(fill='x', pady=5)
        
        self.analysis_var = tk.StringVar(value="all")
        ttk.Radiobutton(analysis_frame, text="Full Combination Analysis", 
                       variable=self.analysis_var, value="all").pack(anchor='w')
        ttk.Radiobutton(analysis_frame, text="Selection Operators Only", 
                       variable=self.analysis_var, value="selection").pack(anchor='w')
        ttk.Radiobutton(analysis_frame, text="Crossover Operators Only", 
                       variable=self.analysis_var, value="crossover").pack(anchor='w')
        ttk.Radiobutton(analysis_frame, text="Mutation Operators Only", 
                       variable=self.analysis_var, value="mutation").pack(anchor='w')
        
        ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=10)
        
        # Control Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill='x', pady=10)
        
        self.comp_run_button = ttk.Button(button_frame, text="▶  Start Comparison",
                                         command=self.run_operator_comparison)
        self.comp_run_button.pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="📊 View Results", 
                  command=self.show_comparison_results).pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="🔄 Refresh", 
                  command=self.refresh_comparison_state).pack(side='left', padx=5)
        
        # Status display
        self.comp_status_label = ttk.Label(frame, text="Ready", foreground="blue")
        self.comp_status_label.pack(anchor='w', pady=(10, 0))
        
        # Progress bar
        self.comp_progress_var = tk.DoubleVar()
        self.comp_progress = ttk.Progressbar(frame, variable=self.comp_progress_var,
                                            maximum=100, mode='determinate')
        self.comp_progress.pack(fill='x', pady=5)
    
    def setup_comparison_instance_section(self, parent):
        """Setup instance selection for comparison"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=5)
        
        ttk.Label(frame, text="Instance:").pack(side='left', padx=5)
        
        self.comp_instance_var = tk.StringVar(value="C101.txt")
        instance_combo = ttk.Combobox(frame, textvariable=self.comp_instance_var,
                                     state="readonly", width=20)
        
        # Populate with available instances
        data_dir = Path('data')
        if data_dir.exists():
            instances = sorted([f.name for f in data_dir.glob('*.txt')])
            instance_combo['values'] = instances
        
        instance_combo.pack(side='left', padx=5)
    
    def setup_comparison_params_section(self, parent):
        """Setup comparison parameters"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=5)
        
        # Population size
        ttk.Label(frame, text="Pop Size:").pack(side='left', padx=5)
        self.comp_pop_var = tk.StringVar(value="50")
        ttk.Spinbox(frame, from_=20, to=200, textvariable=self.comp_pop_var,
                   width=8).pack(side='left', padx=2)
        
        # Generations
        ttk.Label(frame, text="Generations:").pack(side='left', padx=5)
        self.comp_gen_var = tk.StringVar(value="100")
        ttk.Spinbox(frame, from_=50, to=500, textvariable=self.comp_gen_var,
                   width=8).pack(side='left', padx=2)
        
        # Mutation rate
        ttk.Label(frame, text="Mut Rate:").pack(side='left', padx=5)
        self.comp_mut_var = tk.StringVar(value="0.2")
        ttk.Spinbox(frame, from_=0.0, to=1.0, increment=0.1, textvariable=self.comp_mut_var,
                   width=8).pack(side='left', padx=2)
        
        # Runs
        ttk.Label(frame, text="Runs:").pack(side='left', padx=5)
        self.comp_runs_var = tk.StringVar(value="2")
        ttk.Spinbox(frame, from_=1, to=10, textvariable=self.comp_runs_var,
                   width=8).pack(side='left', padx=2)
    
    def run_operator_comparison(self):
        """Execute operator comparison in a background thread"""
        if self.is_running:
            messagebox.showwarning("Warning", "Experiment already running")
            return
        
        instance_name = self.comp_instance_var.get()
        if not instance_name:
            messagebox.showerror("Error", "Please select an instance")
            return
        
        try:
            pop_size = int(self.comp_pop_var.get())
            generations = int(self.comp_gen_var.get())
            mutation_rate = float(self.comp_mut_var.get())
            num_runs = int(self.comp_runs_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid parameter values")
            return
        
        # Disable button and show status
        self.is_running = True
        self.comp_run_button.config(state='disabled')
        self.comp_status_label.config(text="🔄 Running...", foreground="orange")
        
        # Run in background thread
        thread = threading.Thread(target=self._run_comparison_thread,
                                 args=(instance_name, pop_size, generations, 
                                      mutation_rate, num_runs))
        thread.daemon = True
        thread.start()
    
    def _run_comparison_thread(self, instance_name, pop_size, generations, mutation_rate, num_runs):
        """Background thread for running comparison"""
        try:
            instance_path = Path('data') / instance_name
            if not instance_path.exists():
                raise FileNotFoundError(f'Instance not found: {instance_name}')
            
            # Load instance
            instance = Instance(str(instance_path))
            
            # Create comparator and run analysis
            comparator = OperatorComparator(
                instance, pop_size=pop_size, generations=generations,
                mutation_rate=mutation_rate
            )
            
            analysis_type = self.analysis_var.get()
            
            # Run appropriate analysis
            if analysis_type == "all":
                # Full analysis
                logger.info("Starting full combination analysis...")
                selection_results = comparator.evaluate_operator_group('selection', num_runs=num_runs)
                self.comp_progress_var.set(25)
                self.update()
                
                crossover_results = comparator.evaluate_operator_group('crossover', num_runs=num_runs)
                self.comp_progress_var.set(50)
                self.update()
                
                mutation_results = comparator.evaluate_operator_group('mutation', num_runs=num_runs)
                self.comp_progress_var.set(75)
                self.update()
                
                combo_results = comparator.evaluate_combinations(num_runs=num_runs)
                self.comp_progress_var.set(85)
                self.update()
                
                # Generate plots
                instance_clean = instance_name.replace('.txt', '')
                output_dir = Path('results') / instance_clean / 'operator_comparison'
                
                plotter = OperatorPlotter()
                plotter.plot_group_comparison('selection', selection_results, output_dir)
                self.comp_progress_var.set(88)
                self.update()
                
                plotter.plot_group_comparison('crossover', crossover_results, output_dir)
                self.comp_progress_var.set(91)
                self.update()
                
                plotter.plot_group_comparison('mutation', mutation_results, output_dir)
                self.comp_progress_var.set(94)
                self.update()
                
                plotter.plot_combo_leaderboard(combo_results, output_dir)
                self.comp_progress_var.set(97)
                self.update()
                
                plotter.plot_combo_heatmap(combo_results, output_dir)
                self.comp_progress_var.set(100)
                self.update()
                
                messagebox.showinfo("Success", 
                    f"✓ Comparison complete!\n\nResults saved to:\n{output_dir}")
            
            elif analysis_type in ["selection", "crossover", "mutation"]:
                # Single operator type analysis
                logger.info(f"Analyzing {analysis_type} operators...")
                results = comparator.evaluate_operator_group(analysis_type, num_runs=num_runs)
                self.comp_progress_var.set(75)
                self.update()
                
                instance_clean = instance_name.replace('.txt', '')
                output_dir = Path('results') / instance_clean / 'operator_comparison'
                
                plotter = OperatorPlotter()
                plotter.plot_group_comparison(analysis_type, results, output_dir)
                self.comp_progress_var.set(100)
                self.update()
                
                messagebox.showinfo("Success",
                    f"✓ {analysis_type.capitalize()} analysis complete!\n\nResults saved to:\n{output_dir}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Comparison failed:\n{str(e)}")
            logger.exception(f"Comparison error: {e}")
        
        finally:
            self.is_running = False
            self.comp_run_button.config(state='normal')
            self.comp_status_label.config(text="✓ Ready", foreground="green")
            self.comp_progress_var.set(0)
    
    def show_comparison_results(self):
        """Open results directory in file manager"""
        try:
            instance_name = self.comp_instance_var.get()
            instance_clean = instance_name.replace('.txt', '')
            results_dir = Path('results') / instance_clean / 'operator_comparison'
            
            if not results_dir.exists():
                messagebox.showwarning("Info", "No results found. Run a comparison first.")
                return
            
            import subprocess
            if sys.platform == 'darwin':
                subprocess.Popen(['open', str(results_dir)])
            elif sys.platform == 'win32':
                subprocess.Popen(['explorer', str(results_dir)])
            else:
                subprocess.Popen(['xdg-open', str(results_dir)])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open results:\n{str(e)}")
    
    def refresh_comparison_state(self):
        """Refresh comparison UI state"""
        self.comp_status_label.config(text="✓ Ready", foreground="green")
        self.comp_progress_var.set(0)

if __name__ == "__main__":
    app = AdvancedGAApp()
    app.mainloop()