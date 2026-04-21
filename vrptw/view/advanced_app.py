#!/usr/bin/env python3
"""
Advanced GA VRPTW UI - Enhanced version with detailed Operator Dashboards
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import json
from pathlib import Path
from collections import defaultdict

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, '../..'))

from vrptw.view.app import GAApp
from stats import StatsManager


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
        
        ttk.Label(frame, text="Select instances to compare:").pack(anchor='w', pady=5)
        
        comparison_frame = ttk.Frame(frame)
        comparison_frame.pack(fill='both', expand=True, pady=10)
        
        scrollbar = ttk.Scrollbar(comparison_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.comparison_listbox = tk.Listbox(comparison_frame, yscrollcommand=scrollbar.set,
                                           selectmode='multiple', height=10)
        self.comparison_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.comparison_listbox.yview)
        
        self.refresh_comparison_list()
        
        # Control Panel
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill='x', pady=5)
        
        ttk.Label(control_frame, text="Analyze By:").pack(side='left', padx=5)
        self.analyze_var = tk.StringVar(value="crossover")
        ttk.Combobox(control_frame, textvariable=self.analyze_var, 
                     values=["selection", "crossover", "mutation"], 
                     state="readonly", width=15).pack(side='left', padx=5)
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill='x', pady=10)
        
        # Buttons
        ttk.Button(button_frame, text="📊 Detailed Dashboard",
                  command=self.generate_operator_dashboard).pack(side='left', padx=5)
        ttk.Button(button_frame, text="📈 Run-by-Run Boxplots",
                  command=self.compare_all).pack(side='left', padx=5)
        ttk.Button(button_frame, text="🔄 Refresh", 
                  command=self.refresh_comparison_list).pack(side='left', padx=5)
    
    def refresh_comparison_list(self):
        """Refresh the comparison listbox via StatsManager"""
        self.comparison_listbox.delete(0, tk.END)
        stats_mgr = StatsManager()
        
        if stats_mgr.results_dir.exists():
            for folder in sorted(d for d in stats_mgr.results_dir.iterdir() if d.is_dir()):
                run_count = len(list(folder.glob("run_*.json")))
                if run_count > 0:
                    self.comparison_listbox.insert(tk.END, f"{folder.name} ({run_count} runs)")
    
    def generate_operator_dashboard(self):
        """Generates the 3-panel dashboard (Fitness, Runtime, Convergence)"""
        selection = self.comparison_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select at least one instance")
            return
            
        selected_instances = [self.comparison_listbox.get(i).split()[0] for i in selection]
        operator_category = self.analyze_var.get()
        
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            stats_mgr = StatsManager()
            
            # Data structures to aggregate runs by operator name
            operator_data = defaultdict(lambda: {
                "fitness": [], 
                "runtime": [], 
                "convergence": []
            })
            
            # Parse JSONs
            for instance in selected_instances:
                instance_dir = stats_mgr.results_dir / instance
                for run_file in instance_dir.glob("run_*.json"):
                    data = stats_mgr.load_result(str(run_file))
                    
                    # Extract the specific operator used for this run
                    op_name = data.get("parameters", {}).get(operator_category, "Unknown")
                    fitness = data.get("best_fitness", float('inf'))
                    runtime = data.get("runtime", 0)
                    best_record = data.get("best_record", [])
                    
                    if fitness != float('inf'):
                        operator_data[op_name]["fitness"].append(fitness)
                        operator_data[op_name]["runtime"].append(runtime)
                        if best_record:
                            operator_data[op_name]["convergence"].append(best_record)

            if not operator_data:
                messagebox.showwarning("Warning", "No valid data found to plot.")
                return

            # Calculate means
            labels = list(operator_data.keys())
            avg_fitness = [np.mean(operator_data[op]["fitness"]) for op in labels]
            avg_runtime = [np.mean(operator_data[op]["runtime"]) for op in labels]
            
            # Plot Setup
            fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
            fig.suptitle(f"Operator Comparison — {operator_category.upper()}", 
                         fontsize=16, fontweight='bold')
            
            colors = plt.cm.tab10(np.linspace(0, 1, len(labels)))

            # Panel 1: Solution Quality (Lower is Better)
            bars1 = ax1.bar(labels, avg_fitness, color=colors, alpha=0.8)
            ax1.set_title("Solution Quality", fontweight='bold')
            ax1.set_ylabel("Avg best fitness (lower = better)")
            ax1.grid(True, alpha=0.3, axis='y', linestyle='--')
            
            # Add values on top of bars
            for bar in bars1:
                yval = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2, yval, 
                         f'{yval:.1f}', ha='center', va='bottom', fontweight='bold')

            # Panel 2: Time Consumption
            bars2 = ax2.bar(labels, avg_runtime, color=colors, alpha=0.5, edgecolor=colors, linewidth=3)
            ax2.set_title("⏱ Time Consumption", fontweight='bold')
            ax2.set_ylabel("Avg runtime (seconds)")
            ax2.grid(True, alpha=0.3, axis='y', linestyle='--')
            
            for bar in bars2:
                yval = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2, yval, 
                         f'{yval:.2f}s', ha='center', va='bottom', fontweight='bold')

            # Panel 3: Convergence
            ax3.set_title("Convergence (mean)", fontweight='bold')
            ax3.set_ylabel("Best fitness")
            ax3.set_xlabel("Generation")
            ax3.grid(True, alpha=0.3, linestyle='--')
            
            for idx, op in enumerate(labels):
                records = operator_data[op]["convergence"]
                if records:
                    # Pad arrays to same length if generations varied
                    max_len = max(len(r) for r in records)
                    padded_records = [r + [r[-1]]*(max_len-len(r)) for r in records]
                    mean_convergence = np.mean(padded_records, axis=0)
                    
                    ax3.plot(mean_convergence, label=op, color=colors[idx], linewidth=2.5)
            
            ax3.legend()

            # Format formatting
            for ax in [ax1, ax2, ax3]:
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.set_facecolor('#fafafa')

            plt.tight_layout()
            plt.show()

        except Exception as e:
            messagebox.showerror("Error", f"Error creating dashboard:\n{str(e)}")

    def compare_all(self):
        """Original Boxplot Comparison by Instance"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            stats_mgr = StatsManager()
            if not stats_mgr.results_dir.exists():
                messagebox.showwarning("Warning", "No results found")
                return
            
            instances = sorted([d.name for d in stats_mgr.results_dir.iterdir() if d.is_dir()])
            
            if not instances:
                return
            
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            axes = axes.flatten()
            
            for idx, instance_name in enumerate(instances[:4]):
                try:
                    instance_dir = stats_mgr.results_dir / instance_name
                    fitness_values = []
                    
                    for run_file in instance_dir.glob("run_*.json"):
                        data = stats_mgr.load_result(str(run_file))
                        val = data.get("best_fitness")
                        if val is not None and val != float("inf"):
                            fitness_values.append(val)
                    
                    if fitness_values:
                        axes[idx].boxplot(fitness_values, patch_artist=True,
                                        boxprops=dict(facecolor='#90CAF9'))
                        axes[idx].set_title(instance_name)
                        axes[idx].set_ylabel("Best Fitness")
                        axes[idx].grid(True, alpha=0.3, axis='y')
                except Exception as e:
                    axes[idx].text(0.5, 0.5, f"Error: {str(e)}", ha='center', va='center')
            
            for idx in range(len(instances[:4]), 4):
                axes[idx].axis('off')
            
            fig.suptitle("Run-by-Run Fitness Overview", fontsize=14, fontweight='bold')
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error creating comparison:\n{str(e)}")

if __name__ == "__main__":
    app = AdvancedGAApp()
    app.mainloop()