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


def call_explainer(question, plan, result):
    prompt = f"""
Return STRICT JSON:

{{
  "summary": "short answer",
  "insights": ["point1", "point2"],
  "recommendation": "action"
}}

No extra text.

Question: {question}
Results: {json.dumps(result[:10])}
"""

    try:
        response = generate_response(prompt)
        structured = extract_json(response)
        if structured:
            return structured
    except Exception:
        pass

    # Fallback: build a meaningful response from the data itself
    summary = f"Analysis of your question: '{question}' completed successfully."
    insights = []

    if result:
        keys = list(result[0].keys())
        if len(keys) >= 2:
            val_key = keys[-1]
            label_key = keys[0]
            values = [row[val_key] for row in result if isinstance(row.get(val_key), (int, float))]
            if values:
                top = max(result, key=lambda r: r.get(val_key, 0))
                insights.append(f"Highest value: {top.get(label_key)} with {val_key} = {top.get(val_key):,.2f}")
                insights.append(f"Total across all groups: {sum(values):,.2f}")
                insights.append(f"Average per group: {sum(values)/len(values):,.2f}")

    if not insights:
        insights = ["Data processed successfully.", "Review the table and chart above for details."]

    return {
        "summary": summary,
        "insights": insights,
        "recommendation": "Drill down further by applying sidebar filters or asking a follow-up question."
    }
