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
    df, quantiles=[0.10, 0.5, 0.90], n_splits=5, shuffle=True, random_state=42
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
            pin5 = pinball_loss(y_test, preds[0.10], 0.01)
            pin50 = pinball_loss(y_test, preds[0.5], 0.5)
            pin95 = pinball_loss(y_test, preds[0.90], 0.90)
            pinball_losses_5.append(pin5)
            pinball_losses_50.append(pin50)
            pinball_losses_95.append(pin95)

            # Coverage and Width
            coverage = ((y_test >= preds[0.10]) & (y_test <= preds[0.90])).mean()
            coverage_list.append(coverage)
            interval_width = (preds[0.90] - preds[0.10]).mean()
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


def run_CCS_regression_analysis(library_file):
    # Load data
    df = pd.read_csv(library_file)
    df = df[["PrecursorMz", "PrecursorCCS"]].dropna()
    df["log_mz"] = np.log(df["PrecursorMz"])

    # Run KFold cross-validation
    cross_val_results = run_kfold_cv(df)

    # Logarithmic Model Equations (5th and 95th Percentiles)
    X = dmatrix("1 + log_mz", df, return_type="dataframe")
    model_5 = QuantReg(df["PrecursorCCS"], X).fit(q=0.10)
    model_95 = QuantReg(df["PrecursorCCS"], X).fit(q=0.90)

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


if __name__ == "__main__":
    # File path for the dataset
    library_file = (
        r"PIMMS v1.2\CCSRT v mz predictions\Library Data for model building.csv"
    )
    # Run the analysis
    run_analysis(library_file)
