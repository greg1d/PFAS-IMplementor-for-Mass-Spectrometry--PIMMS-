import os
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib import font_manager
import matplotlib as mpl
import numpy as np
from scipy.interpolate import make_interp_spline

# Set paths
output_folder = r"LOC tracking outputs"
output_file = os.path.join(output_folder, "code_metrics.xlsx")
font_path = r"/root/PFAS-IMplementor-for-Mass-Spectrometry--PIMMS-/Formatting/NormativePro-Bold.otf"
font_prop = font_manager.FontProperties(fname=font_path)
font_manager.fontManager.addfont(font_path)
mpl.rc('font', family=font_prop.get_name())
# Ensure the output folder exists
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

def run_scc():
    # Path to the directory to be counted
    target_directory = r"/root/PFAS-IMplementor-for-Mass-Spectrometry--PIMMS-"
    
    # Full path to the scc executable
    scc_path = "scc"  # Use the Linux-compatible version of scc

    # Build the command for scc
    scc_command = [scc_path, "--no-cocomo", target_directory]

    # Print the command being executed
    print("Running command:", " ".join(scc_command))

    result = subprocess.run(scc_command, capture_output=True, text=True)
    output = result.stdout
    error_output = result.stderr

    # Print the output of the command
    print("scc output:")
    print(output)

    # Print the error output of the command
    if error_output:
        print("scc error output:")
        print(error_output)

    # Check if the output is empty
    if not output:
        print("Error: No output from scc command")
        return 0, {}

    # Extract relevant data (e.g., lines of code)
    lines_of_code = 0
    language_data = {
        "JavaScript": 0,
        "CSS": 0,
        "HTML": 0,
        "Python": 0,
        "Others": 0
    }
    for line in output.splitlines():
        print(f"Processing line: {line}")  # Debugging line to print each line of output
        if "Total" in line:
            parts = line.split()
            try:
                lines_of_code = int(parts[2])  # Assuming the 3rd column is lines of code
            except ValueError:
                print(f"Skipping line due to ValueError: {line}")
        elif "Language" not in line and "Files" not in line:
            parts = line.split()
            if len(parts) > 4:
                language = parts[0]
                try:
                    code_lines = int(parts[2])  # Assuming the 3rd column is lines of code
                    if language in language_data:
                        language_data[language] += code_lines
                    else:
                        language_data["Others"] += code_lines
                except ValueError:
                    print(f"Skipping line due to ValueError: {line}")

    return lines_of_code, language_data


def save_data(lines_of_code, language_data):
    # Get the current date
    date = datetime.now().strftime("%Y-%m-%d")

    # Load existing data if file exists
    if os.path.exists(output_file):
        df = pd.read_excel(output_file)
    else:
        df = pd.DataFrame(columns=["Date", "Lines of Code", "JavaScript", "CSS", "HTML", "Python", "Others"])

    # Create a new DataFrame for the new row
    new_row = pd.DataFrame({
        "Date": [date],
        "Lines of Code": [lines_of_code],
        "JavaScript": [language_data["JavaScript"]],
        "CSS": [language_data["CSS"]],
        "HTML": [language_data["HTML"]],
        "Python": [language_data["Python"]],
        "Others": [language_data["Others"]]
    })
    # Concatenate the new row with the existing DataFrame
    df = pd.concat([df, new_row], ignore_index=True)

    # Save to Excel
    df.to_excel(output_file, index=False)

    return df

def plot_data(df):
    # Fill any missing values with zeros
    df = df.fillna(0)

    # Create a plot with specified figure size and background color
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('#FEF1E5')  # Set the figure background color
    ax.set_facecolor('#FEF1E5')  # Set the axes background color

    # Interpolate for smooth lines
    x = np.arange(len(df["Date"]))
    x_smooth = np.linspace(x.min(), x.max(), 300)  # Generate more points for a smooth line

    def smooth_data(column):
        spline = make_interp_spline(x, df[column], k=3)  # Cubic spline interpolation
        return spline(x_smooth)

    # Plot the smoothed lines for each language
    ax.plot(x_smooth, smooth_data("JavaScript"), label="JavaScript", color='blue', linewidth=3)
    ax.plot(x_smooth, smooth_data("CSS"), label="CSS", color='orange', linewidth=3)
    ax.plot(x_smooth, smooth_data("HTML"), label="HTML", color='green', linewidth=3)
    ax.plot(x_smooth, smooth_data("Python"), label="Python", color='red', linewidth=3)
    ax.plot(x_smooth, smooth_data("Others"), label="Others", color='pink', linewidth=3)

    # Plot the sum of all code
    sum_of_all_code = df["JavaScript"] + df["CSS"] + df["HTML"] + df["Python"] + df["Others"]
    sum_of_all_code_smooth = make_interp_spline(x, sum_of_all_code, k=3)(x_smooth)
    ax.plot(x_smooth, sum_of_all_code_smooth, label="Sum of all code", color='black', linewidth=3)

    # Modify the title to be larger and more specific
    ax.text(-0.05, 1.1, "Coding Progress for the Website", transform=ax.transAxes,
            fontsize=18, weight='bold', color='#757575', va='top', ha='left')
        
    # Modify the y-axis label with increased size and specific color
    ax.set_ylabel("Lines of Code", fontsize=14, color='#757575')
    
    # Drop the x-axis label
    ax.set_xlabel("")
    
    # Customize the spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('#757575')  # Set color of the x-axis
    ax.spines['bottom'].set_linewidth(1.5)  # Set linewidth of the x-axis
    
    # Set gridlines on the y-axis with a soft grey color and interval of 500
    ax.grid(axis='y', color='lightgrey', linestyle='--', linewidth=0.7)
    ax.set_yticks(range(0, int(df[["JavaScript", "CSS", "HTML", "Python", "Others"]].sum(axis=1).max()) + 100, 100))
    
    # Set color for y-axis tick labels
    ax.tick_params(axis='y', colors='#757575')
    
    # Rotate x-axis labels for clarity and set their color
    plt.xticks(np.arange(len(df["Date"])), df["Date"], rotation=45, color='#757575')
    
    # Display the legend without border
    legend = ax.legend(frameon=False, fontsize=12, loc='lower right')
    for text in legend.get_texts():
        text.set_color('#757575')
    date = datetime.now().strftime("%Y-%m-%d-%H-%M")

    # Ensure the layout is tight and no overlaps occur
    plt.tight_layout()
    output_image_path = os.path.join(output_folder, f"coding_progress_{date}.png")
    plt.savefig(output_image_path, format='png', dpi=400, bbox_inches='tight')
    # Show the plot
    plt.show()

def main():
    lines_of_code, language_data = run_scc()
    df = save_data(lines_of_code, language_data)
    plot_data(df)

if __name__ == "__main__":
    main()