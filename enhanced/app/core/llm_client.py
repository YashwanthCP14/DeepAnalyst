import requests
import json
import re
from app.core.config import Gemini_API


def generate_response(prompt: str) -> str:
    """Try Ollama first, then Gemini if API key available, fall back to rule-based response."""

    # ── 1. Try Ollama (original behaviour preserved) ─────────────────────────
    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "tinyllama", "prompt": prompt, "stream": False},
            timeout=20,
        )
        if resp.status_code == 200:
            return resp.json().get("response", "")
    except Exception:
        pass

    # ── 2. Try Gemini REST API if key is configured ───────────────────────────
    if Gemini_API:
        try:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"gemini-pro:generateContent?key={Gemini_API}"
            )
            body = {"contents": [{"parts": [{"text": prompt}]}]}
            r = requests.post(url, json=body, timeout=30)
            if r.status_code == 200:
                data = r.json()
                return (
                    data["candidates"][0]["content"]["parts"][0]["text"]
                )
        except Exception:
            pass

    # ── 3. Rule-based fallback (original logic kept intact) ───────────────────
    columns = []
    num_cols = []
    cat_cols = []

    for line in prompt.splitlines():
        m = re.match(r"^\s*(\w[\w\s]*?)\s+\((.*?)\)\s*$", line.strip())
        if m:
            col_name = m.group(1).strip()
            dtype = m.group(2).strip()
            columns.append(col_name)
            if any(t in dtype for t in ["int", "float"]):
                num_cols.append(col_name)
            else:
                cat_cols.append(col_name)

    q = prompt.lower()

    metric = "mean"
    if any(w in q for w in ["total", "sum"]):
        metric = "sum"
    elif any(w in q for w in ["count", "how many"]):
        metric = "count"

    chart_type = "bar"
    if "line" in q or "trend" in q or "over time" in q:
        chart_type = "line"
    elif "pie" in q or "share" in q or "proportion" in q:
        chart_type = "pie"
    elif "scatter" in q or "correlation" in q or "vs" in q:
        chart_type = "scatter"
    elif "heat" in q or "heatmap" in q:
        chart_type = "heatmap"

    # Detect operation from question
    operation = "group_by_summary"
    if any(w in q for w in ["correlat", "relationship", "scatter", "vs"]):
        operation = "correlation"
    elif any(w in q for w in ["outlier", "anomal", "unusual", "extreme"]):
        operation = "outlier_detection"
    elif any(w in q for w in ["trend", "over time", "time series", "forecast"]):
        operation = "trend_analysis"
    elif any(w in q for w in ["distribut", "histogram", "spread"]):
        operation = "distribution"

    group_by = [cat_cols[0]] if cat_cols else (columns[:1] if columns else ["category"])
    target = num_cols[0] if num_cols else (columns[1] if len(columns) > 1 else "value")
    x_col = num_cols[0] if num_cols else target
    y_col = num_cols[1] if len(num_cols) > 1 else target

    plan = {
        "operation": operation,
        "group_by": group_by,
        "target_column": target,
        "x_column": x_col,
        "y_column": y_col,
        "metric": metric,
        "chart_type": chart_type,
        "need_chart": True,
    }

    return json.dumps(plan)


class DummyModel:
    def generate_content(self, prompt):
        return generate_response(prompt)


model = DummyModel()
