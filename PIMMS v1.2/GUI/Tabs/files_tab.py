# gui/tabs/files_tab.py

import os
import tkinter as tk
from tkinter import filedialog, ttk

from ..utils import format_display_path

# Import the Tooltip class
from ..widgets.tooltip import Tooltip


class FilesTab(ttk.Frame):
    def __init__(self, parent, config, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.config = config
        self.file_path_entries = {}

        # --- NEW: Initialize the ignore standards variable ---
        self.ignore_standards_var = tk.BooleanVar(
            value=getattr(self.config, "ignore_standards", False)
        )

        self._create_widgets()

    def _create_widgets(self):
        """Creates all widgets for the file paths tab."""
        file_options = {
            "Raw Data Input": "raw_data_input_location",
            "Standards for Removal": "standards_file",
            "Level 1 Library": "level_2_library",
            "Level 5 Library": "level_5_library",
            "Output Report Path": "output_path",
        }

        help_texts = {
            "raw_data_input_location": "CSV file containing the feature list you wish to process. This file should include columns for row ID, m/z, RT, ID, CCS, and intensity. Column mappings selected on the 'Column Mappings' tab.",
            "standards_file": "Select a CSV file that lists the internal standards (e.g., by name or mass) that should be removed during processing.",
            "level_2_library": "Level 2 spectral library CSV file containing previously ran standards with known RT and CCS values for higher confidence annotations.",
            "level_5_library": "Level 5 spectral library CSV file containing m/z only for tentative annotations when RT and CCS data are not available.",
            "output_path": "Specify the location and name for the final output report file. This will be created or overwritten.",
        }

        for i, (text, key) in enumerate(file_options.items()):
            help_text = help_texts.get(key, "No details available.")
            self._create_file_input(self, text, key, i, help_text)

    def _create_file_input(self, parent, label_text, config_key, row, help_text):
        """Helper to create a label, entry, browse button, and help icon row."""
        ttk.Label(parent, text=label_text + ":").grid(
            row=row, column=0, padx=5, pady=5, sticky="w"
        )
        entry = ttk.Entry(parent, width=70)

        # Get the full path from the config, but format it for display.
        default_val = getattr(self.config, config_key, "")
        if isinstance(default_val, list):
            default_val = default_val[0] if default_val else ""

        display_val = format_display_path(default_val)
        entry.insert(0, display_val)

        entry.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        self.file_path_entries[config_key] = entry

        browse_button = ttk.Button(
            parent,
            text="Browse...",
            command=lambda e=entry, k=config_key: self._browse_file(e, k),
        )
        browse_button.grid(row=row, column=2, padx=5, pady=5)

        help_label = ttk.Label(parent, text=" (?) ", cursor="question_arrow")
        help_label.grid(row=row, column=3, padx=(0, 5), pady=5, sticky="w")
        Tooltip(help_label, text=help_text)

        # --- NEW: Add Checkbox specifically for Standards File ---
        if config_key == "standards_file":
            chk = ttk.Checkbutton(
                parent,
                text="Process without standards removal",
                variable=self.ignore_standards_var,
                command=self._toggle_standards_entry,
            )
            # Place in column 4 (next to help icon)
            chk.grid(row=row, column=4, padx=5, pady=5, sticky="w")

            # Apply initial state (grey out if checked by default)
            self._toggle_standards_entry()

        parent.grid_columnconfigure(1, weight=1)

    def _toggle_standards_entry(self):
        """Enables or disables the standards file entry based on the checkbox."""
        entry = self.file_path_entries.get("standards_file")
        if entry:
            if self.ignore_standards_var.get():
                entry.config(state="disabled")
            else:
                entry.config(state="normal")

    def _browse_file(self, entry, key):
        """Handles the file dialog logic for the browse buttons."""
        # Default browse location: user's Documents folder
        user_documents = os.path.join(os.path.expanduser("~"), "Documents", "PIMMS")

        if "output" in key:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialdir=user_documents,
                title="Select output file location",
            )
        else:
            filename = filedialog.askopenfilename(
                filetypes=[("CSV files", "*.csv")],
                initialdir=user_documents,
                title="Select input file",
            )

        if filename:
            entry.delete(0, tk.END)
            entry.insert(0, filename)

    def update_config(self, config_obj):
        """Updates the main config object with values from this tab."""
        for key, entry in self.file_path_entries.items():
            path_from_entry = entry.get()
            # If the path in the widget starts with "...", it's our formatted
            # display path. This means the user hasn't changed it, so we should
            # NOT update the config object, as it already holds the correct full path.
            # We only update the config if the path is a new, user-selected one.
            if not path_from_entry.startswith("..."):
                setattr(config_obj, key, path_from_entry)

        # --- NEW: Update the ignore_standards flag ---
        config_obj.ignore_standards = self.ignore_standards_var.get()
