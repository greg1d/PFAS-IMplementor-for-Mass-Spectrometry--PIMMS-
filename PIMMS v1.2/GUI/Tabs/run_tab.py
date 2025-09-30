# gui/tabs/run_tab.py

import tkinter as tk
from tkinter import ttk


class RunTab(ttk.Frame):
    def __init__(self, parent, run_callback, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.run_callback = run_callback
        self._create_widgets()

    def _create_widgets(self):
        """Creates all widgets for the run tab."""
        run_button = ttk.Button(
            self, text="Run PIMMS Workflow", command=self.run_callback
        )
        run_button.pack(pady=20)

        self.log_text = tk.Text(
            self, height=20, width=80, state="disabled", wrap="word"
        )
        self.log_text.pack(pady=10, padx=10, expand=True, fill="both")

    # This tab does not need an 'update_config' method as it doesn't hold configuration data.
