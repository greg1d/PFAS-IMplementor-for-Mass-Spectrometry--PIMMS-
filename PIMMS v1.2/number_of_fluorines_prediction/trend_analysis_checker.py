import pandas as pd
import re
import numpy as np
import plotly.graph_objects as go
from statsmodels.regression.quantile_regression import QuantReg
import statsmodels.api as sm

# Load data
file_path = r"PIMMS v1.2\CCSRT v mz predictions\Library Data for model building.csv"
df = pd.read_csv(file_path)

# CCS defect
df["Expected_CCS"] = df["PrecursorMz"] * 0.19 + 110.28
df["CCS_defect"] = -df["PrecursorCCS"] + df["Expected_CCS"]  # can be negative


# Extract fluorine count
def extract_fluorine_count(formula):
    match = re.search(r"F(\d*)", str(formula))
    if not match:
        return 0
    return int(match.group(1)) if match.group(1) else 1


df["Number_of_fluorines"] = df["PrecursorFormula"].apply(extract_fluorine_count)

# Drop missing values and rows with non-positive CCS defect (can't log those)
subset = (
    df[["PrecursorName", "Number_of_fluorines", "CCS_defect", "PrecursorFormula"]]
    .dropna()
    .copy()
)
subset = subset[subset["CCS_defect"] > 0].copy()
subset["log_CCS_defect"] = np.log1p(subset["CCS_defect"])  # safe log

# Fit quantile regression: y = fluorines, x = log(CCS defect)
X = sm.add_constant(subset["log_CCS_defect"])
y = subset["Number_of_fluorines"]
model = QuantReg(y, X)
fit = model.fit(q=0.5)

# Predict and compute residuals
y_pred = fit.predict(X)
residuals = y - y_pred
std_dev = residuals.std()

# Identify outliers
outlier_mask = (y > y_pred + std_dev) | (y < y_pred - std_dev)
outliers = subset[outlier_mask]
non_outliers = subset[~outlier_mask]

# Prediction band
log_ccs_grid = np.linspace(
    subset["log_CCS_defect"].min(), subset["log_CCS_defect"].max(), 200
)
X_pred = sm.add_constant(log_ccs_grid)
y_grid_pred = fit.predict(X_pred)
upper = y_grid_pred + std_dev
lower = y_grid_pred - std_dev

# Plot setup
fig = go.Figure()

# Shaded ±1 SD band
fig.add_trace(
    go.Scatter(
        x=np.concatenate([log_ccs_grid, log_ccs_grid[::-1]]),
        y=np.concatenate([upper, lower[::-1]]),
        fill="toself",
        fillcolor="rgba(0,100,200,0.2)",
        line=dict(color="rgba(255,255,255,0)"),
        hoverinfo="skip",
        name="±1 SD",
        showlegend=True,
    )
)

# Median regression line
fig.add_trace(
    go.Scatter(
        x=log_ccs_grid,
        y=y_grid_pred,
        mode="lines",
        name="Median Trend",
        line=dict(color="blue", width=2),
        hoverinfo="skip",
    )
)

# Plot inliers
fig.add_trace(
    go.Scatter(
        x=non_outliers["log_CCS_defect"],
        y=non_outliers["Number_of_fluorines"],
        mode="markers",
        name="Inliers",
        text=non_outliers["PrecursorName"],
        marker=dict(color="lightgray", size=6, opacity=0.5),
        hovertemplate="<b>%{text}</b><br>log(CCS Defect): %{x:.2f}<br>Fluorines: %{y}<extra></extra>",
    )
)

# Plot outliers
fig.add_trace(
    go.Scatter(
        x=outliers["log_CCS_defect"],
        y=outliers["Number_of_fluorines"],
        mode="markers",
        name="Outliers",
        text=outliers["PrecursorName"],
        marker=dict(color="red", size=8, symbol="circle-open-dot"),
        hovertemplate="<b>%{text}</b><br>log(CCS Defect): %{x:.2f}<br>Fluorines: %{y}<extra></extra>",
    )
)

# Layout
fig.update_layout(
    title="Fluorine Count vs. log(CCS Defect + 1) with ±1 SD Band and Outliers",
    xaxis_title="log(CCS Defect + 1)",
    yaxis_title="Number of Fluorines",
    template="plotly_white",
    width=950,
    height=600,
)

fig.show()

# Print outlier formulas
print("\n=== Outlier Molecular Formulas ===")
for _, row in outliers.iterrows():
    print(f"{row['PrecursorName']}: {row['PrecursorFormula']}")
