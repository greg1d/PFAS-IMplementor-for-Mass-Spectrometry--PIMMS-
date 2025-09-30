import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

# --- Local Imports ---
# Make sure your configuration file is named PIMMS_Configuration.py
from PIMMS_Configuration import Config
from PIMMS_Workflow_Logic import run_pimms_workflow


class PimmsGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PIMMS Workflow Configuration")
        self.geometry("850x700")

        self.config = Config()
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        self._create_files_tab()
        self._create_mapping_tab()
        self._create_params_tab()
        self._create_run_tab()

    def _create_files_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="File Paths")
        self.file_path_entries = {}
        file_options = {
            "Raw Data Input": "raw_data_input_location",
            "Standards for Removal": "standards_file",
            "Level 2 Library": "level_2_library",
            "Level 5 Library": "level_5_library",
            "Output Report Path": "output_path",
        }
        for i, (text, key) in enumerate(file_options.items()):
            self._create_file_input(tab, text, key, i)

    def _create_mapping_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Column Mappings")
        self.mapping_entries = {}

        def _create_mapping_input(parent, text, key, default, row, col):
            ttk.Label(parent, text=text + ":").grid(
                row=row, column=col * 2, padx=5, pady=2, sticky="w"
            )
            entry = ttk.Entry(parent, width=8)
            entry.insert(0, default)
            entry.grid(row=row, column=col * 2 + 1, padx=5, pady=2, sticky="w")
            self.mapping_entries[key] = entry

        meta_frame = ttk.LabelFrame(
            tab, text="Metadata Column Letters (Raw Data)", padding=(10, 5)
        )
        meta_frame.pack(fill="x", padx=10, pady=5)
        for i, (key, val) in enumerate(self.config.metadata_mapping.items()):
            _create_mapping_input(meta_frame, key, f"meta_{key}", val, i // 3, i % 3)

        sample_frame = ttk.LabelFrame(
            tab, text="Sample Column Ranges (Raw Data)", padding=(10, 5)
        )
        sample_frame.pack(fill="x", padx=10, pady=5)
        _create_mapping_input(
            sample_frame,
            "Control Start",
            "control_start_col",
            self.config.control_start_col,
            0,
            0,
        )
        _create_mapping_input(
            sample_frame,
            "Control End",
            "control_end_col",
            self.config.control_end_col,
            0,
            1,
        )
        _create_mapping_input(
            sample_frame,
            "Experimental Start",
            "experimental_start_col",
            self.config.experimental_start_col,
            1,
            0,
        )
        _create_mapping_input(
            sample_frame,
            "Experimental End",
            "experimental_end_col",
            self.config.experimental_end_col,
            1,
            1,
        )

        l2_frame = ttk.LabelFrame(
            tab, text="Level 2 Library Column Letters", padding=(10, 5)
        )
        l2_frame.pack(fill="x", padx=10, pady=5)
        for i, (key, val) in enumerate(self.config.level_2_library_mapping.items()):
            _create_mapping_input(l2_frame, key, f"l2_{key}", val, i // 3, i % 3)

        l5_frame = ttk.LabelFrame(
            tab, text="Level 5 Library Column Letters", padding=(10, 5)
        )
        l5_frame.pack(fill="x", padx=10, pady=5)
        for i, (key, val) in enumerate(self.config.level_5_library_mapping.items()):
            _create_mapping_input(l5_frame, key, f"l5_{key}", val, i // 2, i % 2)

    def _create_params_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Parameters")
        self.param_entries = {}

        params_frame = ttk.LabelFrame(
            tab, text="Tolerances and Filters", padding=(10, 5)
        )
        params_frame.pack(fill="x", padx=10, pady=5)

        params = {
            "Mass Error (ppm)": "mass_error_ppm",
            "CCS Tolerance (%)": "ccs_tolerance",
            "RT Tolerance": "rt_tolerance",
            "Min Intensity": "min_intensity",
            "Min RT": "rt_min",
            "Max RT": "rt_max",
        }
        for i, (text, key) in enumerate(params.items()):
            ttk.Label(params_frame, text=text + ":").grid(
                row=i, column=0, padx=5, pady=2, sticky="w"
            )
            entry = ttk.Entry(params_frame)
            entry.insert(0, str(getattr(self.config, key)))
            entry.grid(row=i, column=1, padx=5, pady=2, sticky="ew")
            self.param_entries[key] = entry

        mdf_frame = ttk.LabelFrame(tab, text="Mass Defect Filter", padding=(10, 5))
        mdf_frame.pack(fill="x", padx=10, pady=5, anchor="w")

        ttk.Label(mdf_frame, text="Lower Bound:").grid(
            row=0, column=0, padx=5, pady=2, sticky="w"
        )
        mdf_lower_entry = ttk.Entry(mdf_frame)
        mdf_lower_entry.insert(
            0, str(getattr(self.config, "mass_defect_lower_bound", -0.11))
        )
        mdf_lower_entry.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        self.param_entries["mass_defect_lower_bound"] = mdf_lower_entry

        ttk.Label(mdf_frame, text="Upper Bound:").grid(
            row=1, column=0, padx=5, pady=2, sticky="w"
        )
        mdf_upper_entry = ttk.Entry(mdf_frame)
        mdf_upper_entry.insert(
            0, str(getattr(self.config, "mass_defect_upper_bound", 0.12))
        )
        mdf_upper_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        self.param_entries["mass_defect_upper_bound"] = mdf_upper_entry

        bs_frame = ttk.LabelFrame(tab, text="Blank Subtraction", padding=(10, 5))
        bs_frame.pack(fill="x", padx=10, pady=5, anchor="w")

        ttk.Label(bs_frame, text="Method:").grid(
            row=0, column=0, padx=5, pady=2, sticky="w"
        )
        self.bs_method_var = tk.StringVar(value=self.config.blank_subtraction_method)
        bs_combo = ttk.Combobox(
            bs_frame,
            textvariable=self.bs_method_var,
            values=["1", "2"],
            state="readonly",
        )
        bs_combo.grid(row=0, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(bs_frame, text="Std Deviations (for Method 2):").grid(
            row=1, column=0, padx=5, pady=2, sticky="w"
        )
        self.std_dev_entry = ttk.Entry(bs_frame)
        self.std_dev_entry.insert(
            0, str(getattr(self.config, "blank_subtraction_std_dev", 3.0))
        )
        self.std_dev_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        self.param_entries["blank_subtraction_std_dev"] = self.std_dev_entry

        bs_combo.bind("<<ComboboxSelected>>", self._toggle_std_dev_entry)
        self._toggle_std_dev_entry()

        reg_frame = ttk.LabelFrame(tab, text="Regression Analysis", padding=(10, 5))
        reg_frame.pack(fill="x", padx=10, pady=5, anchor="w")

        self.rt_reg_var = tk.BooleanVar(
            value=getattr(self.config, "rt_regression_filter", False)
        )
        rt_check = ttk.Checkbutton(
            reg_frame, text="Apply RT Regression Filter", variable=self.rt_reg_var
        )
        rt_check.pack(anchor="w", padx=5)

        self.ccs_reg_var = tk.BooleanVar(
            value=getattr(self.config, "ccs_regression_filter", True)
        )
        ccs_check = ttk.Checkbutton(
            reg_frame, text="Apply CCS Regression Filter", variable=self.ccs_reg_var
        )
        ccs_check.pack(anchor="w", padx=5)

    def _toggle_std_dev_entry(self, event=None):
        if self.bs_method_var.get() == "2":
            self.std_dev_entry.config(state="normal")
        else:
            self.std_dev_entry.config(state="disabled")

    def _create_run_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Run Workflow")
        run_button = ttk.Button(
            tab, text="Run PIMMS Workflow", command=self.run_workflow_thread
        )
        run_button.pack(pady=20)
        self.log_text = tk.Text(tab, height=20, width=80, state="disabled", wrap="word")
        self.log_text.pack(pady=10, padx=10, expand=True, fill="both")
        sys.stdout = TextRedirector(self.log_text, "stdout")

    def _create_file_input(self, parent, label_text, config_key, row):
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

    def _browse_file(self, entry, key):
        if "output" in key:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv", filetypes=[("CSV files", "*.csv")]
            )
        else:
            filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if filename:
            entry.delete(0, tk.END)
            entry.insert(0, filename)

    def run_workflow_thread(self):
        try:
            for key, entry in self.file_path_entries.items():
                setattr(self.config, key, entry.get())
            for key, entry in self.param_entries.items():
                setattr(self.config, key, float(entry.get()))

            self.config.blank_subtraction_method = self.bs_method_var.get()

            self.config.rt_regression_filter = self.rt_reg_var.get()
            self.config.ccs_regression_filter = self.ccs_reg_var.get()

            self.config.control_start_col = self.mapping_entries[
                "control_start_col"
            ].get()
            self.config.control_end_col = self.mapping_entries["control_end_col"].get()
            self.config.experimental_start_col = self.mapping_entries[
                "experimental_start_col"
            ].get()
            self.config.experimental_end_col = self.mapping_entries[
                "experimental_end_col"
            ].get()

            self.config.metadata_mapping = {
                k: self.mapping_entries[f"meta_{k}"].get()
                for k in self.config.metadata_mapping
            }
            self.config.level_2_library_mapping = {
                k: self.mapping_entries[f"l2_{k}"].get()
                for k in self.config.level_2_library_mapping
            }
            self.config.level_5_library_mapping = {
                k: self.mapping_entries[f"l5_{k}"].get()
                for k in self.config.level_5_library_mapping
            }

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
                f"An unexpected error occurred before starting the workflow: {e}",
            )


class TextRedirector(object):
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, str):
        self.widget.configure(state="normal")
        self.widget.insert("end", str, (self.tag,))
        self.widget.configure(state="disabled")
        self.widget.see("end")

    def flush(self):
        pass


if __name__ == "__main__":
    app = PimmsGUI()
    app.mainloop()
