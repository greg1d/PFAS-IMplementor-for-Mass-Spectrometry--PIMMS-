import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import pandas as pd


class ScrollableTable(ttk.Frame):
    """Scrollable Treeview with working horizontal and vertical scrollbars."""

    def __init__(self, parent):
        super().__init__(parent)

        # --- Proper layout configuration ---
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # --- Treeview setup ---
        self.tree = ttk.Treeview(self, show="headings")
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # --- Layout with sticky expansion ---
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # --- Make sure the frame expands with its parent ---
        self.bind("<Configure>", self._on_frame_resize)

    def _on_frame_resize(self, event):
        """Force treeview width to expand with the parent frame."""
        self.tree.configure(width=event.width)

    def update_table(self, df):
        """Clears the table and populates it with data from a DataFrame."""
        self.tree.delete(*self.tree.get_children())

        if df is None or df.empty:
            self.tree["columns"] = []
            return

        self.tree["columns"] = list(df.columns)
        font = tkfont.Font()

        for col in df.columns:
            self.tree.heading(col, text=col, anchor=tk.W)
            header_width = font.measure(col)
            max_data_width = (
                df[col].head(100).astype(str).apply(font.measure).max()
                if not df[col].empty
                else 0
            )
            safe_max = max(header_width, int(max_data_width)) + 30
            self.tree.column(col, width=max(safe_max, 120), anchor=tk.W, stretch=False)

        for _, row in df.iterrows():
            self.tree.insert("", "end", values=[v if pd.notna(v) else "" for v in row])
