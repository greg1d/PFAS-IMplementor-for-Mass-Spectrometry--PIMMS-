import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import pandas as pd


class ScrollableTable(ttk.Frame):
    """Scrollable Treeview with working horizontal and vertical scrollbars."""

    def __init__(self, parent):
        super().__init__(parent)

        # --- Proper layout configuration ---
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Treeview setup ---
        self.tree = ttk.Treeview(self, show="headings")
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # --- Layout with sticky expansion ---
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # The problematic .bind() and _on_frame_resize method have been removed.

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

            # Correctly and safely calculate max data width
            max_data_width = 0
            if not df[col].empty:
                # Use .max() on the result of .apply()
                max_data_width = df[col].head(100).astype(str).apply(font.measure).max()

            # Ensure max_data_width is not NaN before converting to int
            safe_max_data_width = max_data_width if pd.notna(max_data_width) else 0

            # Calculate the width needed for the content
            content_width = max(header_width, int(safe_max_data_width)) + 30

            # Set the final width to be at least 120px
            final_width = max(content_width, 120)

            self.tree.column(col, width=final_width, anchor=tk.W, stretch=False)

        for _, row in df.iterrows():
            self.tree.insert("", "end", values=[v if pd.notna(v) else "" for v in row])
