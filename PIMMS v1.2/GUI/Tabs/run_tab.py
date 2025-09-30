# gui/tabs/run_tab.py

import tkinter as tk
from tkinter import ttk

# --- NEW: Import the Tooltip class ---
from ..widgets.tooltip import Tooltip


class RunTab(ttk.Frame):
    def __init__(self, parent, run_callback, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.run_callback = run_callback
        self._create_widgets()

    def _create_widgets(self):
        """Creates all widgets for the run tab."""

        # --- NEW: Create a frame to hold the button and help icon together ---
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=20)

        # The button's parent is now the new frame
        run_button = ttk.Button(
            button_frame, text="Run PIMMS Workflow", command=self.run_callback
        )
        run_button.pack(side="left", padx=5)

        # --- NEW: Add the help icon and tooltip ---
        help_text = "Click to start the PIMMS workflow using all configured settings from the previous tabs. \n\nLet's find some PFAS!"
        help_label = ttk.Label(button_frame, text=" (?) ", cursor="question_arrow")
        help_label.pack(side="left", anchor="center")
        Tooltip(help_label, text=help_text, wraplength=300)

        # The log text widget remains the same
        self.log_text = tk.Text(
            self, height=20, width=80, state="disabled", wrap="word"
        )
        self.log_text.pack(pady=10, padx=10, expand=True, fill="both")

    # This tab does not need an 'update_config' method as it doesn't hold configuration data.
