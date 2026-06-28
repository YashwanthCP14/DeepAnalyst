import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go


def generate_chart(df, plan):
    if df is None or df.empty:
        return None

    operation = plan.get("operation", "group_by_summary")
    group_by = plan.get("group_by", [])
    target = plan.get("target_column")
    chart_type = plan.get("chart_type", "bar")
    x_col = plan.get("x_column")
    y_col = plan.get("y_column")

    # ── Heatmap for correlation matrix ───────────────────────────────────────
    if operation == "heatmap":
        try:
            fig = px.imshow(
                df,
                text_auto=".2f",
                color_continuous_scale="RdBu_r",
                title="Correlation Matrix",
                aspect="auto",
            )
            return fig
        except Exception:
            pass

    # ── Scatter for correlation / x-y analysis ───────────────────────────────
    if operation == "correlation" and x_col and y_col:
        cols = df.columns.tolist()
        if x_col in cols and y_col in cols:
            return px.scatter(
                df, x=x_col, y=y_col,
                trendline="ols",
                title=f"{x_col} vs {y_col}",
                labels={x_col: x_col, y_col: y_col},
            )

    # ── Outlier detection chart ───────────────────────────────────────────────
    if operation == "outlier_detection" and target and target in df.columns:
        fig = px.box(df, y=target, title=f"Outlier Detection — {target}", points="all")
        return fig

    # ── Distribution histogram with stats overlay ─────────────────────────────
    if operation == "distribution" and target:
        # Return a bar chart of the stats dataframe
        if set(df.columns).issuperset({"mean", "median", "std"}):
            melted = df.melt(var_name="Statistic", value_name="Value")
            return px.bar(melted, x="Statistic", y="Value", title=f"Distribution Stats — {target}")

    # ── Trend with rolling average ────────────────────────────────────────────
    if operation == "trend_analysis" and group_by and target:
        x = group_by[0]
        if x in df.columns and target in df.columns:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df[x], y=df[target], name=target, opacity=0.6))
            if "rolling_avg" in df.columns:
                fig.add_trace(go.Scatter(
                    x=df[x], y=df["rolling_avg"],
                    name="Rolling Avg", line=dict(color="red", width=2)
                ))
            fig.update_layout(title=f"Trend — {target}", barmode="overlay")
            return fig

    # ── Original chart logic (preserved exactly) ─────────────────────────────
    if group_by and target and target in df.columns:
        x = group_by[0]
        if x not in df.columns:
            return None

        if chart_type == "line":
            return px.line(df, x=x, y=target)
        elif chart_type == "pie":
            return px.pie(df, names=x, values=target)
        elif chart_type == "scatter" and x_col and y_col:
            return px.scatter(df, x=x_col, y=y_col)
        elif chart_type == "histogram" and target:
            return px.histogram(df, x=target)
        elif chart_type == "box" and target:
            return px.box(df, y=target)
        return px.bar(df, x=x, y=target)

    return None
