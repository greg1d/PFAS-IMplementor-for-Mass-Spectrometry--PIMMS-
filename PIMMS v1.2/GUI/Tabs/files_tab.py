# gui/tabs/files_tab.py

import tkinter as tk
from tkinter import ttk, filedialog


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
        for i, (text, key) in enumerate(file_options.items()):
            # The parent for the input widgets is the tab frame itself (self)
            self._create_file_input(self, text, key, i)

    def _create_file_input(self, parent, label_text, config_key, row):
        """Helper to create a label, entry, and browse button row."""
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
