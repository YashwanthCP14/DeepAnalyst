def get_schema(df):
    lines = ["Columns:"]
    for col in df.columns:
        lines.append(f"{col} ({df[col].dtype})")
    return "\n".join(lines)
