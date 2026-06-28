import re


def _closest_column(name: str, columns: list) -> str:
    """Return the closest real column name."""
    name_lower = name.lower().replace(" ", "_")
    for c in columns:
        if c.lower() == name_lower:
            return c
    for c in columns:
        if name_lower in c.lower() or c.lower() in name_lower:
            return c
    return columns[0] if columns else name


def validate_plan(plan, df):
    if not isinstance(plan, dict):
        return False, "Invalid plan format"

    cols = df.columns.tolist()
    num_cols = df.select_dtypes(include="number").columns.tolist()

    # Auto-correct target_column instead of crashing
    if "target_column" not in plan or not plan["target_column"]:
        plan["target_column"] = num_cols[0] if num_cols else cols[0]

    if plan["target_column"] not in cols:
        plan["target_column"] = _closest_column(plan["target_column"], cols)

    # Auto-correct group_by columns
    if "group_by" in plan and isinstance(plan["group_by"], list):
        plan["group_by"] = [
            c if c in cols else _closest_column(c, cols)
            for c in plan["group_by"]
        ]

    # Auto-correct x_column / y_column for correlation / scatter
    if "x_column" in plan and plan["x_column"] not in cols:
        plan["x_column"] = _closest_column(plan["x_column"], num_cols or cols)
    if "y_column" in plan and plan["y_column"] not in cols:
        plan["y_column"] = _closest_column(plan["y_column"], num_cols or cols)

    # Ensure x_column / y_column exist for correlation ops
    op = plan.get("operation", "group_by_summary")
    if op in ("correlation", "scatter") and num_cols:
        plan.setdefault("x_column", num_cols[0])
        plan.setdefault("y_column", num_cols[1] if len(num_cols) > 1 else num_cols[0])

    return True, "Valid"
