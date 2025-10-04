# pimms_project/gui/app.py

import threading
import tkinter as tk
from tkinter import messagebox, ttk

# --- Project Imports ---
from PIMMS_Configuration import Config
from PIMMS_Workflow_Logic import run_pimms_workflow

# --- GUI Component Imports ---
from .Tabs.files_tab import FilesTab
from .Tabs.mapping_tab import MappingTab
from .Tabs.params_tab import ParamsTab
from .Tabs.run_tab import RunTab
from .Tabs.visualizations_tab import VisualizationsTab


class PimmsGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PIMMS v1.2")
        self.geometry("1200x800")

        # The Config object acts as the central data model
        self.config = Config()

        # The notebook is the container for all the tabs
        notebook = ttk.Notebook(self)
        notebook.pack(pady=10, padx=10, expand=True, fill="both")

        # --- Create instances of each tab ---
        # Each tab class is responsible for creating its own widgets.
        self.files_tab = FilesTab(notebook, self.config)
        self.mapping_tab = MappingTab(notebook, self.config)
        self.params_tab = ParamsTab(notebook, self.config)

        # The RunTab is given a "callback" function to execute when its button is pressed.
        self.run_tab = RunTab(notebook, self.run_workflow_thread)
        self.visualizations_tab = VisualizationsTab(notebook, self.config)

        # --- Add tabs to the notebook ---
        # The main app adds the fully-formed tabs to the notebook.
        notebook.add(self.files_tab, text="File Paths")
        notebook.add(self.mapping_tab, text="Column Mappings")
        notebook.add(self.params_tab, text="Parameters")
        notebook.add(self.run_tab, text="Run Workflow")
        notebook.add(
            self.visualizations_tab, text="CCS vs m/z Analysis"
        )  # <-- ADD THE NEW TAB

    def run_workflow_thread(self):
        """Orchestrates data collection from tabs and runs the workflow."""
        try:
            # Tell each tab to update the shared config object with its current values.
            self.files_tab.update_config(self.config)
            self.mapping_tab.update_config(self.config)
            self.params_tab.update_config(self.config)

            # The workflow logic now has the fully updated config.
            print("Starting PIMMS workflow...")
            thread = threading.Thread(target=run_pimms_workflow, args=(self.config,))
            thread.daemon = True
            thread.start()

        except ValueError as e:
            messagebox.showerror(
                "Invalid Input",
                f"Please check your parameters. A numeric value is required.\n\nError: {e}",
            )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"An unexpected error occurred: {e}",
            )
