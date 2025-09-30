# gui/widgets/tooltip.py

import tkinter as tk


class Tooltip:
    """
    Creates a tooltip (pop-up) for a given widget.
    """

    def __init__(self, widget, text, wraplength=250):
        self.widget = widget
        self.text = text
        self.wraplength = wraplength
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        """Display the tooltip"""
        if self.tooltip_window or not self.text:
            return

        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        # Creates a toplevel window
        self.tooltip_window = tk.Toplevel(self.widget)

        # Removes the window decoration
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffe0",  # Light yellow background
            relief=tk.SOLID,
            borderwidth=1,
            wraplength=self.wraplength,
        )
        label.pack(ipadx=5, ipady=5)

    def hide_tip(self, event=None):
        """Hide the tooltip"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None
