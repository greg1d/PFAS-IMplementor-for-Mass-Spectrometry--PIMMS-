import numpy as np
import matplotlib.pyplot as plt

# === Define peaks ===
# Format: (mass_center, max_height)
observed_peaks = [
    (530.89504, 100),
    (531.89504, 9.61),
    (532.89504, 37.71),
    (533.89504, 3.56),
]

# === Define theoretical distributions ===
# Each entry is a list of (mass_center, max_height)
theoretical_distributions = [
    [
        (530.89504, 100.00),
        (531.89504, 0),
        (532.89504, 97.28),
        (533.89504, 0),
    ],  # Theory 1
    [
        (530.89504, 100.00),
        (531.89504, 0),
        (532.89504, 31.96),
        (533.89504, 0),
    ],  # Theory 2
    [
        (530.89504, 100.00),
        (531.89504, 8.65),
        (532.89504, 0.33),
        (533.89504, 0.01),
    ],  # Theory 2
]

# === x-axis range ===
x_min = min(p[0] for p in observed_peaks) - 1
x_max = max(p[0] for p in observed_peaks) + 1
x = np.linspace(x_min, x_max, 2000)


# === Gaussian function using FWHM from mass/20000 ===
def gaussian_fwhm(x, center, height):
    fwhm = center / 20000
    sigma = fwhm / 2.3548
    return height * np.exp(-((x - center) ** 2) / (2 * sigma**2))


# === Compute observed curve ===
y_observed = np.zeros_like(x)
for mass, height in observed_peaks:
    y_observed += gaussian_fwhm(x, mass, height)

# === Plot observed ===
fig, ax = plt.subplots(figsize=(7, 4.326))
ax.plot(x, y_observed, color="black", linewidth=1.5, label="Observed")

# === Plot theoretical curves with vertical spacing ===
vertical_spacing = 120  # Adjust for visual clarity
for i, theory in enumerate(theoretical_distributions):
    y_theory = np.zeros_like(x)
    for mass, height in theory:
        y_theory += gaussian_fwhm(x, mass, height)
    offset = vertical_spacing * (i + 1)
    ax.plot(
        x,
        y_theory + offset,
        linestyle="--",
        linewidth=1.2,
        label=f"Theoretical {i + 1}",
        color="gray",
    )

# === Axis labels ===
ax.set_xlabel(r"$\mathbfit{m/z}$", fontsize=10, fontfamily="Arial", fontweight="bold")
label_positions = [50, 170, 290, 410]
labels = [
    "Experimental",
    "Theoretical 1 \n(Br-containing)",
    "Theoretical 2 \n(Cl-containing)",
    "Theoretical 3 \n(C, F only)",
]

for y, text in zip(label_positions, labels):
    ax.text(
        x=x_max - 1,  # slightly left of the x-axis start
        y=y,
        s=text,
        va="center",
        ha="right",
        fontsize=9,
        fontfamily="Arial",
        fontweight="bold",
    )
# === Custom y-axis tick marks and labels
custom_ticks = [0, 100, 120, 220, 240, 340, 360, 460]
custom_labels = ["0", "100", "0", "100", "0", "100", "0", "100"]
ax.set_yticks(custom_ticks)
ax.set_yticklabels(custom_labels, fontfamily="Arial", fontsize=9, weight="bold")
# === Tick formatting ===
ax.tick_params(axis="both", which="major", labelsize=9, pad=6)
for label in ax.get_xticklabels() + ax.get_yticklabels():
    label.set_fontname("Arial")
    label.set_weight("bold")

# === Spines cleanup ===
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_linewidth(2)
ax.spines["bottom"].set_linewidth(2)
ax.set_xlim(530, 534)
# === Add legend ===

plt.tight_layout()
plt.show()
