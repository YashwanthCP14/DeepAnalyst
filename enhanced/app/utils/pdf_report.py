import io
import pandas as pd
from datetime import datetime

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False


def generate_pdf_report(df_filtered, result, explanation, plan, insights, quality_summary):
    """
    Generates a PDF report and returns bytes.
    Falls back to a plain-text report if fpdf2 is not installed.
    """
    if not FPDF_AVAILABLE:
        return _text_fallback(df_filtered, result, explanation, plan, insights, quality_summary)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    pdf.set_x(15)

    # ── Header ───────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, "Deep Analyst - Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}", ln=True, align="C")
    pdf.ln(6)

    # ── Dataset overview ─────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Dataset Overview", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Rows: {quality_summary.get('total_rows', '-')}  |  "
                   f"Columns: {quality_summary.get('total_columns', '-')}  |  "
                   f"Duplicates: {quality_summary.get('duplicate_rows', '-')}  |  "
                   f"Missing columns: {quality_summary.get('columns_with_missing', '-')}", ln=True)
    pdf.ln(4)

    # ── Analysis plan ────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Analysis Plan", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for k, v in plan.items():
        pdf.cell(0, 6, f"  {k}: {v}", ln=True)
    pdf.ln(4)

    # ── Result table (first 20 rows) ─────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Analysis Results (first 20 rows)", ln=True)
    pdf.set_font("Helvetica", "", 8)

    if result is not None and not result.empty:
        cols = result.columns.tolist()
        col_w = min(40, 180 // max(len(cols), 1))
        # Header row
        pdf.set_fill_color(220, 220, 220)
        for c in cols:
            pdf.cell(col_w, 7, str(c)[:18], border=1, fill=True)
        pdf.ln()
        # Data rows
        for _, row in result.head(20).iterrows():
            for c in cols:
                val = str(row[c])
                pdf.cell(col_w, 6, val[:18], border=1)
            pdf.ln()
    pdf.ln(4)

    # ── Insights ─────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Auto Insights", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for ins in insights:
        pdf.cell(0, 6, f"  - {ins}", ln=True)
    pdf.ln(4)

    # ── AI explanation ───────────────────────────────────────────────────────
    if isinstance(explanation, dict):
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "AI Summary", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, explanation.get("summary", ""))
        pdf.ln(2)

        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "Key Insights", ln=True)
        pdf.set_font("Helvetica", "", 10)
        for i in explanation.get("insights", []):
            pdf.multi_cell(0, 6, f"  - {i}")

        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "Recommendation", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, explanation.get("recommendation", ""))

    return bytes(pdf.output())


def _text_fallback(df_filtered, result, explanation, plan, insights, quality_summary):
    """Plain text fallback when fpdf2 is unavailable."""
    lines = [
        "DEEP ANALYST REPORT",
        f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}",
        "",
        "DATASET OVERVIEW",
        f"  Rows: {quality_summary.get('total_rows', '-')}",
        f"  Columns: {quality_summary.get('total_columns', '-')}",
        f"  Duplicates: {quality_summary.get('duplicate_rows', '-')}",
        "",
        "ANALYSIS PLAN",
    ]
    for k, v in plan.items():
        lines.append(f"  {k}: {v}")
    lines += ["", "AUTO INSIGHTS"]
    for ins in insights:
        lines.append(f"  - {ins}")
    if isinstance(explanation, dict):
        lines += ["", "AI SUMMARY", explanation.get("summary", "")]
        lines += ["", "RECOMMENDATION", explanation.get("recommendation", "")]
    return "\n".join(lines).encode("utf-8")
