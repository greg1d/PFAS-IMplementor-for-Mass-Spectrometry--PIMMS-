import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import pandas as pd
import traceback

# Import the logic engine
try:
    from modules.transformation_checker import run_transformation_checker
except ImportError:
    run_transformation_checker = None

from GUI.widgets.scrollable_table_widget import ScrollableTable


class TransformationTab(ttk.Frame):
    def __init__(self, parent, config):
        super().__init__(parent)
        # RENAMED: Use app_config to avoid overwriting Tkinter's self.config() method
        self.app_config = config

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
        default_excl_path = getattr(self.app_config, "exclusion_library", None)

        self.paths = {
            "experimental": None,
            "suspect": None,
            "exclusion": default_excl_path,
        }

        self.mapping_vars = {
            "experimental": {"mz": None},
            "suspect": {"mz": None, "name": None},  # Added 'name' here
            "exclusion": {"mz": None},
        }

        self._create_widgets()

    def _create_widgets(self):
        # --- File Inputs & Column Mapping ---
        input_frame = ttk.Labelframe(self, text="Input Files & Column Mapping")
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        # 1. Experimental
        self._build_file_section(
            input_frame, "Experimental File", "experimental", default_mz="H"
        )

        # 2. Suspect Library (Now includes Name Column)
        self._build_file_section(
            input_frame, "Suspect Library", "suspect", default_mz="G", include_name=True
        )

        # 3. Exclusion Library
        excl_mz_def = "G"
        if hasattr(self.app_config, "exclusion_mapping"):
            excl_mz_def = self.app_config.exclusion_mapping.get("m/z", "G")

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
        self.ppm_spin = ttk.Spinbox(
            builder_frame, from_=0, to=100, increment=1, width=6
        )
        self.ppm_spin.set(15)
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

    def _build_file_section(
        self, parent, btn_text, key, default_mz="", include_name=False
    ):
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, padx=5, pady=2)

        # 1. Browse Button
        ttk.Button(
            row, text=btn_text, width=20, command=lambda: self._browse_file(key)
        ).pack(side=tk.LEFT)

        # 2. Filename Label
        current_path = self.paths.get(key)
        initial_label = (
            os.path.basename(current_path) if current_path else "No file loaded"
        )

        path_var = tk.StringVar(value=initial_label)
        setattr(self, f"{key}_path_var", path_var)

        lbl = ttk.Label(row, textvariable=path_var, foreground="black", width=40)
        lbl.pack(side=tk.LEFT, padx=(10, 5))

        # 3. Mapping Section
        ttk.Label(row, text="|").pack(side=tk.LEFT, padx=5)

        # m/z Input
        ttk.Label(row, text="m/z col:").pack(side=tk.LEFT)
        mz_var = tk.StringVar(value=default_mz)
        self.mapping_vars[key]["mz"] = mz_var
        ttk.Entry(row, textvariable=mz_var, width=5, justify="center").pack(
            side=tk.LEFT, padx=(2, 5)
        )

        # Optional Name Input
        if include_name:
            ttk.Label(row, text="Name col:").pack(side=tk.LEFT)
            # Default to "B" for name if not specified, usually standard
            name_var = tk.StringVar(value="B")
            self.mapping_vars[key]["name"] = name_var
            ttk.Entry(row, textvariable=name_var, width=5, justify="center").pack(
                side=tk.LEFT, padx=(2, 0)
            )

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
        if run_transformation_checker is None:
            messagebox.showerror(
                "Configuration Error",
                "Could not import 'run_transformation_checker' from modules.",
            )
            return

        if not self.paths["experimental"]:
            messagebox.showwarning("Error", "Experimental file required.")
            return

        # Extract Mappings (Now including Suspect Name)
        mappings = {
            "experimental": self.mapping_vars["experimental"]["mz"].get(),
            "suspect": self.mapping_vars["suspect"]["mz"].get(),
            "suspect_name": None,  # Default
            "exclusion": self.mapping_vars["exclusion"]["mz"].get(),
        }

        # Handle the new Name column if available
        if self.mapping_vars["suspect"].get("name"):
            mappings["suspect_name"] = self.mapping_vars["suspect"]["name"].get()

        if not mappings["experimental"]:
            messagebox.showwarning(
                "Missing Mapping", "Please enter m/z column for Experimental file."
            )
            return

        units = []
        for item in self.unit_tree.get_children():
            v = self.unit_tree.item(item)["values"]
            try:
                r_min, r_max = map(int, v[2].split(" to "))
                units.append(
                    {"name": v[0], "mass": float(v[1]), "min": r_min, "max": r_max}
                )
            except ValueError:
                continue

        if not units:
            messagebox.showwarning("Error", "Add at least one unit.")
            return

        try:
            ppm = float(self.ppm_spin.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid PPM value.")
            return

        params = {
            "ppm": ppm,
            "paths": self.paths,
            "mappings": mappings,
            "units": units,
        }

        print(f"[UI] Running Analysis with: {params}")

        try:
            self.configure(cursor="watch")
            self.update_idletasks()

            results_df = run_transformation_checker(params)

            self.configure(cursor="")

            if results_df is None:
                messagebox.showerror("Error", "No data returned.")
                return

            if "Error" in results_df.columns:
                messagebox.showerror("Analysis Error", results_df.iloc[0]["Error"])
                return

            if "Status" in results_df.columns:
                self.table.update_table(pd.DataFrame())
                messagebox.showinfo("Info", results_df.iloc[0]["Status"])
                return

            if not results_df.empty:
                self.table.update_table(results_df)
                messagebox.showinfo(
                    "Success", f"Found {len(results_df)} transformation pairs."
                )
            else:
                self.table.update_table(pd.DataFrame())
                messagebox.showinfo("No Results", "No matching pairs found.")

        except Exception as e:
            self.configure(cursor="")
            traceback.print_exc()
            messagebox.showerror("Critical Error", f"An error occurred:\n{e}")
