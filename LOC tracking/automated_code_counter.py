import os
from datetime import datetime

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from scipy.interpolate import make_interp_spline

# Set paths
output_folder = r"LOC tracking outputs"
font_path = r"fonts/NormativePro-Bold.otf"
font_prop = font_manager.FontProperties(fname=font_path)
font_manager.fontManager.addfont(font_path)
mpl.rc("font", family=font_prop.get_name())

# Ensure the output folder exists
if not os.path.exists(output_folder):
    os.makedirs(output_folder)


def read_results_md():
    data = []
    for root, dirs, files in os.walk(output_folder):
        for file in files:
            if file == "results.md":
                file_path = os.path.join(root, file)
                creation_date = datetime.fromtimestamp(
                    os.path.getctime(file_path)
                ).strftime("%Y-%m-%d")
                with open(file_path, "r") as f:
                    lines = f.readlines()
                    lines_of_code = 0
                    language_data = {
                        "JavaScript": 0,
                        "CSS": 0,
                        "HTML": 0,
                        "Python": 0,
                        "Others": 0,
                    }
                    for line in lines:
                        if line.startswith("|") and not line.startswith("| :---"):
                            parts = line.split("|")
                            if len(parts) > 3:
                                language = parts[1].strip()
                                try:
                                    code_lines = int(parts[3].replace(",", "").strip())
                                    if language in language_data:
                                        language_data[language] += code_lines
                                    else:
                                        language_data["Others"] += code_lines
                                    lines_of_code += code_lines
                                except ValueError:
                                    print(f"Skipping line due to ValueError: {line}")
                    data.append(
                        (
                            creation_date,
                            lines_of_code,
                            language_data["JavaScript"],
                            language_data["CSS"],
                            language_data["HTML"],
                            language_data["Python"],
                            language_data["Others"],
                        )
                    )
    return data


def save_data(data):
    # Load existing data if file exists
    output_file = os.path.join(output_folder, "code_metrics.xlsx")
    if os.path.exists(output_file):
        df = pd.read_excel(output_file)
    else:
        df = pd.DataFrame(
            columns=[
                "Date",
                "Lines of Code",
                "JavaScript",
                "CSS",
                "HTML",
                "Python",
                "Others",
            ]
        )

    # Create a new DataFrame for the new data
    new_data = pd.DataFrame(
        data,
        columns=[
            "Date",
            "Lines of Code",
            "JavaScript",
            "CSS",
            "HTML",
            "Python",
            "Others",
        ],
    )
    df = pd.concat([df, new_data], ignore_index=True)

    # Save to Excel
    df.to_excel(output_file, index=False)

    return df


def plot_data(df):
    # Fill any missing values with zeros
    df = df.fillna(0)

    # Create a plot with specified figure size and background color
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor("#FEF1E5")  # Set the figure background color
    ax.set_facecolor("#FEF1E5")  # Set the axes background color

    # Interpolate for smooth lines
    x = np.arange(len(df["Date"]))
    x_smooth = np.linspace(
        x.min(), x.max(), 300
    )  # Generate more points for a smooth line

    def smooth_data(column):
        spline = make_interp_spline(x, df[column], k=3)  # Cubic spline interpolation
        return spline(x_smooth)

    # Plot the smoothed lines for each language
    ax.plot(
        x_smooth,
        smooth_data("JavaScript"),
        label="JavaScript",
        color="blue",
        linewidth=3,
    )
    ax.plot(x_smooth, smooth_data("CSS"), label="CSS", color="orange", linewidth=3)
    ax.plot(x_smooth, smooth_data("HTML"), label="HTML", color="green", linewidth=3)
    ax.plot(x_smooth, smooth_data("Python"), label="Python", color="red", linewidth=3)
    ax.plot(x_smooth, smooth_data("Others"), label="Others", color="pink", linewidth=3)

    # Plot the sum of all code
    sum_of_all_code = (
        df["JavaScript"] + df["CSS"] + df["HTML"] + df["Python"] + df["Others"]
    )
    sum_of_all_code_smooth = make_interp_spline(x, sum_of_all_code, k=3)(x_smooth)
    ax.plot(
        x_smooth,
        sum_of_all_code_smooth,
        label="Sum of all code",
        color="black",
        linewidth=3,
    )

    # Modify the title to be larger and more specific
    ax.text(
        -0.05,
        1.1,
        "Coding Progress for PIMMS",
        transform=ax.transAxes,
        fontsize=18,
        weight="bold",
        color="#757575",
        va="top",
        ha="left",
    )

    # Modify the y-axis label with increased size and specific color
    ax.set_ylabel("Lines of Code", fontsize=14, color="#757575")

    # Drop the x-axis label
    ax.set_xlabel("")

    # Customize the spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#757575")  # Set color of the x-axis
    ax.spines["bottom"].set_linewidth(1.5)  # Set linewidth of the x-axis
    y = df["Lines of Code"]
    ax.set_ylim(0, y.max() * 1.3)
    # Set gridlines on the y-axis with a soft grey color and interval of 500
    ax.grid(axis="y", color="lightgrey", linestyle="--", linewidth=0.7)
    ax.set_yticks(
        range(
            0,
            int(
                df[["JavaScript", "CSS", "HTML", "Python", "Others"]].sum(axis=1).max()
                * 1.3
            )
            + 100,
            500,
        )
    )

    # Set color for y-axis tick labels
    ax.tick_params(axis="y", colors="#757575")

    # Rotate x-axis labels for clarity and set their color
    plt.xticks(np.arange(len(df["Date"])), df["Date"], rotation=45, color="#757575")

    # Display the legend without border
    legend = ax.legend(frameon=False, fontsize=12, loc="lower right")
    for text in legend.get_texts():
        text.set_color("#757575")
    date = datetime.now().strftime("%Y-%m-%d-%H-%M")

    # Ensure the layout is tight and no overlaps occur
    plt.tight_layout()
    output_image_path = os.path.join(output_folder, f"coding_progress_{date}.png")
    plt.savefig(output_image_path, format="png", dpi=400, bbox_inches="tight")
    # Show the plot
    plt.show()


def main():
    data = read_results_md()
    df = save_data(data)
    plot_data(df)


if __name__ == "__main__":
    main()
