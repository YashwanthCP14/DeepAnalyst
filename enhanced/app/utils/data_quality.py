import pandas as pd
import numpy as np


def get_data_quality_report(df):
    """
    Returns a DataFrame with per-column quality metrics:
    data type, missing count, fill rate, unique values, duplicates, and sample values.
    """
    report_rows = []

    total_rows = len(df)
    duplicate_rows = df.duplicated().sum()

    for col in df.columns:
        series = df[col]
        missing = series.isnull().sum()
        fill_rate = round((1 - missing / total_rows) * 100, 1) if total_rows > 0 else 0
        unique_vals = series.nunique(dropna=True)
        dtype = str(series.dtype)

        issues = []
        if missing > 0:
            issues.append(f"{missing} missing")
        if dtype == "object" and unique_vals == total_rows:
            issues.append("possible ID column")
        if dtype in ("float64", "int64") and series.min() < 0:
            issues.append("has negatives")

        report_rows.append({
            "Column": col,
            "Type": dtype,
            "Missing": missing,
            "Fill Rate (%)": fill_rate,
            "Unique Values": unique_vals,
            "Issues": ", ".join(issues) if issues else "OK",
        })

    summary = {
        "total_rows": total_rows,
        "total_columns": len(df.columns),
        "duplicate_rows": int(duplicate_rows),
        "complete_rows": int((~df.isnull().any(axis=1)).sum()),
        "columns_with_missing": int((df.isnull().sum() > 0).sum()),
    }

    return pd.DataFrame(report_rows), summary
