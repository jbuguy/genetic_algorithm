#!/usr/bin/env python3
"""
GA VRPTW UI Application
A modern interface for running genetic algorithm experiments on VRPTW instances
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
from pathlib import Path
import threading
import json
import time

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, '../..'))
sys.path.insert(0, current_dir)

# Now import the modules
from ga.genetic_algorithm import GeneticAlgorithm
from vrptw.instance import Instance
from vrptw.fitness import calculateFitness
from vrptw.generateInit import (
    random_generator, solomon_generator, 
    cluster_first_route_second, savings_heuristic, make_mixed_initializer
)
from operators.crossover import (
    PMXCrossOver, crossover_ox, crossover_cx, 
    edgeAssemblyCrossover, route_based_crossover
)
from operators.mutation import orOpt, mutate_scramble, twoOpt, mutate_route_rebuild
from ga.selection import tournamentSelection, rouletteSelection, selection_truncation

# Try importing plot_results from parent directory
try:
    import plot_results
except ImportError:
    import sys
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    import plot_results

from stats import StatsManager

# Available operators
INITIALIZERS = {
    "Random": random_generator,
    "Solomon": solomon_generator,
    "Cluster First": cluster_first_route_second,
    "Savings": savings_heuristic,
    "Mixed": lambda inst: make_mixed_initializer()(inst)
}

CROSSOVERS = {
    "PMX": PMXCrossOver,
    "Order (OX)": crossover_ox,
    "Cycle (CX)": crossover_cx,
    "Edge Assembly": edgeAssemblyCrossover,
    "Route-Based": route_based_crossover
}

MUTATIONS = {
    "Or-Opt": orOpt,
    "Scramble": mutate_scramble,
    "2-Opt": twoOpt,
    "Route Rebuild": mutate_route_rebuild,
}

SELECTIONS = {
    "Tournament": tournamentSelection,
    "Roulette": rouletteSelection,
    "Truncation": selection_truncation
}


class GAApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GA VRPTW Optimizer")
        self.geometry("1000x800")
        self.configure(bg="#f0f0f0")
        
        # Store selected data
        self.selected_instances = []
        self.selected_initializers = []
        self.selected_crossovers = []
        self.selected_mutations = []
        self.selected_selection = "Tournament"
        self.is_running = False
        self.stats_manager = StatsManager()
        
        self.setup_ui()
        self.center_window()
    
    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        """Setup the main UI"""
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
    
    def setup_config_tab(self, parent):
        """Setup configuration tab"""
        # Use canvas with scrollbar for better layout
        canvas = tk.Canvas(parent, bg="#f0f0f0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Data Selection Section
        self.setup_data_section(scrollable_frame)
        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill='x', pady=15)
        
        # Operators Selection Section
        self.setup_operators_section(scrollable_frame)
        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill='x', pady=15)
        
        # Parameters Section
        self.setup_parameters_section(scrollable_frame)
        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill='x', pady=15)
        
        # Control Buttons
        self.setup_control_buttons(scrollable_frame)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_data_section(self, parent):
        """Setup data file selection"""
        frame = ttk.LabelFrame(parent, text="1. Select Data Files", padding=15)
        frame.pack(fill='x', pady=10)
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="📁 Browse Data Folder", 
                  command=self.browse_data_files).pack(side='left', padx=5)
        ttk.Button(button_frame, text="➕ Add Custom File", 
                  command=self.add_custom_file).pack(side='left', padx=5)
        ttk.Button(button_frame, text="🗑️ Clear", 
                  command=self.clear_instances).pack(side='left', padx=5)
        
        # Listbox for selected files
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill='both', expand=True, pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.instances_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=6)
        self.instances_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.instances_listbox.yview)
        
        self.instances_label = ttk.Label(frame, text="Selected: 0 files")
        self.instances_label.pack(anchor='w')
    
    def setup_operators_section(self, parent):
        """Setup operator selection"""
        frame = ttk.LabelFrame(parent, text="2. Select Operators", padding=15)
        frame.pack(fill='x', pady=10)
        
        # Initializers
        init_frame = ttk.LabelFrame(frame, text="Initialization", padding=10)
        init_frame.pack(fill='x', pady=10)
        
        self.init_vars = {}
        for name in INITIALIZERS.keys():
            var = tk.BooleanVar(value=False)
            self.init_vars[name] = var
            ttk.Checkbutton(init_frame, text=name, variable=var,
                           command=self.on_operators_changed).pack(anchor='w')
        
        # Crossovers
        cross_frame = ttk.LabelFrame(frame, text="Crossover", padding=10)
        cross_frame.pack(fill='x', pady=10)
        
        self.cross_vars = {}
        for name in CROSSOVERS.keys():
            var = tk.BooleanVar(value=False)
            self.cross_vars[name] = var
            ttk.Checkbutton(cross_frame, text=name, variable=var,
                           command=self.on_operators_changed).pack(anchor='w')
        
        # Mutations
        mut_frame = ttk.LabelFrame(frame, text="Mutation", padding=10)
        mut_frame.pack(fill='x', pady=10)
        
        self.mut_vars = {}
        for name in MUTATIONS.keys():
            var = tk.BooleanVar(value=False)
            self.mut_vars[name] = var
            ttk.Checkbutton(mut_frame, text=name, variable=var,
                           command=self.on_operators_changed).pack(anchor='w')
        
        # Selection
        sel_frame = ttk.LabelFrame(frame, text="Selection", padding=10)
        sel_frame.pack(fill='x', pady=10)
        
        self.selection_var = tk.StringVar(value="Tournament")
        for name in SELECTIONS.keys():
            ttk.Radiobutton(sel_frame, text=name, variable=self.selection_var,
                           value=name).pack(anchor='w')
        
        self.operators_label = ttk.Label(frame, text="Selected: 0 combinations", 
                                        foreground="blue")
        self.operators_label.pack(anchor='w', pady=10)
    
    def setup_parameters_section(self, parent):
        """Setup GA parameters"""
        frame = ttk.LabelFrame(parent, text="3. GA Parameters", padding=15)
        frame.pack(fill='x', pady=10)
        
        # Population size
        ttk.Label(frame, text="Population Size:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.pop_size_var = tk.StringVar(value="50")
        ttk.Spinbox(frame, from_=10, to=500, textvariable=self.pop_size_var, 
                   width=10).grid(row=0, column=1, sticky='w', padx=5, pady=5)
        
        # Generations
        ttk.Label(frame, text="Generations:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.gen_var = tk.StringVar(value="100")
        ttk.Spinbox(frame, from_=10, to=1000, textvariable=self.gen_var, 
                   width=10).grid(row=1, column=1, sticky='w', padx=5, pady=5)
        
        # Mutation rate
        ttk.Label(frame, text="Mutation Rate:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.mut_rate_var = tk.StringVar(value="0.2")
        ttk.Spinbox(frame, from_=0.0, to=1.0, increment=0.1, textvariable=self.mut_rate_var,
                   width=10).grid(row=2, column=1, sticky='w', padx=5, pady=5)
        
        # Number of runs
        ttk.Label(frame, text="Number of Runs:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.runs_var = tk.StringVar(value="3")
        ttk.Spinbox(frame, from_=1, to=20, textvariable=self.runs_var,
                   width=10).grid(row=3, column=1, sticky='w', padx=5, pady=5)
    
    def setup_control_buttons(self, parent):
        """Setup control buttons"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=20)
        
        self.run_button = ttk.Button(frame, text="▶️ Run Experiment", 
                                    command=self.run_experiment)
        self.run_button.pack(side='left', padx=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(frame, variable=self.progress_var, 
                                       maximum=100, mode='determinate')
        self.progress.pack(side='left', fill='x', expand=True, padx=5)
        
        self.status_label = ttk.Label(frame, text="Ready")
        self.status_label.pack(side='left', padx=10)
    
    def setup_results_tab(self, parent):
        """Setup results tab"""
        frame = ttk.LabelFrame(parent, text="Plot Results", padding=15)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        ttk.Label(frame, text="Instance:").pack(anchor='w', pady=5)
        
        self.results_instances = tk.Listbox(frame, height=15)
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=self.results_instances.yview)
        self.results_instances.config(yscrollcommand=scrollbar.set)
        self.results_instances.pack(side='left', fill='both', expand=True, pady=5)
        scrollbar.pack(side='right', fill='y')
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="📊 Plot Selected", 
                  command=self.plot_selected).pack(side='left', padx=5)
        ttk.Button(button_frame, text="🔄 Refresh", 
                  command=self.refresh_results).pack(side='left', padx=5)
        
        self.refresh_results()
    
    def browse_data_files(self):
        """Browse and select data files from data/ folder"""
        data_dir = "data"
        if not os.path.exists(data_dir):
            messagebox.showerror("Error", f"Data folder not found: {data_dir}")
            return
        
        files = filedialog.askopenfilenames(
            initialdir=data_dir,
            title="Select data files",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        for file in files:
            if file not in self.selected_instances:
                self.selected_instances.append(os.path.basename(file))
        
        self.update_instances_display()
    
    def add_custom_file(self):
        """Add a custom file"""
        file = filedialog.askopenfilename(
            title="Select a data file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file and os.path.basename(file) not in self.selected_instances:
            self.selected_instances.append(os.path.basename(file))
        self.update_instances_display()
    
    def clear_instances(self):
        """Clear all selected instances"""
        self.selected_instances = []
        self.update_instances_display()
    
    def update_instances_display(self):
        """Update the instances listbox display"""
        self.instances_listbox.delete(0, tk.END)
        for instance in self.selected_instances:
            self.instances_listbox.insert(tk.END, instance)
        self.instances_label.config(text=f"Selected: {len(self.selected_instances)} files")
    
    def on_operators_changed(self):
        """Update operator count display"""
        init_count = sum(1 for v in self.init_vars.values() if v.get())
        cross_count = sum(1 for v in self.cross_vars.values() if v.get())
        mut_count = sum(1 for v in self.mut_vars.values() if v.get())
        
        total = max(1, init_count) * max(1, cross_count) * max(1, mut_count)
        self.operators_label.config(text=f"Selected: {total} combinations")
    
    def run_experiment(self):
        """Run the GA experiment"""
        # Validation
        if not self.selected_instances:
            messagebox.showwarning("Warning", "Please select at least one data file")
            return
        
        init_count = sum(1 for v in self.init_vars.values() if v.get())
        cross_count = sum(1 for v in self.cross_vars.values() if v.get())
        mut_count = sum(1 for v in self.mut_vars.values() if v.get())
        
        if init_count == 0 or cross_count == 0 or mut_count == 0:
            messagebox.showwarning("Warning", 
                                  "Please select at least one option for each operator type")
            return
        
        # Disable button during run
        self.run_button.config(state='disabled')
        self.is_running = True
        
        # Run in background thread
        thread = threading.Thread(target=self._run_experiment_thread)
        thread.start()
    
    def _run_experiment_thread(self):
        """Run experiment in background"""
        try:
            # Get parameters
            pop_size = int(self.pop_size_var.get())
            generations = int(self.gen_var.get())
            mut_rate = float(self.mut_rate_var.get())
            num_runs = int(self.runs_var.get())
            
            # Get selected operators
            selected_inits = [name for name, var in self.init_vars.items() if var.get()]
            selected_cross = [name for name, var in self.cross_vars.items() if var.get()]
            selected_muts = [name for name, var in self.mut_vars.items() if var.get()]
            selected_sel = self.selection_var.get()
            
            total_experiments = (len(self.selected_instances) * 
                               len(selected_inits) * 
                               len(selected_cross) * 
                               len(selected_muts))
            
            current = 0
            
            # Run experiments
            for instance_name in self.selected_instances:
                for init_name in selected_inits:
                    for cross_name in selected_cross:
                        for mut_name in selected_muts:
                            current += 1
                            progress = (current / total_experiments) * 100
                            self.progress_var.set(progress)
                            
                            status = f"Running {instance_name} ({init_name}, {cross_name}, {mut_name})..."
                            self.status_label.config(text=status)
                            self.update_idletasks()
                            
                            # Run the GA
                            self.run_ga_experiment(
                                instance_name, init_name, cross_name, mut_name,
                                selected_sel, pop_size, generations, mut_rate, num_runs
                            )
            
            self.status_label.config(text="✓ Experiment completed")
            self.refresh_results()
            messagebox.showinfo("Success", "Experiment completed successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error running experiment:\n{str(e)}")
            self.status_label.config(text="✗ Error occurred")
        finally:
            self.run_button.config(state='normal')
            self.is_running = False
    
    def run_ga_experiment(self, instance_name, init_name, cross_name, mut_name,
                         sel_name, pop_size, generations, mut_rate, num_runs):
        """Run a single GA experiment"""
        data_dir = "data"
        instance_path = os.path.join(data_dir, instance_name)
        
        if not os.path.exists(instance_path):
            instance_path = instance_name  # Try full path
        
        if not os.path.exists(instance_path):
            raise FileNotFoundError(f"Instance file not found: {instance_path}")
        
        instance = Instance(instance_path)
        
        # Get operator functions
        init_fn = INITIALIZERS[init_name]
        cross_fn = CROSSOVERS[cross_name]
        mut_fn = MUTATIONS[mut_name]
        sel_fn = SELECTIONS[sel_name]
        
        # Run GA multiple times
        params = {
            "population_size": pop_size,
            "generations": generations,
            "mutation_rate": mut_rate,
            "initializer": init_name,
            "crossover": cross_name,
            "mutation": mut_name,
            "selection": sel_name
        }
        
        for run_num in range(num_runs):
            ga = GeneticAlgorithm(
                instance=instance,
                fnFitness=calculateFitness,
                fnInitPopulation=init_fn,
                fnSelection=sel_fn,
                fnCrossover=cross_fn,
                fnMutation=mut_fn,
                populationSize=pop_size,
                generations=generations,
                mutationRate=mut_rate
            )
            
            result = ga.run()
            
            # Save result
            self.stats_manager.save_result(result, instance_name, run_num + 1, params)
            
            print(f"✓ {instance_name} ({init_name}, {cross_name}, {mut_name}): "
                  f"Fitness={result.bestFitness:.2f}")
    
    def refresh_results(self):
        """Refresh results from results/ folder"""
        self.results_instances.delete(0, tk.END)
        results_dir = "results"
        
        if os.path.exists(results_dir):
            for folder in sorted(os.listdir(results_dir)):
                folder_path = os.path.join(results_dir, folder)
                if os.path.isdir(folder_path):
                    self.results_instances.insert(tk.END, folder)
    
    def plot_selected(self):
        """Plot selected result"""
        selection = self.results_instances.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an instance to plot")
            return
        
        instance_name = self.results_instances.get(selection[0])
        
        try:
            # Load runs and plot
            runs = plot_results.load_runs(instance_name)
            if not runs:
                messagebox.showwarning("Warning", f"No results found for {instance_name}")
                return
            
            # Create plotting window
            self.plot_results_window(instance_name, runs)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error loading results:\n{str(e)}")
    
    def plot_results_window(self, instance_name, runs):
        """Create a window with plotted results"""
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec
        
        fig = plt.figure(figsize=(14, 10))
        fig.suptitle(f"Results for {instance_name}", fontsize=16, fontweight='bold')
        
        gs = gridspec.GridSpec(2, 2, figure=fig)
        
        # Convergence plot
        ax1 = fig.add_subplot(gs[0, :])
        plot_results.plot_convergence(instance_name, runs, ax1)
        
        # Fitness distribution
        ax2 = fig.add_subplot(gs[1, 0])
        plot_results.plot_fitness_distribution(instance_name, runs, ax2)
        
        # Statistics
        ax3 = fig.add_subplot(gs[1, 1])
        self.plot_statistics(instance_name, runs, ax3)
        
        plt.tight_layout()
        plt.show()
    
    def plot_statistics(self, instance_name, runs, ax):
        """Plot statistics"""
        fitness_values = [r["best_fitness"] for r in runs if r.get("best_fitness") != float("inf")]
        
        if not fitness_values:
            ax.text(0.5, 0.5, "No feasible solutions", ha="center", va="center")
            return
        
        import numpy as np
        stats_text = f"""Statistics for {instance_name}

Runs: {len(runs)}
Feasible: {len(fitness_values)}

Best: {min(fitness_values):.2f}
Avg: {np.mean(fitness_values):.2f}
Worst: {max(fitness_values):.2f}
Std Dev: {np.std(fitness_values):.2f}
"""
        
        ax.text(0.1, 0.5, stats_text, fontsize=11, verticalalignment='center',
               family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        ax.axis('off')


if __name__ == "__main__":
    app = GAApp()
    app.mainloop()
