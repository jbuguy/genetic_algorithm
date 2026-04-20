#!/usr/bin/env python3
"""
Advanced GA VRPTW UI - Enhanced version with comparison features
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import json
from pathlib import Path
import threading
import subprocess

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, '../..'))

from vrptw.view.app import GAApp


class AdvancedGAApp(GAApp):
    """Extended GA App with advanced comparison features"""
    
    def setup_ui(self):
        """Override to add additional tabs"""
        # Create main notebook (tabs)
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
        
        # Tab 3: Comparison (NEW)
        comparison_frame = ttk.Frame(notebook)
        notebook.add(comparison_frame, text="Operator Comparison")
        self.setup_comparison_tab(comparison_frame)
    
    def setup_comparison_tab(self, parent):
        """Setup operator comparison tab"""
        frame = ttk.LabelFrame(parent, text="Compare Operators", padding=15)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Select instances to compare
        ttk.Label(frame, text="Select instances to compare:").pack(anchor='w', pady=5)
        
        comparison_frame = ttk.Frame(frame)
        comparison_frame.pack(fill='both', expand=True, pady=10)
        
        scrollbar = ttk.Scrollbar(comparison_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.comparison_listbox = tk.Listbox(comparison_frame, yscrollcommand=scrollbar.set,
                                           selectmode='multiple', height=10)
        self.comparison_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.comparison_listbox.yview)
        
        # Load available instances
        self.refresh_comparison_list()
        
        # Button frame
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="📊 Compare Selected",
                  command=self.compare_operators).pack(side='left', padx=5)
        ttk.Button(button_frame, text="🔄 Refresh", 
                  command=self.refresh_comparison_list).pack(side='left', padx=5)
        ttk.Button(button_frame, text="📈 Compare All",
                  command=self.compare_all).pack(side='left', padx=5)
    
    def refresh_comparison_list(self):
        """Refresh the comparison listbox"""
        self.comparison_listbox.delete(0, tk.END)
        results_dir = "results"
        
        if os.path.exists(results_dir):
            for folder in sorted(os.listdir(results_dir)):
                folder_path = os.path.join(results_dir, folder)
                if os.path.isdir(folder_path):
                    # Count runs
                    run_count = len([f for f in os.listdir(folder_path) 
                                   if f.startswith('run_') and f.endswith('.json')])
                    self.comparison_listbox.insert(tk.END, f"{folder} ({run_count} runs)")
    
    def compare_operators(self):
        """Compare selected operators"""
        selection = self.comparison_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select at least one instance")
            return
        
        selected_instances = [self.comparison_listbox.get(i).split()[0] for i in selection]
        
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            import plot_results
            
            # Create comparison figure
            n_instances = len(selected_instances)
            fig, axes = plt.subplots(1, n_instances, figsize=(6*n_instances, 5))
            
            if n_instances == 1:
                axes = [axes]
            
            for idx, instance_name in enumerate(selected_instances):
                try:
                    runs = plot_results.load_runs(instance_name)
                    fitness_values = [r["best_fitness"] for r in runs 
                                    if r.get("best_fitness") != float("inf")]
                    
                    if fitness_values:
                        axes[idx].boxplot(fitness_values, patch_artist=True)
                        axes[idx].set_title(instance_name)
                        axes[idx].set_ylabel("Best Fitness")
                        axes[idx].grid(True, alpha=0.3, axis='y')
                except Exception as e:
                    print(f"Error loading {instance_name}: {e}")
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error comparing operators:\n{str(e)}")
    
    def compare_all(self):
        """Compare all available instances"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            import plot_results
            
            results_dir = "results"
            if not os.path.exists(results_dir):
                messagebox.showwarning("Warning", "No results found")
                return
            
            instances = sorted([f for f in os.listdir(results_dir) 
                              if os.path.isdir(os.path.join(results_dir, f))])
            
            if not instances:
                messagebox.showwarning("Warning", "No instances found in results")
                return
            
            # Create comparison matrix
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            axes = axes.flatten()
            
            for idx, instance_name in enumerate(instances[:4]):
                try:
                    runs = plot_results.load_runs(instance_name)
                    fitness_values = [r["best_fitness"] for r in runs 
                                    if r.get("best_fitness") != float("inf")]
                    
                    if fitness_values:
                        axes[idx].boxplot(fitness_values, patch_artist=True)
                        axes[idx].set_title(instance_name)
                        axes[idx].set_ylabel("Best Fitness")
                        axes[idx].grid(True, alpha=0.3, axis='y')
                except Exception as e:
                    axes[idx].text(0.5, 0.5, f"Error: {str(e)}", 
                                 ha='center', va='center')
            
            # Hide unused subplots
            for idx in range(len(instances), 4):
                axes[idx].axis('off')
            
            fig.suptitle("Operator Comparison Overview", fontsize=14, fontweight='bold')
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error creating comparison:\n{str(e)}")


if __name__ == "__main__":
    try:
        app = AdvancedGAApp()
        app.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
