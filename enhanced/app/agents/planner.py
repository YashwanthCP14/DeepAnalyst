import json
import re
from app.core.llm_client import generate_response


def extract_json(text):
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return None


def _closest_column(name: str, columns: list) -> str:
    """Return the closest real column name (case-insensitive substring match)."""
    name_lower = name.lower().replace(" ", "_")
    for c in columns:
        if c.lower() == name_lower:
            return c
    for c in columns:
        if name_lower in c.lower() or c.lower() in name_lower:
            return c
    return columns[0] if columns else name


def _parse_columns(schema_text: str):
    """Extract real column names and their types from schema text."""
    num_cols, cat_cols, all_cols = [], [], []
    for line in schema_text.splitlines():
        m = re.match(r"^([\S][\S ]*?)\s+\((.*?)\)\s*$", line.strip())
        if m:
            col = m.group(1).strip()
            dtype = m.group(2).strip()
            all_cols.append(col)
            if any(t in dtype for t in ["int", "float"]):
                num_cols.append(col)
            else:
                cat_cols.append(col)
    return all_cols, num_cols, cat_cols


def _detect_operation(question: str) -> str:
    q = question.lower()
    if any(w in q for w in ["correlat", "relationship between", "scatter", " vs ", "versus"]):
        return "correlation"
    if any(w in q for w in ["outlier", "anomal", "unusual", "extreme value", "spike"]):
        return "outlier_detection"
    if any(w in q for w in ["trend", "over time", "time series", "month", "year", "forecast", "growth"]):
        return "trend_analysis"
    if any(w in q for w in ["distribut", "spread", "histogram", "frequency"]):
        return "distribution"
    if any(w in q for w in ["heatmap", "heat map", "matrix"]):
        return "heatmap"
    return "group_by_summary"


def _build_fallback_plan(question: str, all_cols: list, num_cols: list, cat_cols: list) -> dict:
    """Build a working plan purely from the question and real column names."""
    q = question.lower()

    mentioned_num = [c for c in num_cols if c.lower() in q]
    mentioned_cat = [c for c in cat_cols if c.lower() in q]

    target = mentioned_num[0] if mentioned_num else (num_cols[0] if num_cols else all_cols[-1])
    group_by = [mentioned_cat[0]] if mentioned_cat else ([cat_cols[0]] if cat_cols else [all_cols[0]])

    operation = _detect_operation(question)

    metric = "sum"
    if any(w in q for w in ["average", "mean", "avg"]):
        metric = "mean"
    elif any(w in q for w in ["count", "how many"]):
        metric = "count"

    chart_type = "bar"
    if any(w in q for w in ["line", "trend", "over time", "month", "year"]):
        chart_type = "line"
    elif any(w in q for w in ["pie", "share", "proportion"]):
        chart_type = "pie"
    elif any(w in q for w in ["scatter", "correlat", " vs "]):
        chart_type = "scatter"
    elif any(w in q for w in ["heat", "matrix"]):
        chart_type = "heatmap"

    x_col = mentioned_num[0] if mentioned_num else (num_cols[0] if num_cols else all_cols[0])
    y_col = mentioned_num[1] if len(mentioned_num) > 1 else (num_cols[1] if len(num_cols) > 1 else target)

    return {
        "operation": operation,
        "group_by": group_by,
        "target_column": target,
        "x_column": x_col,
        "y_column": y_col,
        "metric": metric,
        "chart_type": chart_type,
        "need_chart": True,
    }


def call_planner(schema_text: str, question: str, history=None):
    history_text = ""
    if history:
        history_text = "\n".join(
            [f"{m['role']}: {m['content']}" for m in history[-5:]]
        )

    all_cols, num_cols, cat_cols = _parse_columns(schema_text)

    prompt = f"""
You are a data analyst.

Return ONLY valid JSON with no extra text.

{{
  "operation": "group_by_summary | correlation | outlier_detection | trend_analysis | distribution | heatmap",
  "group_by": ["column_name"],
  "target_column": "column_name",
  "x_column": "numeric_column",
  "y_column": "numeric_column",
  "metric": "sum | mean | count",
  "chart_type": "bar | line | pie | scatter | heatmap | histogram | box",
  "need_chart": true
}}

Rules:
- No explanation
- Only JSON
- Use EXACT column names from the dataset below
- For correlation/scatter: set x_column and y_column to numeric columns
- For trend: use a date/time column in group_by if available
- For outlier_detection: set target_column to the numeric column to inspect

Conversation:
{history_text}

Dataset:
{schema_text}

Question:
{question}
"""

    response = generate_response(prompt)
    plan = extract_json(response)

    if not plan:
        plan = _build_fallback_plan(question, all_cols, num_cols, cat_cols)
        return plan

    # Ensure operation field exists
    if "operation" not in plan:
        plan["operation"] = _detect_operation(question)

    # Fix any column name mismatches in LLM output
    if all_cols:
        if "target_column" in plan:
            plan["target_column"] = _closest_column(plan["target_column"], all_cols)
        if "group_by" in plan and isinstance(plan["group_by"], list):
            plan["group_by"] = [_closest_column(c, all_cols) for c in plan["group_by"]]
        if "x_column" in plan:
            plan["x_column"] = _closest_column(plan["x_column"], num_cols or all_cols)
        if "y_column" in plan:
            plan["y_column"] = _closest_column(plan["y_column"], num_cols or all_cols)

    return plan
