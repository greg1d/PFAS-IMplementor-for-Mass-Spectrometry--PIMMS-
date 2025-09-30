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
                df["PrecursorRT"].values[train_index],
                df["PrecursorRT"].values[test_index],
            )

            preds = {}
            for q in quantiles:
                model = QuantReg(y_train, X_train)
                res = model.fit(q=q)
                preds[q] = res.predict(X_test)

            # Calculate Pinball Loss for each quantile
            pin5 = pinball_loss(y_test, preds[0.10], 0.10)
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


def run_RT_regression_analysis(library_file, column_mappings):
    """
    Performs quantile regression on RT vs. m/z using dynamic column mappings.
    """
    # --- 1. Get column names from the mapping dictionary using the standard keys ---
    mz_col_name = column_mappings.get("m/z")
    rt_col_name = column_mappings.get("RT")

    # --- 2. Validate that the required column names were provided ---
    if not mz_col_name or not rt_col_name:
        raise ValueError("Column mappings for 'm/z' and 'RT' must be provided.")

    # Load data
    df = pd.read_csv(library_file)

    # --- 3. Check if the specified columns exist in the DataFrame ---
    required_cols = [mz_col_name, rt_col_name]
    if not all(col in df.columns for col in required_cols):
        missing_cols = [col for col in required_cols if col not in df.columns]
        raise KeyError(
            f"The following specified columns are not in the library file: {missing_cols}"
        )

    # --- 4. Use the dynamic column names for processing ---
    df = df[required_cols].dropna()
    df["log_mz"] = np.log(df[mz_col_name])

    # --- 5. Fit the quantile regression models ---
    # We will use a simple logarithmic model for RT as well.
    X = dmatrix("1 + log_mz", df, return_type="dataframe")
    model_5 = QuantReg(df[rt_col_name], X).fit(q=0.05)  # Using 5th percentile
    model_95 = QuantReg(df[rt_col_name], X).fit(q=0.95)  # Using 95th percentile

    coef_5 = model_5.params
    coef_95 = model_95.params

    # Optional: print equation for verification
    print("Adjusted RT regression equations:")
    print(
        f"5th percentile: y = {coef_5['log_mz']:.4f} * log(m/z) + {coef_5['Intercept']:.4f}"
    )
    print(
        f"95th percentile: y = {coef_95['log_mz']:.4f} * log(m/z) + {coef_95['Intercept']:.4f}"
    )

    # Return the coefficients for the upper and lower bounds
    return {
        "q05_intercept": coef_5["Intercept"],
        "q05_slope": coef_5["log_mz"],
        "q95_intercept": coef_95["Intercept"],
        "q95_slope": coef_95["log_mz"],
    }
