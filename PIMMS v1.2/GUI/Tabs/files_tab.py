# gui/tabs/files_tab.py

import tkinter as tk
from tkinter import ttk, filedialog

# --- NEW: Import the Tooltip class ---
from ..widgets.tooltip import Tooltip


class FilesTab(ttk.Frame):
    def __init__(self, parent, config, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.config = config
        self.file_path_entries = {}
        self._create_widgets()

    def _create_widgets(self):
        """Creates all widgets for the file paths tab."""
        file_options = {
            "Raw Data Input": "raw_data_input_location",
            "Standards for Removal": "standards_file",
            "Level 2 Library": "level_2_library",
            "Level 5 Library": "level_5_library",
            "Output Report Path": "output_path",
        }

        # --- NEW: Define help texts for each entry ---
        help_texts = {
            "raw_data_input_location": "CSV file containing the feature list you wish to process. This file should include columns for row ID, m/z, RT, ID, CCS, and intensity. Column mappings selected on the 'Column Mappings' tab.",
            "standards_file": "Select a CSV file that lists the internal standards (e.g., by name or mass) that should be removed during processing.",
            "level_2_library": "Level 2 spectral library CSV file containing previously ran standards with known RT and CCS values for higher confidence annotations.",
            "level_5_library": "Level 5 spectral library CSV file containing m/z only for tentative annotations when RT and CCS data are not available.",
            "output_path": "Specify the location and name for the final output report file. This will be created or overwritten.",
        }

        # --- MODIFIED: Loop now also gets the help text ---
        for i, (text, key) in enumerate(file_options.items()):
            help_text = help_texts.get(key, "No details available.")
            # Pass the help_text to the creation function
            self._create_file_input(self, text, key, i, help_text)

    # --- MODIFIED: Method now accepts 'help_text' ---
    def _create_file_input(self, parent, label_text, config_key, row, help_text):
        """Helper to create a label, entry, browse button, and help icon row."""
        ttk.Label(parent, text=label_text + ":").grid(
            row=row, column=0, padx=5, pady=5, sticky="w"
        )
        entry = ttk.Entry(parent, width=70)

        default_val = getattr(self.config, config_key, "")
        if isinstance(default_val, list):
            default_val = default_val[0] if default_val else ""
        entry.insert(0, default_val)

        entry.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        self.file_path_entries[config_key] = entry

        browse_button = ttk.Button(
            parent,
            text="Browse...",
            command=lambda e=entry, k=config_key: self._browse_file(e, k),
        )
        browse_button.grid(row=row, column=2, padx=5, pady=5)

        # --- NEW: Add a help icon with a tooltip ---
        help_label = ttk.Label(parent, text=" (?) ", cursor="question_arrow")
        help_label.grid(row=row, column=3, padx=(0, 5), pady=5, sticky="w")
        Tooltip(help_label, text=help_text)  # Attach the tooltip to this label

        # Configure the column containing the entry to expand
        parent.grid_columnconfigure(1, weight=1)

    def _browse_file(self, entry, key):
        """Handles the file dialog logic for the browse buttons."""
        if "output" in key:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv", filetypes=[("CSV files", "*.csv")]
            )
        else:
            filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])

        if filename:
            entry.delete(0, tk.END)
            entry.insert(0, filename)

    def update_config(self, config_obj):
        """Updates the main config object with values from this tab."""
        for key, entry in self.file_path_entries.items():
            setattr(config_obj, key, entry.get())
