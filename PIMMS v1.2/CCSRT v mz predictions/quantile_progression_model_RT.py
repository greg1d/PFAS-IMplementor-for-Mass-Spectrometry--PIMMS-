import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from patsy import dmatrix
from statsmodels.regression.quantile_regression import QuantReg

# Load and prepare data
file_path = r"PIMMS v1.2\CCSRT v mz predictions\Library Data for model building.csv"
df = pd.read_csv(file_path)
df = df[["PrecursorMz", "PrecursorRT"]].dropna()
df["log_mz"] = np.log(df["PrecursorMz"])

quantiles = [0.05, 0.5, 0.95]  # Use 5th and 95th instead

# Define models
models = {
    "Linear": dmatrix("PrecursorMz", df, return_type="dataframe"),
    "Logarithmic": dmatrix("log_mz", df, return_type="dataframe"),
    "Spline": dmatrix(
        "bs(log_mz, df=3, include_intercept=False)", df, return_type="dataframe"
    ),
}


# Loss function
def pinball_loss(y, y_pred, q):
    delta = y - y_pred
    return np.mean(np.maximum(q * delta, (q - 1) * delta))


# Plot setup
fig, axes = plt.subplots(1, 3, figsize=(7, 5), sharey=True)

for i, (ax, (label, X)) in enumerate(zip(axes, models.items())):
    preds = {}
    for q in quantiles:
        model = QuantReg(df["PrecursorRT"], X)
        res = model.fit(q=q)
        preds[q] = res.predict(X)

    # Sort for smooth plotting
    sort_idx = df["PrecursorMz"].argsort()
    x_sorted = df["PrecursorMz"].values[sort_idx]
    q5_sorted = preds[0.05].values[sort_idx]
    q50_sorted = preds[0.5].values[sort_idx]
    q95_sorted = preds[0.95].values[sort_idx]

    pin5 = pinball_loss(df["PrecursorRT"], preds[0.05], 0.05)
    pin50 = pinball_loss(df["PrecursorRT"], preds[0.5], 0.5)
    pin95 = pinball_loss(df["PrecursorRT"], preds[0.95], 0.95)
    coverage = (
        (df["PrecursorRT"] >= preds[0.05]) & (df["PrecursorRT"] <= preds[0.95])
    ).mean()
    interval_width = (preds[0.95] - preds[0.05]).mean()

    # Plot data and quantile lines
    ax.scatter(
        df["PrecursorMz"],
        df["PrecursorRT"],
        color="gray",
        alpha=0.3,
        s=15,
        label="Observed",
    )
    ax.scatter(
        df["PrecursorMz"],
        df["PrecursorRT"],
        color="gray",
        alpha=0.3,
        s=15,
        label="Observed",
    )
    ax.plot(x_sorted, q50_sorted, color="black", label="Median (50%)")
    ax.plot(x_sorted, q5_sorted, linestyle="--", color="red", label="5th Percentile")
    ax.plot(x_sorted, q95_sorted, linestyle="--", color="red", label="95th Percentile")
    ax.fill_between(x_sorted, q5_sorted, q95_sorted, color="red", alpha=0.1)

    # Add metric box
    metrics_text = (
        f"Pinball Loss:\n"
        f"  5% = {pin5:.3f}\n"
        f"  50% = {pin50:.3f}\n"
        f"  95% = {pin95:.3f}\n"
        f"Coverage: {coverage:.2%}\n"
        f"Width: {interval_width:.2f}"
    )
    ax.text(
        0.97,
        0.03,
        metrics_text,
        transform=ax.transAxes,
        fontsize=8,
        fontfamily="Arial",
        fontweight="bold",
        verticalalignment="bottom",
        horizontalalignment="right",
        bbox=dict(
            boxstyle="round,pad=0.4", facecolor="white", edgecolor="gray", alpha=0.7
        ),
    )

    ax.set_title(label, fontsize=10, fontweight="bold", fontfamily="Arial")
    ax.set_xlabel(r"$\mathbfit{m/z}$", fontsize=10, fontfamily="Arial")

    ax.set_ylim(0, 20)
    ax.grid(True)

    ax.tick_params(axis="both", labelsize=9)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontname("Arial")
        label.set_fontweight("bold")

    # Add y-axis label only to the first plot
    if i == 0:
        ax.set_ylabel("CCS (Å²)", fontsize=10, fontweight="bold", fontfamily="Arial")

handles, labels = axes[1].get_legend_handles_labels()
unique = dict(zip(labels, handles))  # Remove duplicates by label
legend = axes[1].legend(
    unique.values(),
    unique.keys(),
    loc="upper left",
    fontsize=8,
    frameon=True,
    fancybox=True,
    facecolor="white",
    edgecolor="gray",
    framealpha=0.7,
)

# Manually style legend text
for text in legend.get_texts():
    text.set_fontweight("bold")
    text.set_fontfamily("Arial")
plt.tight_layout(rect=[0, 0, 1, 0.93])
plt.show()
