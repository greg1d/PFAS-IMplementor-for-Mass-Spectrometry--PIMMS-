from tkinter import Tk, Label, Button, Frame, Canvas, Scrollbar, StringVar


def launch_column_selection_gui(column_names):
    """
    Launch a GUI to allow users to assign each sample to control, experimental, or exclude groups.

    Args:
        column_names (list): List of column names to display.

    Returns:
        dict: Dictionary with control, experimental, and excluded selections.
    """

    def assign_to_group(sample, group_name, label_var):
        # Remove the sample from all groups first
        for group in selections:
            if sample in selections[group]:
                selections[group].remove(sample)

        # Add the sample to the selected group
        if group_name != "exclude":
            selections[group_name].append(sample)

        # Update the label to reflect the selected group
        label_var.set(group_name.capitalize())

        # Update the summary labels
        update_selection_labels()

    def update_selection_labels():
        control_label_var.set(f"Control Samples: {', '.join(selections['control'])}")
        experimental_label_var.set(
            f"Experimental Samples: {', '.join(selections['experimental'])}"
        )
        exclude_label_var.set(f"Excluded Samples: {', '.join(selections['exclude'])}")

    def finalize_selection():
        root.destroy()

    # Create the main GUI window
    root = Tk()
    root.title("Select Experimental, Control, or Exclude Samples")
    root.geometry("900x600")

    # Create a scrollable canvas
    canvas = Canvas(root)
    scrollbar = Scrollbar(root, orient="vertical", command=canvas.yview)
    scrollable_frame = Frame(canvas)

    # Configure the canvas to use the scrollbar
    scrollable_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Add rows for each sample with buttons and labels
    for col_name in column_names:
        row = Frame(scrollable_frame)
        row.pack(fill="x", padx=10, pady=5)

        # Display the sample name
        Label(row, text=col_name, width=40, anchor="w").pack(side="left")

        # Display the default selection label
        label_var = StringVar()
        label_var.set("Experimental")
        Label(row, textvariable=label_var, width=15).pack(side="left")

        # Add buttons for control, experimental, and exclude selection
        Button(
            row,
            text="Set as Control",
            command=lambda sample=col_name, var=label_var: assign_to_group(
                sample, "control", var
            ),
        ).pack(side="left", padx=5)

        Button(
            row,
            text="Set as Experimental",
            command=lambda sample=col_name, var=label_var: assign_to_group(
                sample, "experimental", var
            ),
        ).pack(side="left", padx=5)

        Button(
            row,
            text="Exclude",
            command=lambda sample=col_name, var=label_var: assign_to_group(
                sample, "exclude", var
            ),
        ).pack(side="left", padx=5)

    # Labels to display the current selections
    control_label_var = StringVar()
    experimental_label_var = StringVar()
    exclude_label_var = StringVar()
    control_label_var.set("Control Samples: None")
    experimental_label_var.set(
        f"Experimental Samples: {', '.join(column_names)}"
    )  # Default all to experimental
    exclude_label_var.set("Excluded Samples: None")

    selections = {
        "control": [],
        "experimental": column_names.copy(),  # Default all to experimental
        "exclude": [],
    }  # Initialize selections

    Label(root, textvariable=control_label_var, wraplength=800, justify="left").pack(
        pady=10
    )
    Label(
        root, textvariable=experimental_label_var, wraplength=800, justify="left"
    ).pack(pady=10)
    Label(root, textvariable=exclude_label_var, wraplength=800, justify="left").pack(
        pady=10
    )

    # Finalize button
    Button(root, text="Finalize Selection", command=finalize_selection).pack(pady=20)

    # Run the GUI event loop
    root.mainloop()

    return selections
