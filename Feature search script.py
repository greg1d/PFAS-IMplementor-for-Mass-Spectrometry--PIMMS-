import pandas as pd
import os
import glob
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.backend_bases import MouseButton

# Define the directory containing the Excel files
directory_path = r'F:\Twins Project (2.24-)\Non-target work\All Features Master 2'

# Define the directory to save the search results
output_directory = r'F:\Twins Project (2.24-)\Non-target work\All Features Master\Search Results'
os.makedirs(output_directory, exist_ok=True)  # Create the directory if it doesn't exist

# Find all Excel files in the directory
excel_files = glob.glob(os.path.join(directory_path, '*.xlsx'))

# Define a mapping for sheet options
sheet_mapping = {
    1: 'Likely',
    2: 'Tentative (EPA match)',
    3: 'Tentative (No EPA match)'
}

# Function to perform the search with ppm error for m/z and Name_or_Class search
def search_feature(name_or_class=None, mz_value=None, ppm_error=10, sheet_options=None, result_tree=None):
    results = []
    
    # Iterate over each Excel file found
    for file_path in excel_files:
        for sheet_option in sheet_options:
            sheet_name = sheet_mapping.get(sheet_option, None)
            
            if not sheet_name:
                continue
            
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Find columns that match specific criteria
                ccs_column = 'CCS'
                dt_column = 'DT'
                retention_time_column = 'Retention Time'
                demp_column = next((col for col in df.columns if col.endswith('.d.DeMP')), None)
                
                # Ensure the necessary columns exist
                if not ccs_column in df.columns or not retention_time_column in df.columns or demp_column is None or dt_column not in df.columns:
                    continue

                # If m/z search is provided, calculate the ppm error range
                if mz_value is not None:
                    mz_min = mz_value - (mz_value * ppm_error / 1e6)
                    mz_max = mz_value + (mz_value * ppm_error / 1e6)
                    mz_match = df[(df['m/z'] >= mz_min) & (df['m/z'] <= mz_max)]
                else:
                    mz_match = df  # If m/z is not specified, consider all rows

                # If Name_or_Class search is provided, further filter the result
                if name_or_class is not None:
                    mz_match = mz_match[mz_match['Name_or_Class'].str.contains(name_or_class, na=False, case=False, regex=False)]

                # If any matches are found, store them along with the file and sheet information
                if not mz_match.empty:
                    for _, row in mz_match.iterrows():
                        results.append({
                            'File': os.path.basename(file_path),
                            'Sheet': sheet_name,
                            'Name_or_Class': row.get('Name_or_Class', 'N/A'),
                            'm/z': row.get('m/z', 'N/A'),
                            'DT': row.get(dt_column, 'N/A'),  # Added DT column
                            'CCS': row.get(ccs_column, 'N/A'),
                            'Retention Time': row.get(retention_time_column, 'N/A'),
                            'Intensity': row.get(demp_column, 'N/A'),
                        })
            
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue
    
    if results:
        result_df = pd.DataFrame(results)
        result_df = result_df.sort_values(by='Intensity', ascending=False)
        
        # Display the results in the GUI
        if result_tree:
            for row in result_tree.get_children():
                result_tree.delete(row)
            for _, row in result_df.iterrows():
                result_tree.insert('', 'end', values=(
                    row['File'], row['Sheet'], row['Name_or_Class'], row['m/z'], row['DT'], row['CCS'], row['Retention Time'], row['Intensity']
                ))

        # Ask the user if they want to save the results
        save_option = messagebox.askyesno("Save Results", "Do you want to save the results to an Excel file?")
        if save_option:
            file_name = filedialog.asksaveasfilename(defaultextension=".xlsx")
            if file_name:
                result_df.to_excel(file_name, index=False)
                messagebox.showinfo("Success", f"Results saved to {file_name}")
        return result_df
    else:
        messagebox.showinfo("No Matches", "No matches found.")
        return None

# Function to visualize CCS vs m/z
def visualize_ccs_vs_mz(result_df):
    if result_df is None or result_df.empty:
        messagebox.showwarning("No Data", "No data available to visualize.")
        return

    fig, ax = plt.subplots()
    scatter = ax.scatter(result_df['m/z'], result_df['CCS'], c=result_df['Intensity'], cmap='viridis', picker=True)
    fig.colorbar(scatter, label='Intensity')
    ax.set_title('CCS vs m/z')
    ax.set_xlabel('m/z')
    ax.set_ylabel('CCS')

    # Interactive click function to show point data
    def onpick(event):
        ind = event.ind
        points = result_df.iloc[ind]
        for _, point in points.iterrows():
            info = (f"File: {point['File']}\n"
                    f"Retention Time: {point['Retention Time']}\n"
                    f"CCS: {point['CCS']}\n"
                    f"m/z: {point['m/z']}\n"
                    f"Intensity: {point['Intensity']}")
        messagebox.showinfo("Selected Point Info", info)

    fig.canvas.mpl_connect('pick_event', onpick)
    plt.show()

# Function to visualize CCS vs Retention Time
def visualize_ccs_vs_rt(result_df):
    if result_df is None or result_df.empty:
        messagebox.showwarning("No Data", "No data available to visualize.")
        return

    fig, ax = plt.subplots()
    scatter = ax.scatter(result_df['Retention Time'], result_df['CCS'], c=result_df['Intensity'], cmap='viridis', picker=True)
    fig.colorbar(scatter, label='Intensity')
    ax.set_title('CCS vs Retention Time')
    ax.set_xlabel('Retention Time')
    ax.set_ylabel('CCS')

    # Interactive click function to show point data
    def onpick(event):
        ind = event.ind
        points = result_df.iloc[ind]
        for _, point in points.iterrows():
            info = (f"File: {point['File']}\n"
                    f"Retention Time: {point['Retention Time']}\n"
                    f"CCS: {point['CCS']}\n"
                    f"m/z: {point['m/z']}\n"
                    f"Intensity: {point['Intensity']}")
            print(info)
            messagebox.showinfo("Selected Point Info", info)

    fig.canvas.mpl_connect('pick_event', onpick)
    plt.show()

# Function to initiate a search using the GUI inputs
def search_button_click():
    name_or_class = name_class_entry.get()
    mz_value = mz_entry.get()

    try:
        mz_value = float(mz_value) if mz_value else None
    except ValueError:
        messagebox.showerror("Error", "Invalid m/z value")
        return
    
    sheet_options = []
    if likely_var.get():
        sheet_options.append(1)
    if epa_var.get():
        sheet_options.append(2)
    if no_epa_var.get():
        sheet_options.append(3)
    
    if not sheet_options:
        messagebox.showerror("Error", "Please select at least one sheet to search")
        return

    result_df = search_feature(name_or_class, mz_value, sheet_options=sheet_options, result_tree=result_tree)
    
    # Enable visualization buttons once search is performed
    if result_df is not None:
        ccs_vs_mz_button.config(state=tk.NORMAL)
        ccs_vs_mz_button.result_df = result_df

        ccs_vs_rt_button.config(state=tk.NORMAL)
        ccs_vs_rt_button.result_df = result_df

# Create the GUI window
window = tk.Tk()
window.title("Search Feature Tool")

# Labels and input fields for Name_or_Class and m/z
tk.Label(window, text="Name_or_Class:").grid(row=0, column=0, padx=10, pady=10)
name_class_entry = tk.Entry(window, width=30)
name_class_entry.grid(row=0, column=1, padx=10, pady=10)

tk.Label(window, text="m/z Value:").grid(row=1, column=0, padx=10, pady=10)
mz_entry = tk.Entry(window, width=30)
mz_entry.grid(row=1, column=1, padx=10, pady=10)

# Checkboxes for sheet selection
likely_var = tk.IntVar()
epa_var = tk.IntVar()
no_epa_var = tk.IntVar()

tk.Checkbutton(window, text="Likely", variable=likely_var).grid(row=2, column=0, padx=10, pady=10)
tk.Checkbutton(window, text="Tentative (EPA Match)", variable=epa_var).grid(row=2, column=1, padx=10, pady=10)
tk.Checkbutton(window, text="Tentative (No EPA Match)", variable=no_epa_var).grid(row=2, column=2, padx=10, pady=10)

# Button to initiate the search
search_button = tk.Button(window, text="Search", command=search_button_click)
search_button.grid(row=3, column=1, padx=10, pady=10)

# Treeview to display search results
columns = ('File', 'Sheet', 'Name_or_Class', 'm/z', 'DT', 'CCS', 'Retention Time', 'Intensity')
result_tree = ttk.Treeview(window, columns=columns, show='headings', height=10)
for col in columns:
    result_tree.heading(col, text=col)
    result_tree.column(col, width=100)

result_tree.grid(row=4, column=0, columnspan=3, padx=10, pady=10)

# Buttons to visualize CCS vs m/z and CCS vs Retention Time
ccs_vs_mz_button = tk.Button(window, text="Visualize CCS vs m/z", state=tk.DISABLED, command=lambda: visualize_ccs_vs_mz(ccs_vs_mz_button.result_df))
ccs_vs_mz_button.grid(row=5, column=0, padx=10, pady=10)

ccs_vs_rt_button = tk.Button(window, text="Visualize CCS vs Retention Time", state=tk.DISABLED, command=lambda: visualize_ccs_vs_rt(ccs_vs_rt_button.result_df))
ccs_vs_rt_button.grid(row=5, column=2, padx=10, pady=10)

# Start the GUI event loop
window.mainloop()
