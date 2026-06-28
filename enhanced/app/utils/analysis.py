import pandas as pd
import numpy as np


def run_analysis(df, plan):
    operation = plan.get("operation", "group_by_summary")
    group_by = plan.get("group_by", [])
    target = plan.get("target_column")
    metric = plan.get("metric", "sum")
    x_col = plan.get("x_column")
    y_col = plan.get("y_column")

    # ── Original operation (preserved) ───────────────────────────────────────
    if operation == "group_by_summary":
        if group_by and target and target in df.columns:
            valid_group = [c for c in group_by if c in df.columns]
            if valid_group:
                if metric == "sum":
                    return df.groupby(valid_group)[target].sum().reset_index()
                elif metric == "mean":
                    return df.groupby(valid_group)[target].mean().reset_index()
                elif metric == "count":
                    return df.groupby(valid_group)[target].count().reset_index()
        return df

    # ── Correlation analysis ──────────────────────────────────────────────────
    elif operation == "correlation":
        num_df = df.select_dtypes(include="number")
        if x_col and y_col and x_col in df.columns and y_col in df.columns:
            return df[[x_col, y_col]].dropna()
        return num_df

    # ── Outlier detection (IQR method) ────────────────────────────────────────
    elif operation == "outlier_detection":
        if target and target in df.columns:
            col = df[target].dropna()
            q1, q3 = col.quantile(0.25), col.quantile(0.75)
            iqr = q3 - q1
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            outliers = df[(df[target] < lower) | (df[target] > upper)].copy()
            outliers["outlier_type"] = outliers[target].apply(
                lambda v: "High" if v > upper else "Low"
            )
            outliers["lower_bound"] = round(lower, 2)
            outliers["upper_bound"] = round(upper, 2)
            return outliers if not outliers.empty else df[[target]].describe().reset_index()
        return df

    # ── Trend analysis ────────────────────────────────────────────────────────
    elif operation == "trend_analysis":
        if group_by and target and target in df.columns:
            valid_group = [c for c in group_by if c in df.columns]
            if valid_group:
                result = df.groupby(valid_group)[target].sum().reset_index()
                result = result.sort_values(valid_group[0])
                if len(result) > 1:
                    vals = result[target].values
                    result["rolling_avg"] = (
                        pd.Series(vals).rolling(window=min(3, len(vals)), min_periods=1).mean().values
                    )
                return result
        return df

    # ── Distribution ──────────────────────────────────────────────────────────
    elif operation == "distribution":
        if target and target in df.columns:
            col = df[target].dropna()
            stats = {
                "mean": round(col.mean(), 2),
                "median": round(col.median(), 2),
                "std": round(col.std(), 2),
                "min": round(col.min(), 2),
                "max": round(col.max(), 2),
                "skewness": round(col.skew(), 2),
                "kurtosis": round(col.kurt(), 2),
                "q25": round(col.quantile(0.25), 2),
                "q75": round(col.quantile(0.75), 2),
            }
            return pd.DataFrame([stats])
        return df

    # ── Heatmap (correlation matrix) ──────────────────────────────────────────
    elif operation == "heatmap":
        num_df = df.select_dtypes(include="number")
        if not num_df.empty:
            return num_df.corr().round(2)
        return df

    return df
