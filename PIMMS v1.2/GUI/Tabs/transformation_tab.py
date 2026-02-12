import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from GUI.widgets.scrollable_table_widget import ScrollableTable


class TransformationTab(ttk.Frame):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config

        # --- Modular Unit Definitions ---
        # You can add to this dictionary easily in the future
        self.available_units = {
            "CF2": 49.9968,
            "CH2": 14.0156,
            "O (Ether)": 15.9949,
            "C2H4": 28.0313,
            "H2O (Loss)": -18.0105,  # Example of a negative mass unit
            "CO2": 43.9898,
        }

        self.paths = {"experimental": None, "suspect": None, "exclusion": None}
        self.column_maps = {}

        self._create_widgets()

    def _create_widgets(self):
        # --- 1. File Management (Top) ---
        file_frame = ttk.Labelframe(self, text="1. Data Loading")
        file_frame.pack(fill=tk.X, padx=10, pady=5)

        for key in ["experimental", "suspect", "exclusion"]:
            self._build_file_row(file_frame, f"{key.capitalize()} Library:", key)

        # --- 2. Search Configuration (Middle - Split into 2 sides) ---
        config_frame = ttk.Labelframe(self, text="2. Transformation Logic")
        config_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)

        # Left Side: Unit Builder
        builder_frame = ttk.Frame(config_frame)
        builder_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)

        ttk.Label(builder_frame, text="Global Mass Error (ppm):").grid(
            row=0, column=0, sticky="w"
        )
        self.ppm_spin = ttk.Spinbox(builder_frame, from_=0.1, to=50, width=8)
        self.ppm_spin.set(5.0)
        self.ppm_spin.grid(row=0, column=1, sticky="w", pady=5)

        ttk.Separator(builder_frame, orient="horizontal").grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=10
        )

        # Unit Selection
        ttk.Label(builder_frame, text="Select Unit:").grid(row=2, column=0, sticky="w")
        self.unit_combo = ttk.Combobox(
            builder_frame, values=list(self.available_units.keys()), state="readonly"
        )
        self.unit_combo.current(0)
        self.unit_combo.grid(row=2, column=1, sticky="ew", pady=2)

        # Range Selection (Asymmetric)
        ttk.Label(builder_frame, text="Min Multiple (e.g. -1):").grid(
            row=3, column=0, sticky="w"
        )
        self.min_spin = ttk.Spinbox(builder_frame, from_=-20, to=20, width=8)
        self.min_spin.set(-1)
        self.min_spin.grid(row=3, column=1, sticky="w", pady=2)

        ttk.Label(builder_frame, text="Max Multiple (e.g. +3):").grid(
            row=4, column=0, sticky="w"
        )
        self.max_spin = ttk.Spinbox(builder_frame, from_=-20, to=20, width=8)
        self.max_spin.set(3)
        self.max_spin.grid(row=4, column=1, sticky="w", pady=2)

        # Add Button
        self.add_btn = ttk.Button(
            builder_frame, text="Add Unit to Search >>", command=self._add_unit_to_list
        )
        self.add_btn.grid(row=5, column=0, columnspan=2, pady=10, sticky="ew")

        # Right Side: Active Search List
        list_frame = ttk.Frame(config_frame)
        list_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)

        ttk.Label(list_frame, text="Active Transformation Queue:").pack(anchor="w")

        # Treeview to show selected units
        cols = ("unit", "mass", "min", "max")
        self.unit_tree = ttk.Treeview(
            list_frame, columns=cols, show="headings", height=6
        )

        self.unit_tree.heading("unit", text="Unit Name")
        self.unit_tree.heading("mass", text="Mass")
        self.unit_tree.heading("min", text="Min")
        self.unit_tree.heading("max", text="Max")

        self.unit_tree.column("unit", width=100)
        self.unit_tree.column("mass", width=80)
        self.unit_tree.column("min", width=50)
        self.unit_tree.column("max", width=50)

        self.unit_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for the list
        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.unit_tree.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.unit_tree.configure(yscrollcommand=scrollbar.set)

        # Remove Button
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        ttk.Button(list_frame, text="Remove Selected", command=self._remove_unit).pack(
            anchor="e", pady=5
        )

        # --- 3. Action Area ---
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=10, pady=5)

        self.run_btn = ttk.Button(
            action_frame, text="RUN ANALYSIS PIPELINE", command=self._on_run_clicked
        )
        self.run_btn.pack(side=tk.RIGHT, padx=5)

        # --- 4. Results ---
        self.table_frame = ttk.Labelframe(self, text="3. Results")
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.table = ScrollableTable(self.table_frame)
        self.table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # --- Helper Methods ---

    def _build_file_row(self, master, label_text, key):
        """Creates a consistent file loading row."""
        row = ttk.Frame(master)
        row.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(row, text=label_text, width=20).pack(side=tk.LEFT)

        path_var = tk.StringVar(value="None")
        setattr(self, f"{key}_path_var", path_var)

        lbl = ttk.Label(row, textvariable=path_var, foreground="blue", width=40)
        lbl.pack(side=tk.LEFT, padx=5)

        ttk.Button(row, text="Browse...", command=lambda: self._browse_file(key)).pack(
            side=tk.RIGHT
        )
        ttk.Button(
            row, text="Map Columns", command=lambda: self._map_columns(key)
        ).pack(side=tk.RIGHT, padx=5)

    def _browse_file(self, key):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if path:
            self.paths[key] = path
            getattr(self, f"{key}_path_var").set(path.split("/")[-1])

    def _map_columns(self, key):
        if not self.paths[key]:
            messagebox.showwarning("Warning", "Please load a file first.")
            return
        # Placeholder for your modular mapping dialog
        messagebox.showinfo("Mapping", f"Open Column Mapper for {key}")

    # --- Logic for the Unit Manager ---

    def _add_unit_to_list(self):
        """Takes settings from the builder and adds to the Treeview."""
        unit_name = self.unit_combo.get()
        mass_val = self.available_units[unit_name]

        try:
            min_val = int(self.min_spin.get())
            max_val = int(self.max_spin.get())
        except ValueError:
            messagebox.showerror("Error", "Range values must be integers.")
            return

        if min_val > max_val:
            messagebox.showerror("Error", "Min cannot be greater than Max.")
            return

        # Check if already exists (optional: prevent duplicates or allow update)
        for item in self.unit_tree.get_children():
            if self.unit_tree.item(item)["values"][0] == unit_name:
                self.unit_tree.delete(item)  # Remove old entry to update it

        # Insert into Treeview
        self.unit_tree.insert("", "end", values=(unit_name, mass_val, min_val, max_val))

    def _remove_unit(self):
        selected_item = self.unit_tree.selection()
        if selected_item:
            self.unit_tree.delete(selected_item)

    def _on_run_clicked(self):
        # 1. Gather Global Settings
        ppm = float(self.ppm_spin.get())

        # 2. Gather Unit Settings from Treeview
        search_units = []
        for item in self.unit_tree.get_children():
            vals = self.unit_tree.item(item)["values"]
            # vals = (unit_name, mass, min, max)
            search_units.append(
                {
                    "name": vals[0],
                    "mass": float(vals[1]),
                    "range_min": int(vals[2]),
                    "range_max": int(vals[3]),
                }
            )

        if not search_units:
            messagebox.showwarning(
                "Wait", "Please add at least one unit to the search queue."
            )
            return

        params = {"ppm": ppm, "search_units": search_units, "paths": self.paths}

        print(f"Running Analysis with: {params}")
        # self._execute_backend(params)
