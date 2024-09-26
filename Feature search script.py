import pandas as pd
import os
import glob
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.widgets import RectangleSelector
from matplotlib.ticker import FormatStrFormatter
import matplotlib.ticker as mtick

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

def toggle_selector(event):
    if event.key == 't':
        if toggle_selector.RS.active:
            print('RectangleSelector deactivated.')
            toggle_selector.RS.set_active(False)
        else:
            print('RectangleSelector activated.')
            toggle_selector.RS.set_active(True)

def reset_zoom(event, ax, original_xlim, original_ylim):
    if event.key == 'r':
        ax.set_xlim(original_xlim)
        ax.set_ylim(original_ylim)
        plt.draw()

# Function to perform the search with ppm error for m/z and Name_or_Class search
def search_feature(name_or_class=None, mz_value=None, ppm_error=None, sheet_options=None, result_tree=None):
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
    
    # Create a figure and axes
    fig, ax = plt.subplots(figsize=(5, 5))

    # Define marker shapes and categories
    marker_shapes = {'Likely': 's', 'Tentative (EPA match)': '^', 'Tentative (No EPA match)': 'o'}

    # Plot each category with different marker shapes
    for sheet_type, marker in marker_shapes.items():
        subset = result_df[result_df['Sheet'] == sheet_type]
        ax.scatter(subset['m/z'], subset['CCS'], c=subset['Intensity'], cmap='flare', marker=marker, picker=True, s=25, zorder=2)

    # Plot the Gaussian KDE overlay on the same axes
    sns.kdeplot(x=result_df['m/z'], y=result_df['CCS'], ax=ax, cmap='Greys', fill=True, alpha=1, zorder=1)
    global original_xlim, original_ylim
    original_xlim = (result_df['m/z'].min() - 0.001, result_df['m/z'].max() + 0.001)
    original_ylim = (result_df['CCS'].min() - 3, result_df['CCS'].max() + 3)
    ax.set_xlim(original_xlim)
    ax.set_ylim(original_ylim)
    def custom_format(x, pos):
    # Check if the number has decimal places
        if int(x) == x:  # If the number is an integer
            return f'{int(x)}'  # Display as an integer with no decimals
        elif x * 10 == int(x * 10):  # If the number has 1 decimal place
            return f'{x:.1f}'  # Display with 1 decimal place
        elif x * 100 == int(x * 100):  # If the number has 2 decimal places
            return f'{x:.2f}'  # Display with 2 decimal places
        elif x * 1000 == int(x * 1000):  # If the number has 3 decimal places
            return f'{x:.3f}'  # Display with 3 decimal places
        else:  # For numbers with more decimal places
            return f'{x:.4f}'  # Display with 4 decimal places
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(custom_format))
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(custom_format))
    font_properties = {'family': 'Arial', 'size': 10, 'weight': 'bold'}
    if name_class_entry.get():  # If name_class_entry is not empty
        title = f"for '{name_class_entry.get()}'"
    elif mz_entry.get():  # If name_class_entry is empty but mz_entry has a value
        ppm_tolerance = int(ppm_entry.get())  # User-defined PPM error
        title = f"at {mz_entry.get()} with {ppm_tolerance} PPM"
    else:
        title = "No Filter"
    
# Set the plot title using the defined logic
    ax.set_title(f"CCS vs m/z {title}", fontdict={'fontsize': 10, 'fontweight': 'bold', 'fontname': 'Arial'})

    # Add a color bar to indicate intensity
    fig.colorbar(ax.collections[0], label='Intensity')

    # Set titles and labels
    ax.set_xlabel('m/z', fontdict=font_properties)
    ax.set_ylabel(r'$\mathbf{CCS\ (\mathrm{\AA^2})}$', fontdict=font_properties)

    # Adjust tick label size and font
    ax.tick_params(axis='both', which='major', labelsize=10)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontname('Arial')
        label.set_fontweight('bold')

    # Add grey marker shapes to the legend (without plotting points again)
    for sheet_type, marker in marker_shapes.items():
        ax.scatter([], [], label=sheet_type, marker=marker, color='gray')

    # Position the legend horizontally within the plot's width
    ax.legend(loc='upper center', ncol=2, fancybox=True, shadow=False, mode='expand',
              fontsize=8, handletextpad=0.3)  
    # Interactive click function to show point data
    def onpick(event):
        ind = event.ind
        selected_points = result_df.iloc[ind]
        info = ""
        for _, point in selected_points.iterrows():
            point_info = (f"File: {point['File']}\n"
                          f"Retention Time: {point['Retention Time']}\n"
                          f"CCS: {point['CCS']}\n"
                          f"m/z: {point['m/z']}\n"
                          f"Intensity: {point['Intensity']}\n\n")
            info += point_info
        
        # Display all selected points in a text box for easy copying
        if info:
            dialog_box(info)

    # Function to create a dialog box with copyable content
    def dialog_box(info):
        top = tk.Toplevel()
        top.title("Selected Points Info")
        top.geometry("800x400")  # Set the width and height as desired

        # Create a scrollable text widget
        text_box = tk.Text(top, wrap='word', height=15, width=60)
        text_box.insert('1.0', info)  # Insert the info into the text widget
        text_box.config(state=tk.NORMAL)  # Set to NORMAL to allow copying
        text_box.pack(expand=True, fill='both')

        # Add a scrollbar
        scrollbar = tk.Scrollbar(text_box, command=text_box.yview)
        scrollbar.pack(side='right', fill='y')
        text_box.config(yscrollcommand=scrollbar.set)

        # Add a close button
        close_button = tk.Button(top, text="Close", command=top.destroy)
        close_button.pack(pady=5)

    # Connect the pick event for selecting points
    fig.canvas.mpl_connect('pick_event', onpick)


    def line_select_callback(event1, event2):
        x1, y1 = event1.xdata, event1.ydata
        x2, y2 = event2.xdata, event2.ydata
        ax.set_xlim(min(x1, x2), max(x1, x2))
        ax.set_ylim(min(y1, y2), max(y1, y2))
        plt.draw()

    toggle_selector.RS = RectangleSelector(ax, line_select_callback,
                                           drawtype='box', useblit=True,
                                           button=[3],  # right mouse button
                                           minspanx=5, minspany=5,
                                           spancoords='pixels',
                                           interactive=True)
    
    fig.canvas.mpl_connect('key_press_event', toggle_selector)
    fig.canvas.mpl_connect('key_press_event', lambda event: reset_zoom(event, ax, original_xlim, original_ylim))

    plt.tight_layout()
    plt.show()

# Function to visualize CCS vs Retention Time
def visualize_ccs_vs_rt(result_df):
    if result_df is None or result_df.empty:
        messagebox.showwarning("No Data", "No data available to visualize.")
        return
    
    # Create a figure and axes
    fig, ax = plt.subplots(figsize=(5, 5))

    # Define marker shapes and categories
    marker_shapes = {'Likely': 's', 'Tentative (EPA match)': '^', 'Tentative (No EPA match)': 'o'}

    # Plot each category with different marker shapes
    for sheet_type, marker in marker_shapes.items():
        subset = result_df[result_df['Sheet'] == sheet_type]
        ax.scatter(subset['Retention Time'], subset['CCS'], c=subset['Intensity'], cmap='flare', marker=marker, picker=True, s=25, zorder=2)

    # Plot the Gaussian KDE overlay on the same axes
    sns.kdeplot(x=result_df['Retention Time'], y=result_df['CCS'], ax=ax, cmap='Greys', fill=True, alpha=1, zorder=1)
    global original_xlim, original_ylim
    original_xlim = (result_df['Retention Time'].min() - 0.2, result_df['Retention Time'].max() + 0.2)
    original_ylim = (result_df['CCS'].min() - 3, result_df['CCS'].max() + 3)
    ax.set_xlim(original_xlim)
    ax.set_ylim(original_ylim)
    def custom_format(x, pos):
    # Check if the number has decimal places
        if int(x) == x:  # If the number is an integer
            return f'{int(x)}'  # Display as an integer with no decimals
        elif x * 10 == int(x * 10):  # If the number has 1 decimal place
            return f'{x:.1f}'  # Display with 1 decimal place
        elif x * 100 == int(x * 100):  # If the number has 2 decimal places
            return f'{x:.2f}'  # Display with 2 decimal places
        elif x * 1000 == int(x * 1000):  # If the number has 3 decimal places
            return f'{x:.3f}'  # Display with 3 decimal places
        else:  # For numbers with more decimal places
            return f'{x:.4f}'  # Display with 4 decimal places
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(custom_format))
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(custom_format))
    font_properties = {'family': 'Arial', 'size': 10, 'weight': 'bold'}
    if name_class_entry.get():  # If name_class_entry is not empty
        title = f"for '{name_class_entry.get()}'"
    elif mz_entry.get():  # If name_class_entry is empty but mz_entry has a value
        ppm_tolerance = int(ppm_entry.get())  # User-defined PPM error
        title = f"at {mz_entry.get()} with {ppm_tolerance} PPM"
    else:
        title = "No Filter"
    
# Set the plot title using the defined logic
    ax.set_title(f"CCS vs Retention Time {title}", fontdict={'fontsize': 10, 'fontweight': 'bold', 'fontname': 'Arial'})

    # Add a color bar to indicate intensity
    fig.colorbar(ax.collections[0], label='Intensity')

    # Set titles and labels
    ax.set_xlabel('Retention Time (min)', fontdict=font_properties)
    ax.set_ylabel(r'$\mathbf{CCS\ (\mathrm{\AA^2})}$', fontdict=font_properties)

    # Adjust tick label size and font
    ax.tick_params(axis='both', which='major', labelsize=10)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontname('Arial')
        label.set_fontweight('bold')

    # Add grey marker shapes to the legend (without plotting points again)
    for sheet_type, marker in marker_shapes.items():
        ax.scatter([], [], label=sheet_type, marker=marker, color='gray')

    # Position the legend horizontally within the plot's width
    ax.legend(loc='upper center', ncol=2, fancybox=True, shadow=False, mode='expand',
              fontsize=8, handletextpad=0.3)  
    # Interactive click function to show point data
    def onpick(event):
        ind = event.ind
        selected_points = result_df.iloc[ind]
        info = ""
        for _, point in selected_points.iterrows():
            point_info = (f"File: {point['File']}\n"
                          f"Retention Time: {point['Retention Time']}\n"
                          f"CCS: {point['CCS']}\n"
                          f"m/z: {point['m/z']}\n"
                          f"Intensity: {point['Intensity']}\n\n")
            info += point_info
        
        # Display all selected points in a text box for easy copying
        if info:
            dialog_box(info)

    # Function to create a dialog box with copyable content
    def dialog_box(info):
        top = tk.Toplevel()
        top.title("Selected Points Info")
        top.geometry("800x400")  # Set the width and height as desired

        # Create a scrollable text widget
        text_box = tk.Text(top, wrap='word', height=15, width=60)
        text_box.insert('1.0', info)  # Insert the info into the text widget
        text_box.config(state=tk.NORMAL)  # Set to NORMAL to allow copying
        text_box.pack(expand=True, fill='both')

        # Add a scrollbar
        scrollbar = tk.Scrollbar(text_box, command=text_box.yview)
        scrollbar.pack(side='right', fill='y')
        text_box.config(yscrollcommand=scrollbar.set)

        # Add a close button
        close_button = tk.Button(top, text="Close", command=top.destroy)
        close_button.pack(pady=5)

    # Connect the pick event for selecting points
    fig.canvas.mpl_connect('pick_event', onpick)


    def line_select_callback(event1, event2):
        x1, y1 = event1.xdata, event1.ydata
        x2, y2 = event2.xdata, event2.ydata
        ax.set_xlim(min(x1, x2), max(x1, x2))
        ax.set_ylim(min(y1, y2), max(y1, y2))
        plt.draw()

    toggle_selector.RS = RectangleSelector(ax, line_select_callback,
                                           drawtype='box', useblit=True,
                                           button=[3],  # right mouse button
                                           minspanx=5, minspany=5,
                                           spancoords='pixels',
                                           interactive=True)
    
    fig.canvas.mpl_connect('key_press_event', toggle_selector)
    fig.canvas.mpl_connect('key_press_event', lambda event: reset_zoom(event, ax, original_xlim, original_ylim))

    plt.tight_layout()
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

    # Get the user-defined ppm tolerance value
    try:
        ppm_tolerance = int(ppm_entry.get())  # User-defined PPM error
    except ValueError:
        messagebox.showerror("Error", "Invalid PPM value")
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

    result_df = search_feature(name_or_class, mz_value, ppm_error=ppm_tolerance, sheet_options=sheet_options, result_tree=result_tree)
    
    # Enable visualization buttons once search is performed
    if result_df is not None:
        ccs_vs_mz_button.config(state=tk.NORMAL)
        ccs_vs_mz_button.result_df = result_df

        ccs_vs_rt_button.config(state=tk.NORMAL)
        ccs_vs_rt_button.result_df = result_df

#
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

# Label and input field for PPM tolerance
tk.Label(window, text="PPM Tolerance:").grid(row=2, column=0, padx=10, pady=10)
ppm_entry = tk.Entry(window, width=30)
ppm_entry.grid(row=2, column=1, padx=10, pady=10)
ppm_entry.insert(0, "10")  # Default value for ppm

# Checkboxes for sheet selection
likely_var = tk.IntVar()
epa_var = tk.IntVar()
no_epa_var = tk.IntVar()

tk.Checkbutton(window, text="Likely", variable=likely_var).grid(row=3, column=0, padx=10, pady=10)
tk.Checkbutton(window, text="Tentative (EPA Match)", variable=epa_var).grid(row=3, column=1, padx=10, pady=10)
tk.Checkbutton(window, text="Tentative (No EPA Match)", variable=no_epa_var).grid(row=3, column=2, padx=10, pady=10)

# Button to initiate the search
search_button = tk.Button(window, text="Search", command=search_button_click)
search_button.grid(row=4, column=1, padx=10, pady=10)

# Treeview to display search results
columns = ('File', 'Sheet', 'Name_or_Class', 'm/z', 'DT', 'CCS', 'Retention Time', 'Intensity')
result_tree = ttk.Treeview(window, columns=columns, show='headings', height=10)
for col in columns:
    result_tree.heading(col, text=col)
    result_tree.column(col, width=100)

result_tree.grid(row=5, column=0, columnspan=3, padx=10, pady=10)

# Buttons to visualize CCS vs m/z and CCS vs Retention Time
ccs_vs_mz_button = tk.Button(window, text="Visualize CCS vs m/z", state=tk.DISABLED, command=lambda: visualize_ccs_vs_mz(ccs_vs_mz_button.result_df))
ccs_vs_mz_button.grid(row=6, column=0, padx=10, pady=10)

ccs_vs_rt_button = tk.Button(window, text="Visualize CCS vs Retention Time", state=tk.DISABLED, command=lambda: visualize_ccs_vs_rt(ccs_vs_rt_button.result_df))
ccs_vs_rt_button.grid(row=6, column=2, padx=10, pady=10)

# Start the GUI event loop
window.mainloop()
