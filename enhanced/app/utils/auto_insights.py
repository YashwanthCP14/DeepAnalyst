import pandas as pd
import numpy as np


def generate_auto_insights(df, target_col):
    insights = []

    if target_col not in df.columns:
        return insights

    col = df[target_col].dropna()

    # ── Original insights (preserved exactly) ────────────────────────────────
    insights.append(f"Total: {col.sum():,.2f}")
    insights.append(f"Average: {col.mean():,.2f}")
    insights.append(f"Max: {col.max():,.2f}")
    insights.append(f"Min: {col.min():,.2f}")

    if col.std() > 0:
        insights.append("Data shows variability")

    # ── New: Top and bottom performers ───────────────────────────────────────
    if len(df) > 1:
        top_row = df.loc[df[target_col].idxmax()]
        bot_row = df.loc[df[target_col].idxmin()]
        cat_cols = df.select_dtypes(exclude="number").columns.tolist()
        if cat_cols:
            label_col = cat_cols[0]
            insights.append(f"Top performer: {top_row[label_col]} ({col.max():,.2f})")
            insights.append(f"Lowest performer: {bot_row[label_col]} ({col.min():,.2f})")

    # ── New: Trend direction ──────────────────────────────────────────────────
    if len(col) >= 3:
        first_half = col.iloc[: len(col) // 2].mean()
        second_half = col.iloc[len(col) // 2 :].mean()
        if second_half > first_half * 1.05:
            insights.append("Trend: values are increasing over the dataset")
        elif second_half < first_half * 0.95:
            insights.append("Trend: values are decreasing over the dataset")
        else:
            insights.append("Trend: values are relatively stable")

    # ── New: Anomaly / outlier flag ───────────────────────────────────────────
    if len(col) >= 4:
        q1, q3 = col.quantile(0.25), col.quantile(0.75)
        iqr = q3 - q1
        n_outliers = ((col < q1 - 1.5 * iqr) | (col > q3 + 1.5 * iqr)).sum()
        if n_outliers > 0:
            insights.append(f"Anomaly alert: {n_outliers} outlier(s) detected in {target_col}")

    # ── New: Coefficient of variation (spread quality) ───────────────────────
    if col.mean() != 0:
        cv = (col.std() / col.mean()) * 100
        if cv > 50:
            insights.append(f"High variability detected (CV = {cv:.1f}%) - consider segmenting data")

    return insights
