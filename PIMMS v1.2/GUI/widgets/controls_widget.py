import tkinter as tk
from tkinter import messagebox, ttk


class ControlsWidget(ttk.Labelframe):
    """A self-contained widget for user input controls."""

    def __init__(self, parent, load_callback, analyze_callback):
        super().__init__(parent, text="Controls")

        # Callbacks are functions passed in from the parent (the VisualizationsTab)
        self.load_callback = load_callback
        self.analyze_callback = analyze_callback

        self._create_widgets()

    def _create_widgets(self):
        self.load_btn = ttk.Button(
            self, text="Load Report File...", command=self.load_callback
        )
        self.load_btn.pack(side=tk.LEFT, padx=10, pady=10)

        self.file_label = ttk.Label(self, text="No file loaded.")
        self.file_label.pack(side=tk.LEFT, padx=10, pady=10)

        analysis_frame = ttk.Frame(self)
        analysis_frame.pack(side=tk.LEFT, padx=20, pady=5, fill=tk.X, expand=True)

        ttk.Label(analysis_frame, text="Repeating Unit (e.g., CF2:49.9968):").grid(
            row=0, column=0, sticky="w"
        )
        self.unit_entry = ttk.Entry(analysis_frame, width=20)
        self.unit_entry.insert(0, "CF2:49.9968")
        self.unit_entry.grid(row=0, column=1, padx=5)

        self.reanalyze_btn = ttk.Button(
            self,
            text="Find Trends & Plot",
            state="disabled",
            command=self.analyze_callback,
        )
        self.reanalyze_btn.pack(side=tk.RIGHT, padx=10, pady=10)

    def get_repeating_units(self):
        """Parses the text from the entry box into a dictionary."""
        try:
            text = self.unit_entry.get()
            if not text:
                return {}
            name, mass = text.split(":")
            return {name.strip(): float(mass)}
        except Exception:
            messagebox.showerror(
                "Invalid Format", "Repeating unit must be 'Name:Mass'."
            )
            return None

    def set_file_label(self, text):
        self.file_label.config(text=text)

    def set_analyze_button_state(self, state):
        self.reanalyze_btn.config(state=state)
