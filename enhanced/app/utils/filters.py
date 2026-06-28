def apply_filters(df, filters):
    for f in filters:
        col, op, val = f["column"], f["op"], f["value"]
        if op == "==":
            df = df[df[col] == val]
        elif op == ">":
            df = df[df[col] > val]
    return df
