import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os  # Added for path handling
from GUI.widgets.scrollable_table_widget import ScrollableTable


class TransformationTab(ttk.Frame):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config

        # --- Modular Unit Definitions ---
        self.available_units = {
            "CF2": 49.9968,
            "CH2": 14.0156,
            "O (Ether)": 15.9949,
            "C2H4": 28.0313,
            "H2O (Loss)": -18.0105,
            "CO2": 43.9898,
        }

        # --- 1. Load Defaults from Config ---
        # We pre-fill the exclusion path if it exists in the config object
        default_excl_path = getattr(self.config, "exclusion_library", None)

        self.paths = {
            "experimental": None,
            "suspect": None,
            "exclusion": default_excl_path,
        }

        # We store the actual Tkinter StringVars here so we can read them later
        self.mapping_vars = {
            "experimental": {"mz": None},
            "suspect": {"mz": None},
            "exclusion": {"mz": None},
        }

        self._create_widgets()

    def _create_widgets(self):
        # --- File Inputs & Column Mapping ---
        input_frame = ttk.Labelframe(self, text="Input Files & Column Mapping")
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        # 1. Experimental (No default)
        self._build_file_section(
            input_frame, "Experimental File", "experimental", default_mz="H"
        )

        # 2. Suspect Library (No default in this snippet, but could be added similarly)
        self._build_file_section(
            input_frame, "Suspect Library", "suspect", default_mz="G"
        )

        # 3. Exclusion Library (Loads default m/z from config)
        # Fetch default mapping from config, fallback to "G" if missing
        excl_mz_def = "G"
        if hasattr(self.config, "exclusion_mapping"):
            excl_mz_def = self.config.exclusion_mapping.get("m/z", "G")

        self._build_file_section(
            input_frame, "Exclusion Library", "exclusion", default_mz=excl_mz_def
        )

        # --- Search Configuration ---
        config_frame = ttk.Labelframe(self, text="Transformation Logic")
        config_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)

        # Left Side: Unit Builder
        builder_frame = ttk.Frame(config_frame)
        builder_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Row 0: PPM
        ttk.Label(builder_frame, text="Global Mass Error (ppm):").grid(
            row=0, column=0, sticky="w", pady=2
        )
        self.ppm_spin = ttk.Spinbox(builder_frame, from_=0.1, to=50, width=6)
        self.ppm_spin.set(5.0)
        self.ppm_spin.grid(row=0, column=1, sticky="w", pady=2)

        # Row 1: Unit Dropdown
        ttk.Label(builder_frame, text="Select Unit:").grid(
            row=1, column=0, sticky="w", pady=2
        )
        self.unit_combo = ttk.Combobox(
            builder_frame,
            values=list(self.available_units.keys()),
            state="readonly",
            width=15,
        )
        self.unit_combo.current(0)
        self.unit_combo.grid(row=1, column=1, sticky="w", pady=2)

        # Row 2: Range
        ttk.Label(builder_frame, text="Range (Min / Max):").grid(
            row=2, column=0, sticky="w", pady=2
        )

        range_frame = ttk.Frame(builder_frame)
        range_frame.grid(row=2, column=1, sticky="w", pady=2)

        self.min_spin = ttk.Spinbox(range_frame, from_=-20, to=20, width=4)
        self.min_spin.set(-1)
        self.min_spin.pack(side=tk.LEFT)

        ttk.Label(range_frame, text=" to ").pack(side=tk.LEFT)

        self.max_spin = ttk.Spinbox(range_frame, from_=-20, to=20, width=4)
        self.max_spin.set(3)
        self.max_spin.pack(side=tk.LEFT)

        # Row 3: Add Button
        self.add_btn = ttk.Button(
            builder_frame, text="Add Unit >>", command=self._add_unit_to_list
        )
        self.add_btn.grid(row=3, column=0, columnspan=2, pady=5, sticky="ew")

        # Right Side: Active Queue
        list_frame = ttk.Frame(config_frame)
        list_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)

        cols = ("unit", "mass", "range")
        self.unit_tree = ttk.Treeview(
            list_frame, columns=cols, show="headings", height=5
        )
        self.unit_tree.heading("unit", text="Unit")
        self.unit_tree.heading("mass", text="Mass")
        self.unit_tree.heading("range", text="Range")

        self.unit_tree.column("unit", width=80)
        self.unit_tree.column("mass", width=70)
        self.unit_tree.column("range", width=70)

        self.unit_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.unit_tree.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.unit_tree.configure(yscrollcommand=scrollbar.set)

        ttk.Button(list_frame, text="Remove Selected", command=self._remove_unit).pack(
            anchor="e", pady=2
        )

        # --- Run Button ---
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=10, pady=5)
        self.run_btn = ttk.Button(
            action_frame, text="RUN ANALYSIS", command=self._on_run_clicked
        )
        self.run_btn.pack(side=tk.RIGHT)

        # --- Results Table ---
        table_frame = ttk.Labelframe(self, text="Results")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.table = ScrollableTable(table_frame)
        self.table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _build_file_section(self, parent, btn_text, key, default_mz=""):
        """
        Creates a single-line file loader with inline mapping.
        """
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, padx=5, pady=2)

        # 1. Browse Button
        ttk.Button(
            row, text=btn_text, width=20, command=lambda: self._browse_file(key)
        ).pack(side=tk.LEFT)

        # 2. Filename Label
        # Check if we already have a path loaded from Config
        current_path = self.paths.get(key)
        if current_path:
            # If path exists, show filename
            initial_label = os.path.basename(current_path)
        else:
            initial_label = "No file loaded"

        path_var = tk.StringVar(value=initial_label)
        setattr(self, f"{key}_path_var", path_var)

        lbl = ttk.Label(row, textvariable=path_var, foreground="black", width=40)
        lbl.pack(side=tk.LEFT, padx=(10, 5))

        # 3. Mapping Section
        ttk.Label(row, text="|").pack(side=tk.LEFT, padx=5)
        ttk.Label(row, text="m/z col:").pack(side=tk.LEFT)

        mz_var = tk.StringVar(value=default_mz)
        self.mapping_vars[key]["mz"] = mz_var

        entry = ttk.Entry(row, textvariable=mz_var, width=5, justify="center")
        entry.pack(side=tk.LEFT, padx=(2, 0))

    def _browse_file(self, key):
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if path:
            self.paths[key] = path
            filename = os.path.basename(path)
            getattr(self, f"{key}_path_var").set(filename)

    def _add_unit_to_list(self):
        unit = self.unit_combo.get()
        mass = self.available_units[unit]
        try:
            mn = int(self.min_spin.get())
            mx = int(self.max_spin.get())
        except ValueError:
            return

        for item in self.unit_tree.get_children():
            if self.unit_tree.item(item)["values"][0] == unit:
                self.unit_tree.delete(item)

        self.unit_tree.insert("", "end", values=(unit, mass, f"{mn} to {mx}"))

    def _remove_unit(self):
        for item in self.unit_tree.selection():
            self.unit_tree.delete(item)

    def _on_run_clicked(self):
        # 1. Validation
        if not self.paths["experimental"]:
            messagebox.showwarning("Error", "Experimental file required.")
            return

        # 2. Extract Mappings
        mappings = {
            "experimental": self.mapping_vars["experimental"]["mz"].get(),
            "suspect": self.mapping_vars["suspect"]["mz"].get(),
            "exclusion": self.mapping_vars["exclusion"]["mz"].get(),
        }

        # 3. Build Units
        units = []
        for item in self.unit_tree.get_children():
            v = self.unit_tree.item(item)["values"]
            r_min, r_max = map(int, v[2].split(" to "))
            units.append(
                {"name": v[0], "mass": float(v[1]), "min": r_min, "max": r_max}
            )

        if not units:
            messagebox.showwarning("Error", "Add at least one unit.")
            return

        # 4. Construct Params
        params = {
            "ppm": float(self.ppm_spin.get()),
            "paths": self.paths,
            "mappings": mappings,
            "units": units,
        }

        print(f"Running with: {params}")
