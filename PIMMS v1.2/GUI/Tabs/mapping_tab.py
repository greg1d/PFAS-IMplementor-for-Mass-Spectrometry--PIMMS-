# gui/tabs/mapping_tab.py

from tkinter import ttk

# --- NEW: Import the Tooltip class ---
from ..widgets.tooltip import Tooltip


class MappingTab(ttk.Frame):
    def __init__(self, parent, config, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.config = config
        self.mapping_entries = {}
        self._create_widgets()

    def _create_widgets(self):
        """Creates all widgets for the column mappings tab."""

        # --- NEW: Define all help texts in a structured dictionary ---
        help_texts = {
            "metadata": {
                "ID": "The column letter in the Raw Data file for the unique identifier (ID) for each feature.",
                "DT": "The column letter in the Raw Data file for the drift time (DT).",
                "CCS": "The column letter in the Raw Data file for the Collisional Cross-Section (CCS).",
                "RT": "The column letter in the Raw Data file for the Retention Time (RT).",
                "m/z": "The column letter for the m/z value.",
            },
            "sample_ranges": {
                "control_start_col": "The starting column letter for your control/blank samples (e.g., 'H').",
                "control_end_col": "The ending column letter for your control/blank samples (e.g., 'K').",
                "experimental_start_col": "The starting column letter for your experimental samples.",
                "experimental_end_col": "The ending column letter for your experimental samples.",
            },
            "level_2": {
                "Name": "The column letter in the Level 2 Library for the compound's name.",
                "Adduct": "The column letter in the Level 2 Library specifying the adduct type (e.g., M+H, M+Na, M-H, M-).",
                "m/z": "The column letter in the Level 2 Library for the precursor mass-to-charge ratio (m/z).",
                "CCS": "The column letter in the Level 2 Library for the Collisional Cross-Section (CCS) value.",
                "RT": "The column letter in the Level 2 Library for the Retention Time (RT).",
            },
            "level_5": {
                "Name": "The column letter in the Level 5 Library for the compound's name.",
                "m/z": "The column letter in the Level 5 Library for the precursor mass-to-charge ratio (m/z).",
            },
            "standards": {
                "m/z": "The column letter in your Standards Library file that contains the mass-to-charge (m/z) values.",
                "CCS": "The column letter in your Standards Library file that contains the Collisional Cross-Section (CCS) values.",
            },
        }

        # --- Metadata Frame ---
        meta_frame = ttk.LabelFrame(
            self, text="Metadata Column Letters (Raw Data)", padding=(10, 5)
        )
        meta_frame.pack(fill="x", padx=10, pady=5)
        for i, (key, val) in enumerate(self.config.metadata_mapping.items()):
            help_text = help_texts["metadata"].get(key, "No details.")
            self._create_mapping_input(
                meta_frame, key, f"meta_{key}", val, i // 3, i % 3, help_text
            )

        # --- Sample Ranges Frame ---
        sample_frame = ttk.LabelFrame(
            self, text="Sample Column Ranges (Raw Data)", padding=(10, 5)
        )
        sample_frame.pack(fill="x", padx=10, pady=5)
        self._create_mapping_input(
            sample_frame,
            "Control Start",
            "control_start_col",
            self.config.control_start_col,
            0,
            0,
            help_texts["sample_ranges"]["control_start_col"],
        )
        self._create_mapping_input(
            sample_frame,
            "Control End",
            "control_end_col",
            self.config.control_end_col,
            0,
            1,
            help_texts["sample_ranges"]["control_end_col"],
        )
        self._create_mapping_input(
            sample_frame,
            "Experimental Start",
            "experimental_start_col",
            self.config.experimental_start_col,
            1,
            0,
            help_texts["sample_ranges"]["experimental_start_col"],
        )
        self._create_mapping_input(
            sample_frame,
            "Experimental End",
            "experimental_end_col",
            self.config.experimental_end_col,
            1,
            1,
            help_texts["sample_ranges"]["experimental_end_col"],
        )

        # --- Level 2 Library Frame ---
        l2_frame = ttk.LabelFrame(
            self, text="Level 1 Library Column Letters", padding=(10, 5)
        )
        l2_frame.pack(fill="x", padx=10, pady=5)
        for i, (key, val) in enumerate(self.config.level_2_library_mapping.items()):
            help_text = help_texts["level_2"].get(key, "No details.")
            self._create_mapping_input(
                l2_frame, key, f"l2_{key}", val, i // 3, i % 3, help_text
            )

        # --- Level 5 Library Frame ---
        l5_frame = ttk.LabelFrame(
            self, text="Level 5 Library Column Letters", padding=(10, 5)
        )
        l5_frame.pack(fill="x", padx=10, pady=5)
        for i, (key, val) in enumerate(self.config.level_5_library_mapping.items()):
            help_text = help_texts["level_5"].get(key, "No details.")
            self._create_mapping_input(
                l5_frame, key, f"l5_{key}", val, i // 2, i % 2, help_text
            )

        standards_frame = ttk.LabelFrame(
            self, text="Standards Library Column Letters", padding=(10, 5)
        )
        standards_frame.pack(fill="x", padx=10, pady=5)

        # Add m/z and CCS inputs for the standards library
        self._create_mapping_input(
            standards_frame,
            "m/z",
            "standards_m/z",
            self.config.standards_library_mapping.get("m/z", ""),
            0,
            0,
            help_texts["standards"]["m/z"],
        )
        self._create_mapping_input(
            standards_frame,
            "CCS",
            "standards_CCS",
            self.config.standards_library_mapping.get("CCS", ""),
            0,
            1,
            help_texts["standards"]["CCS"],
        )

    # --- MODIFIED: Method now accepts 'help_text' ---
    def _create_mapping_input(self, parent, text, key, default, row, col, help_text=""):
        """Helper to create a label, entry, and help icon for a mapping."""
        # The Label and Entry are placed in columns relative to 'col'
        ttk.Label(parent, text=text + ":").grid(
            row=row, column=col * 3, padx=5, pady=2, sticky="w"
        )
        entry = ttk.Entry(parent, width=8)
        entry.insert(0, default)
        entry.grid(row=row, column=col * 3 + 1, padx=5, pady=2, sticky="w")
        self.mapping_entries[key] = entry

        # --- NEW: Add the help icon and attach the tooltip ---
        if help_text:  # Only add an icon if there is help text
            help_label = ttk.Label(parent, text=" (?) ", cursor="question_arrow")
            help_label.grid(
                row=row, column=col * 3 + 2, padx=(0, 10), pady=2, sticky="w"
            )
            Tooltip(help_label, text=help_text)

    def update_config(self, config_obj):
        """Updates the main config object with values from this tab."""
        config_obj.control_start_col = self.mapping_entries["control_start_col"].get()
        config_obj.control_end_col = self.mapping_entries["control_end_col"].get()
        config_obj.experimental_start_col = self.mapping_entries[
            "experimental_start_col"
        ].get()
        config_obj.experimental_end_col = self.mapping_entries[
            "experimental_end_col"
        ].get()

        config_obj.metadata_mapping = {
            k: self.mapping_entries[f"meta_{k}"].get()
            for k in config_obj.metadata_mapping
        }
        config_obj.level_2_library_mapping = {
            k: self.mapping_entries[f"l2_{k}"].get()
            for k in config_obj.level_2_library_mapping
        }
        config_obj.level_5_library_mapping = {
            k: self.mapping_entries[f"l5_{k}"].get()
            for k in config_obj.level_5_library_mapping
        }
        config_obj.standards_library_mapping = {
            "m/z": self.mapping_entries["standards_m/z"].get(),
            "CCS": self.mapping_entries["standards_CCS"].get(),
        }
