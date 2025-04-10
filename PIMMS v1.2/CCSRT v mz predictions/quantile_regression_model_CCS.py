import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from patsy import dmatrix
from sklearn.model_selection import KFold
from statsmodels.regression.quantile_regression import QuantReg

# Define models globally
models = {
    "Linear": "PrecursorMz",
    "Logarithmic": "log_mz",
    "Spline": "bs(log_mz, df=3, include_intercept=False)",
}


# Loss function
def pinball_loss(y, y_pred, q):
    delta = y - y_pred
    return np.mean(np.maximum(q * delta, (q - 1) * delta))


# KFold Cross-validation setup
def run_kfold_cv(
    df, quantiles=[0.05, 0.5, 0.95], n_splits=5, shuffle=True, random_state=42
):
    # Initialize KFold and result storage
    kf = KFold(n_splits=n_splits, shuffle=shuffle, random_state=random_state)
    cross_val_results = {}

    # Run KFold cross-validation for each model
    for model_name, formula in models.items():
        # Convert the design matrix to NumPy array for compatibility with KFold
        X = dmatrix(formula, df, return_type="dataframe")
        X_array = np.array(X)

        # Store metrics for each fold
        pinball_losses_5 = []
        pinball_losses_50 = []
        pinball_losses_95 = []
        coverage_list = []
        width_list = []

        # Perform k-fold cross-validation
        for train_index, test_index in kf.split(df):
            X_train, X_test = X_array[train_index], X_array[test_index]
            y_train, y_test = (
                df["PrecursorCCS"].values[train_index],
                df["PrecursorCCS"].values[test_index],
            )

            preds = {}
            for q in quantiles:
                model = QuantReg(y_train, X_train)
                res = model.fit(q=q)
                preds[q] = res.predict(X_test)

            # Calculate Pinball Loss for each quantile
            pin5 = pinball_loss(y_test, preds[0.05], 0.01)
            pin50 = pinball_loss(y_test, preds[0.5], 0.5)
            pin95 = pinball_loss(y_test, preds[0.95], 0.99)
            pinball_losses_5.append(pin5)
            pinball_losses_50.append(pin50)
            pinball_losses_95.append(pin95)

            # Coverage and Width
            coverage = ((y_test >= preds[0.05]) & (y_test <= preds[0.95])).mean()
            coverage_list.append(coverage)
            interval_width = (preds[0.95] - preds[0.05]).mean()
            width_list.append(interval_width)

        # Store the results for each model
        cross_val_results[model_name] = {
            "Pinball Loss 5%": np.mean(pinball_losses_5),
            "Pinball Loss 50%": np.mean(pinball_losses_50),
            "Pinball Loss 95%": np.mean(pinball_losses_95),
            "Coverage": np.mean(coverage_list),
            "Width": np.mean(width_list),
        }

    # Return the cross-validation results
    return cross_val_results


# Visualization function
def plot_results(df, cross_val_results, quantiles=[0.05, 0.5, 0.95]):
    fig, axes = plt.subplots(1, 3, figsize=(7, 5), sharey=True)

    for i, (ax, (label, formula)) in enumerate(zip(axes, models.items())):
        preds = {}
        X = dmatrix(formula, df, return_type="dataframe")
        for q in quantiles:
            model = QuantReg(df["PrecursorCCS"], X)
            res = model.fit(q=q)
            bias_correction = -3.0  # Shift down by 5 CCS units, adjust as needed
            preds[q] = res.predict(X) + bias_correction
        # Sort for smooth plotting
        sort_idx = df["PrecursorMz"].argsort()
        x_sorted = df["PrecursorMz"].values[sort_idx]
        q5_sorted = preds[0.05].values[sort_idx]
        q50_sorted = preds[0.5].values[sort_idx]
        q95_sorted = preds[0.95].values[sort_idx]

        # Fetch cross-validation results for the current model
        pin5 = cross_val_results[label]["Pinball Loss 5%"]
        pin50 = cross_val_results[label]["Pinball Loss 50%"]
        pin95 = cross_val_results[label]["Pinball Loss 95%"]
        coverage = cross_val_results[label]["Coverage"]
        interval_width = cross_val_results[label]["Width"]

        # Determine outliers based on bounds
        inliers_mask = (df["PrecursorCCS"] >= preds[0.05]) & (
            df["PrecursorCCS"] <= preds[0.95]
        )
        outliers_mask = ~inliers_mask

        # Print PrecursorNames of outliers if column exists
        if "PrecursorName" in df.columns:
            print(f"\nOutliers for {label} model:")
            print(df.loc[outliers_mask, "PrecursorName"].to_string(index=False))
        else:
            print(f"\nNote: 'PrecursorName' column not found for {label} model.")

        inliers = df[inliers_mask]
        outliers = df[outliers_mask]
        outliers_mask = ~inliers_mask

        # Print PrecursorNames of outliers if column exists

        inliers = df[inliers_mask]
        outliers = df[outliers_mask]

        inliers = df[inliers_mask]
        outliers = df[~inliers_mask]

        # Plot inliers in gray
        ax.scatter(
            inliers["PrecursorMz"],
            inliers["PrecursorCCS"],
            color="gray",
            alpha=0.3,
            s=15,
            label="Within Bounds",
        )

        # Plot outliers in red
        ax.scatter(
            outliers["PrecursorMz"],
            outliers["PrecursorCCS"],
            color="red",
            alpha=0.5,
            edgecolors="k",
            linewidths=0.4,
            s=25,
            label="Outside Bounds",
        )

        ax.plot(x_sorted, q50_sorted, color="black", label="Median (50%)")
        ax.plot(
            x_sorted, q5_sorted, linestyle="--", color="red", label="5th Percentile"
        )
        ax.plot(
            x_sorted, q95_sorted, linestyle="--", color="red", label="95th Percentile"
        )
        ax.fill_between(x_sorted, q5_sorted, q95_sorted, color="red", alpha=0.1)

        # Add metric box with KFold results
        metrics_text = (
            f"Pinball Loss:\n"
            f"5% = {pin5:.3f}\n"
            f"50% = {pin50:.3f}\n"
            f"95% = {pin95:.3f}\n"
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
        ax.set_ylim(0, 300)
        ax.grid(True)
        ax.tick_params(axis="both", labelsize=9)
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontname("Arial")
            label.set_fontweight("bold")

        if i == 0:
            ax.set_ylabel(
                "CCS (Å²)", fontsize=10, fontweight="bold", fontfamily="Arial"
            )

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


def run_CCS_regression_analysis(library_file):
    # Load data
    df = pd.read_csv(library_file)
    df = df[["PrecursorMz", "PrecursorCCS"]].dropna()
    df["log_mz"] = np.log(df["PrecursorMz"])

    # Run KFold cross-validation
    cross_val_results = run_kfold_cv(df)

    # Logarithmic Model Equations (5th and 95th Percentiles)
    X = dmatrix("1 + log_mz", df, return_type="dataframe")
    model_5 = QuantReg(df["PrecursorCCS"], X).fit(q=0.05)
    model_95 = QuantReg(df["PrecursorCCS"], X).fit(q=0.95)

    coef_5 = model_5.params
    coef_95 = model_95.params

    # === Bias correction (e.g., shift curve downward) ===
    bias_correction = -5.0  # adjust as needed

    # Apply correction to intercepts
    q05_intercept_corrected = coef_5["Intercept"] + bias_correction
    q95_intercept_corrected = coef_95["Intercept"] + bias_correction

    # Optional: print equation for verification
    print("Adjusted CCS regression equations:")
    print(
        f"5th percentile: y = {coef_5['log_mz']:.4f} * log(m/z) + {q05_intercept_corrected:.4f}"
    )
    print(
        f"95th percentile: y = {coef_95['log_mz']:.4f} * log(m/z) + {q95_intercept_corrected:.4f}"
    )

    # Plot the results
    plot_results(df, cross_val_results)

    # Return bias-adjusted coefficients
    return {
        "q05_intercept": q05_intercept_corrected,
        "q05_slope": coef_5["log_mz"],
        "q95_intercept": q95_intercept_corrected,
        "q95_slope": coef_95["log_mz"],
    }


def run_analysis(library_file):
    # Load data
    df = pd.read_csv(library_file)
    df = df[["PrecursorName", "PrecursorMz", "PrecursorCCS"]].dropna()
    df["log_mz"] = np.log(df["PrecursorMz"])

    # Run KFold cross-validation
    cross_val_results = run_kfold_cv(df)

    # Print the results
    for model_name, metrics in cross_val_results.items():
        print(f"\n{model_name} Model Cross-Validation Results:")
        for metric, value in metrics.items():
            print(f"  {metric}: {value:.3f}")

    # Plot the results
    plot_results(df, cross_val_results)


if __name__ == "__main__":
    # File path for the dataset
    library_file = (
        r"PIMMS v1.2\CCSRT v mz predictions\Library Data for model building.csv"
    )

    # Run the analysis
    run_analysis(library_file)
