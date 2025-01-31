import os
from datetime import datetime

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.dates import DateFormatter, AutoDateLocator
from scipy.interpolate import make_interp_spline

# Set paths
output_folder = r"LOC tracking outputs"
font_path = r"PIMMS v1.3/fonts/NormativePro-Bold.otf"
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
                ).strftime("%Y-%m-%d %H:%M:%S")
                with open(file_path, "r") as f:
                    lines = f.readlines()
                    lines_of_code = 0
                    language_data = {
                        "JavaScript": 0,
                        "CSS": 0,
                        "HTML": 0,
                        "Python": 0,
                    }
                    for line in lines:
                        if (
                            line.startswith("|")
                            and not line.startswith("| :---")
                            and not line.startswith("| language")
                            and not line.startswith("| path")
                        ):
                            parts = line.split("|")
                            if len(parts) > 3:
                                language = parts[1].strip()
                                if language.lower() == "csv":
                                    continue  # Skip CSV files
                                try:
                                    code_lines = int(parts[3].replace(",", "").strip())
                                    if language in language_data:
                                        language_data[language] += code_lines
                                    lines_of_code += code_lines
                                except ValueError:
                                    print(f"Skipping line due to ValueError: {line}")
                    print(
                        f"Date: {creation_date}, JavaScript: {language_data['JavaScript']}, CSS: {language_data['CSS']}, HTML: {language_data['HTML']}, Python: {language_data['Python']}"
                    )
                    data.append(
                        (
                            creation_date,
                            lines_of_code,
                            language_data["JavaScript"],
                            language_data["CSS"],
                            language_data["HTML"],
                            language_data["Python"],
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
        ],
    )
    df = pd.concat([df, new_data], ignore_index=True)

    # Save to Excel
    df.to_excel(output_file, index=False)

    # Print the total amount of code for each language
    total_js = df["JavaScript"].sum()
    total_css = df["CSS"].sum()
    total_html = df["HTML"].sum()
    total_python = df["Python"].sum()
    print(
        f"Total JavaScript: {total_js}, Total CSS: {total_css}, Total HTML: {total_html}, Total Python: {total_python}"
    )

    return df


def parse_date(date_str):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def plot_data(df):
    # Fill any missing values with zeros
    df = df.fillna(0)

    # Convert the "Date" column to datetime using the custom parse_date function
    df["Date"] = df["Date"].apply(parse_date)

    # Sort the DataFrame by date
    df = df.sort_values("Date")

    # Remove duplicate dates
    df = df.drop_duplicates(subset="Date")

    # Create a plot with specified figure size and background color
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor("#FEF1E5")  # Set the figure background color
    ax.set_facecolor("#FEF1E5")  # Set the axes background color

    # Interpolate for smooth lines
    dates = mpl.dates.date2num(df["Date"])  # Convert dates to matplotlib format
    x_smooth = np.linspace(
        dates.min(), dates.max(), 300
    )  # Generate more points for a smooth line

    def smooth_data(column):
        spline = make_interp_spline(
            dates, df[column], k=1
        )  # Cubic spline interpolation
        return spline(x_smooth)

    # Plot the smoothed lines for each language with transparency
    ax.plot(
        x_smooth,
        smooth_data("JavaScript"),
        label="JavaScript",
        color="blue",
        linewidth=3,
        alpha=0.7,
    )
    ax.plot(
        x_smooth,
        smooth_data("CSS"),
        label="CSS",
        color="orange",
        linewidth=3,
        alpha=0.7,
    )
    ax.plot(
        x_smooth,
        smooth_data("HTML"),
        label="HTML",
        color="green",
        linewidth=3,
        alpha=0.7,
    )
    ax.plot(
        x_smooth,
        smooth_data("Python"),
        label="Python",
        color="red",
        linewidth=3,
        alpha=1,
    )

    # Plot the sum of all code
    sum_of_all_code = df["JavaScript"] + df["CSS"] + df["HTML"] + df["Python"]
    sum_of_all_code_smooth = make_interp_spline(dates, sum_of_all_code, k=1)(x_smooth)
    ax.plot(
        x_smooth,
        sum_of_all_code_smooth,
        label="Sum of all code",
        color="black",
        linewidth=3,
        linestyle="dotted",
        alpha=1,
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

    # Set gridlines on the y-axis with a soft grey color and interval of 500
    ax.grid(axis="y", color="lightgrey", linestyle="--", linewidth=0.7)
    ax.set_yticks(
        range(
            0,
            int(df[["JavaScript", "CSS", "HTML", "Python"]].sum(axis=1).max() + 1000)
            + 1000,
            1000,
        )
    )

    # Set color for y-axis tick labels
    ax.tick_params(axis="y", colors="#757575")

    # Format the x-axis to show dates
    locator = AutoDateLocator()
    formatter = DateFormatter("%Y-%m-%d")
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)

    # Rotate x-axis labels for clarity and set their color
    plt.xticks(rotation=45, color="#757575")

    # Display the legend without border
    legend = ax.legend(frameon=False, fontsize=12, loc="lower right")
    for text in legend.get_texts():
        text.set_color("#757575")
    date = datetime.now().strftime("%Y-%m-%d-%H-%M")
    ax.set_ylim(2000, sum_of_all_code.max() + 1000)
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
