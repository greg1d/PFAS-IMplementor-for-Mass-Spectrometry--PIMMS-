# gui/tabs/mapping_tab.py

from tkinter import ttk


class MappingTab(ttk.Frame):
    def __init__(self, parent, config, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.config = config
        self.mapping_entries = {}
        self._create_widgets()

    def _create_widgets(self):
        """Creates all widgets for the column mappings tab."""
        meta_frame = ttk.LabelFrame(
            self, text="Metadata Column Letters (Raw Data)", padding=(10, 5)
        )
        meta_frame.pack(fill="x", padx=10, pady=5)
        for i, (key, val) in enumerate(self.config.metadata_mapping.items()):
            self._create_mapping_input(
                meta_frame, key, f"meta_{key}", val, i // 3, i % 3
            )

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
        )
        self._create_mapping_input(
            sample_frame,
            "Control End",
            "control_end_col",
            self.config.control_end_col,
            0,
            1,
        )
        self._create_mapping_input(
            sample_frame,
            "Experimental Start",
            "experimental_start_col",
            self.config.experimental_start_col,
            1,
            0,
        )
        self._create_mapping_input(
            sample_frame,
            "Experimental End",
            "experimental_end_col",
            self.config.experimental_end_col,
            1,
            1,
        )

        l2_frame = ttk.LabelFrame(
            self, text="Level 2 Library Column Letters", padding=(10, 5)
        )
        l2_frame.pack(fill="x", padx=10, pady=5)
        for i, (key, val) in enumerate(self.config.level_2_library_mapping.items()):
            self._create_mapping_input(l2_frame, key, f"l2_{key}", val, i // 3, i % 3)

        l5_frame = ttk.LabelFrame(
            self, text="Level 5 Library Column Letters", padding=(10, 5)
        )
        l5_frame.pack(fill="x", padx=10, pady=5)
        for i, (key, val) in enumerate(self.config.level_5_library_mapping.items()):
            self._create_mapping_input(l5_frame, key, f"l5_{key}", val, i // 2, i % 2)

    def _create_mapping_input(self, parent, text, key, default, row, col):
        """Helper to create a label and entry for a mapping."""
        ttk.Label(parent, text=text + ":").grid(
            row=row, column=col * 2, padx=5, pady=2, sticky="w"
        )
        entry = ttk.Entry(parent, width=8)
        entry.insert(0, default)
        entry.grid(row=row, column=col * 2 + 1, padx=5, pady=2, sticky="w")
        self.mapping_entries[key] = entry

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
