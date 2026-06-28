import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io as _io

from app.agents.planner import call_planner
from app.agents.explainer import call_explainer
from app.utils.auto_insights import generate_auto_insights
from app.utils.schema import get_schema
from app.utils.preprocess import preprocess_dates
from app.utils.analysis import run_analysis
from app.utils.charts import generate_chart
from app.core.validator import validate_plan
from app.utils.data_quality import get_data_quality_report
from app.utils.pdf_report import generate_pdf_report

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Deep Analyst",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# HELPER — escape any HTML that comes back from the LLM
# ─────────────────────────────────────────────────────────────────────────────
def esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL STYLES
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Aurora animated background ── */
.stApp {
    background: linear-gradient(270deg, #1a1a2e, #302b63, #0f3460, #533483);
    background-size: 400% 400%;
    animation: aurora 12s ease infinite;
    min-height: 100vh;
}
@keyframes aurora {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e1b4b 0%, #2e1065 100%) !important;
    border-right: 1px solid rgba(139,92,246,0.3);
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div { color: #e2e8f0 !important; }

/* ── Main text on dark background ── */
.stMarkdown p, .stMarkdown li, .stText, p, label { color: #e2e8f0; }

/* ── Hero header ── */
.hero-header {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 40%, #a855f7 70%, #ec4899 100%);
    border-radius: 20px;
    padding: 2.5rem 2rem 2rem 2rem;
    text-align: center;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(139,92,246,0.4);
    position: relative;
    overflow: hidden;
}
.hero-header::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 60%);
    animation: shimmer 6s ease-in-out infinite;
}
@keyframes shimmer {
    0%,100% { transform: translate(0,0); }
    50% { transform: translate(5%,5%); }
}
.hero-title { font-size: 2.6rem; font-weight: 700; color: white; letter-spacing: -0.5px; margin: 0; text-shadow: 0 2px 8px rgba(0,0,0,0.2); }
.hero-sub { font-size: 1rem; color: rgba(255,255,255,0.85); margin-top: 0.5rem; }
.hero-badges { margin-top: 1rem; display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }
.badge { background: rgba(255,255,255,0.18); color: white; border: 1px solid rgba(255,255,255,0.3); border-radius: 20px; padding: 4px 14px; font-size: 12px; font-weight: 500; backdrop-filter: blur(4px); }

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.08) !important;
    border-radius: 16px !important;
    padding: 1rem 1.2rem !important;
    border: 1px solid rgba(139,92,246,0.35) !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.2) !important;
    backdrop-filter: blur(8px);
    transition: transform 0.2s, box-shadow 0.2s;
}
[data-testid="stMetric"]:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(139,92,246,0.3) !important; }
[data-testid="stMetricLabel"] p { color: #a5b4fc !important; font-size: 0.82rem !important; font-weight: 500 !important; }
[data-testid="stMetricValue"] { color: #e2e8f0 !important; font-weight: 700 !important; }

/* ── Snapshot cards ── */
.snapshot-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin: 1rem 0; }
.snapshot-card { background: rgba(255,255,255,0.07); border-radius: 14px; padding: 1.1rem 1.2rem; border: 1px solid rgba(139,92,246,0.3); backdrop-filter: blur(8px); transition: transform 0.2s; }
.snapshot-card:hover { transform: translateY(-2px); background: rgba(255,255,255,0.1); }
.snap-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; color: #a5b4fc; font-weight: 600; margin-bottom: 4px; }
.snap-value { font-size: 1.4rem; font-weight: 700; color: #e2e8f0; }
.snap-sub { font-size: 12px; color: #94a3b8; margin-top: 2px; }

/* ── Insight pills ── */
.insight-pill { display: inline-block; background: rgba(99,102,241,0.25); border: 1px solid rgba(139,92,246,0.4); border-radius: 25px; padding: 6px 16px; margin: 4px; font-size: 13px; color: #c4b5fd; font-weight: 500; }
.insight-grid { display: flex; flex-wrap: wrap; gap: 6px; margin: 0.5rem 0; }

/* ── Tabs ── */
[data-testid="stTabs"] [role="tablist"] { background: rgba(255,255,255,0.06); border-radius: 12px; padding: 4px; border: 1px solid rgba(139,92,246,0.25); gap: 2px; }
[data-testid="stTabs"] [role="tab"] { border-radius: 8px; font-weight: 500; color: #94a3b8; transition: all 0.2s; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { background: linear-gradient(135deg, #6366f1, #a855f7) !important; color: white !important; }

/* ── Upload zone ── */
[data-testid="stFileUploader"] { background: rgba(255,255,255,0.06); border-radius: 16px; border: 2px dashed rgba(139,92,246,0.5); padding: 1rem; }
[data-testid="stFileUploader"]:hover { border-color: #8b5cf6; background: rgba(139,92,246,0.1); }

/* ── Buttons ── */
.stDownloadButton > button, .stButton > button { background: linear-gradient(135deg, #6366f1, #8b5cf6) !important; color: white !important; border: none !important; border-radius: 10px !important; font-weight: 500 !important; padding: 0.4rem 1.2rem !important; box-shadow: 0 2px 8px rgba(99,102,241,0.4) !important; transition: opacity 0.2s !important; }
.stDownloadButton > button:hover, .stButton > button:hover { opacity: 0.85 !important; }

/* ── Chat messages ── */
[data-testid="stChatMessage"] { background: rgba(255,255,255,0.06) !important; border-radius: 14px !important; border: 1px solid rgba(139,92,246,0.25) !important; margin-bottom: 8px !important; backdrop-filter: blur(8px); }

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; border: 1px solid rgba(139,92,246,0.25); }

/* ── Section titles ── */
.sec-title { font-size: 1.1rem; font-weight: 600; color: #a5b4fc; display: flex; align-items: center; gap: 8px; margin-bottom: 1rem; }

/* ── Divider ── */
hr { border-color: rgba(139,92,246,0.2) !important; }

/* ── selectbox / multiselect ── */
[data-testid="stSelectbox"] > div, [data-testid="stMultiSelect"] > div { background: rgba(255,255,255,0.07) !important; border-color: rgba(139,92,246,0.3) !important; color: #e2e8f0 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PLOTLY THEME
# ─────────────────────────────────────────────────────────────────────────────
PLOTLY_COLORS = ["#818cf8","#c084fc","#f472b6","#22d3ee","#34d399","#fbbf24","#f87171","#a78bfa"]
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(255,255,255,0.04)",
    font=dict(family="Inter", color="#e2e8f0"),
    title_font=dict(size=15, color="#a5b4fc", family="Inter"),
    legend=dict(bgcolor="rgba(30,27,75,0.7)", bordercolor="rgba(139,92,246,0.3)", borderwidth=1),
    margin=dict(l=20, r=20, t=50, b=20),
    xaxis=dict(gridcolor="rgba(139,92,246,0.15)", linecolor="rgba(139,92,246,0.2)", color="#94a3b8"),
    yaxis=dict(gridcolor="rgba(139,92,246,0.15)", linecolor="rgba(139,92,246,0.2)", color="#94a3b8"),
    colorway=PLOTLY_COLORS,
)

def apply_theme(fig):
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# HERO HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
    <p class="hero-title">🔬 Deep Analyst</p>
    <p class="hero-sub">AI-powered data analysis &amp; visualisation platform</p>
    <div class="hero-badges">
        <span class="badge">📊 Multi-format Upload</span>
        <span class="badge">🤖 AI Assistant</span>
        <span class="badge">🔍 Data Quality</span>
        <span class="badge">⚡ Smart Snapshot</span>
        <span class="badge">📄 PDF Export</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FILE UPLOAD
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data(file):
    name = file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(file)
    elif name.endswith((".xlsx", ".xlsm")):
        return pd.read_excel(file, engine="openpyxl")
    elif name.endswith(".xls"):
        return pd.read_excel(file, engine="xlrd")
    elif name.endswith(".json"):
        return pd.read_json(file)
    else:
        return pd.read_csv(file)

col_up, col_info = st.columns([2, 1])
with col_up:
    file = st.file_uploader(
        "📂 Upload your data file",
        type=["csv", "xlsx", "xls", "xlsm", "json"],
        help="Supports CSV, Excel (.xlsx / .xls), and JSON files",
    )
with col_info:
    st.markdown("""
    <div style="background:rgba(255,255,255,0.07);border-radius:14px;padding:1rem 1.2rem;
                border:1px solid rgba(139,92,246,0.3);height:100%;box-sizing:border-box;backdrop-filter:blur(8px);">
        <div style="font-size:13px;color:#94a3b8;line-height:1.8;">
            <b style="color:#a5b4fc;">Supported formats</b><br>
            📄 CSV &nbsp;|&nbsp; 📊 Excel (.xlsx / .xls)<br>
            🗂 JSON<br><br>
            <b style="color:#a5b4fc;">What you get</b><br>
            6 analysis tabs + AI chat<br>
            Auto insights &amp; PDF reports
        </div>
    </div>
    """, unsafe_allow_html=True)

if file:
    df = load_data(file)
    df.columns = df.columns.str.strip().str.lower()
    df = preprocess_dates(df)

    # ── SIDEBAR ──────────────────────────────────────────────────────────────
    st.sidebar.markdown("""
    <div style="text-align:center;padding:1rem 0 0.5rem;">
        <div style="font-size:1.5rem;font-weight:700;
                    background:linear-gradient(135deg,#818cf8,#c084fc);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            Deep Analyst
        </div>
        <div style="font-size:12px;color:#94a3b8;margin-top:2px;">AI Data Platform</div>
    </div>
    <hr style="border-color:rgba(139,92,246,0.3);">
    """, unsafe_allow_html=True)

    st.sidebar.markdown("### 🎛️ Filters")
    df_filtered = df.copy()

    for col in df.columns:
        if df[col].dtype == "object" and df[col].nunique() < 20:
            selected = st.sidebar.multiselect(col, df[col].unique())
            if selected:
                df_filtered = df_filtered[df_filtered[col].isin(selected)]

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"""
    <div style="background:rgba(99,102,241,0.2);border-radius:12px;padding:12px 14px;
                font-size:13px;color:#c4b5fd;border:1px solid rgba(139,92,246,0.3);">
        <b>File:</b> {esc(file.name)}<br>
        <b>Rows:</b> {len(df_filtered):,} &nbsp;|&nbsp; <b>Cols:</b> {len(df_filtered.columns)}
    </div>
    """, unsafe_allow_html=True)

    # ── TABS ─────────────────────────────────────────────────────────────────
    tab_overview, tab_snapshot, tab_visuals, tab_quality, tab_advanced, tab_chat = st.tabs([
        "📊 Overview",
        "⚡ Smart Snapshot",
        "📈 Visual Analytics",
        "🔍 Data Quality",
        "🧪 Advanced Analysis",
        "🤖 AI Assistant",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — OVERVIEW
    # ══════════════════════════════════════════════════════════════════════════
    with tab_overview:
        st.markdown('<div class="sec-title">📊 Dataset Overview</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", f"{len(df_filtered):,}")
        c2.metric("Columns", len(df_filtered.columns))
        c3.metric("Missing Values", int(df_filtered.isnull().sum().sum()))
        c4.metric("Numeric Columns", len(df_filtered.select_dtypes(include="number").columns))
        st.markdown("---")
        st.markdown('<div class="sec-title">📋 Data Preview</div>', unsafe_allow_html=True)
        st.dataframe(df_filtered.head(50), use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — SMART SNAPSHOT
    # ══════════════════════════════════════════════════════════════════════════
    with tab_snapshot:
        st.markdown('<div class="sec-title">⚡ Smart Snapshot — Auto Executive Summary</div>', unsafe_allow_html=True)
        st.markdown(
            "<p style='color:#94a3b8;font-size:13px;margin-top:-8px;margin-bottom:16px;'>"
            "Automatically generated summary for every numeric column — no questions needed.</p>",
            unsafe_allow_html=True,
        )
        num_snap_cols = df_filtered.select_dtypes(include="number").columns.tolist()
        cat_snap_cols = df_filtered.select_dtypes(include="object").columns.tolist()

        if not num_snap_cols:
            st.info("No numeric columns found in this dataset.")
        else:
            snap_col = st.selectbox("Select column to snapshot", num_snap_cols, key="snap_col_select")
            s = df_filtered[snap_col].dropna()

            q1_s, q3_s = s.quantile(0.25), s.quantile(0.75)
            iqr_s = q3_s - q1_s
            n_out_s = int(((s < q1_s - 1.5 * iqr_s) | (s > q3_s + 1.5 * iqr_s)).sum())
            cv_s = (s.std() / s.mean() * 100) if s.mean() != 0 else 0
            half = len(s) // 2
            trend_dir = "up" if (s.iloc[half:].mean() > s.iloc[:half].mean() * 1.03) else \
                        "down" if (s.iloc[half:].mean() < s.iloc[:half].mean() * 0.97) else "flat"
            trend_icon = "▲" if trend_dir == "up" else ("▼" if trend_dir == "down" else "━")
            trend_color = "#34d399" if trend_dir == "up" else ("#f87171" if trend_dir == "down" else "#94a3b8")
            out_color = "#f87171" if n_out_s > 0 else "#34d399"
            cv_color = "#fbbf24" if cv_s > 50 else "#34d399"

            st.markdown(f"""
            <div class="snapshot-grid">
                <div class="snapshot-card">
                    <div class="snap-label">Total</div>
                    <div class="snap-value">{s.sum():,.1f}</div>
                    <div class="snap-sub">sum of all values</div>
                </div>
                <div class="snapshot-card">
                    <div class="snap-label">Mean</div>
                    <div class="snap-value">{s.mean():,.2f}</div>
                    <div class="snap-sub">median: {s.median():,.2f}</div>
                </div>
                <div class="snapshot-card">
                    <div class="snap-label">Range</div>
                    <div class="snap-value">{s.min():,.1f} to {s.max():,.1f}</div>
                    <div class="snap-sub">std dev: {s.std():,.2f}</div>
                </div>
                <div class="snapshot-card">
                    <div class="snap-label">Trend</div>
                    <div class="snap-value" style="color:{trend_color};">{trend_icon}</div>
                    <div class="snap-sub">{trend_dir} across dataset</div>
                </div>
                <div class="snapshot-card">
                    <div class="snap-label">Outliers</div>
                    <div class="snap-value" style="color:{out_color};">{n_out_s}</div>
                    <div class="snap-sub">IQR method</div>
                </div>
                <div class="snapshot-card">
                    <div class="snap-label">Variability (CV)</div>
                    <div class="snap-value" style="color:{cv_color};">{cv_s:.1f}%</div>
                    <div class="snap-sub">{'high' if cv_s > 50 else 'normal'} spread</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            fig_spark = go.Figure()
            fig_spark.add_trace(go.Scatter(
                y=s.values, mode="lines",
                line=dict(color="#818cf8", width=2),
                fill="tozeroy", fillcolor="rgba(129,140,248,0.1)",
                name=snap_col,
            ))
            rolling = pd.Series(s.values).rolling(window=max(3, len(s)//10), min_periods=1).mean()
            fig_spark.add_trace(go.Scatter(
                y=rolling.values, mode="lines",
                line=dict(color="#f472b6", width=2, dash="dot"),
                name="Rolling avg",
            ))
            fig_spark.update_layout(
                title=f"Value trend — {snap_col}", height=260, showlegend=True,
                **{k: v for k, v in PLOTLY_LAYOUT.items() if k != "colorway"},
            )
            st.plotly_chart(fig_spark, use_container_width=True)

            if cat_snap_cols:
                snap_group = st.selectbox("Group by (optional)", ["None"] + cat_snap_cols, key="snap_group")
                if snap_group != "None":
                    grp = df_filtered.groupby(snap_group)[snap_col].sum().reset_index()
                    grp = grp.sort_values(snap_col, ascending=False)
                    col_tb1, col_tb2 = st.columns(2)
                    with col_tb1:
                        st.markdown('<div class="sec-title" style="font-size:0.95rem;">🏆 Top 5</div>', unsafe_allow_html=True)
                        fig_top = apply_theme(px.bar(grp.head(5), x=snap_col, y=snap_group, orientation="h",
                            color=snap_col, color_continuous_scale=["#4338ca","#818cf8"], title="Top 5"))
                        fig_top.update_layout(height=260, showlegend=False)
                        st.plotly_chart(fig_top, use_container_width=True)
                    with col_tb2:
                        st.markdown('<div class="sec-title" style="font-size:0.95rem;">📉 Bottom 5</div>', unsafe_allow_html=True)
                        fig_bot = apply_theme(px.bar(grp.tail(5).sort_values(snap_col), x=snap_col, y=snap_group,
                            orientation="h", color=snap_col, color_continuous_scale=["#9d174d","#f472b6"], title="Bottom 5"))
                        fig_bot.update_layout(height=260, showlegend=False)
                        st.plotly_chart(fig_bot, use_container_width=True)

            if n_out_s > 0:
                st.markdown("---")
                st.markdown(f"""
                <div style="background:rgba(244,63,94,0.15);border-left:4px solid #f43f5e;
                            border-radius:10px;padding:10px 16px;margin-bottom:12px;
                            border:1px solid rgba(244,63,94,0.3);">
                    <b style="color:#fda4af;">Warning: {n_out_s} anomalies detected in {esc(snap_col)}</b>
                    <span style="color:#fca5a5;font-size:13px;"> — rows listed below</span>
                </div>
                """, unsafe_allow_html=True)
                outlier_rows = df_filtered[
                    (df_filtered[snap_col] < q1_s - 1.5 * iqr_s) |
                    (df_filtered[snap_col] > q3_s + 1.5 * iqr_s)
                ]
                st.dataframe(outlier_rows, use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — VISUAL ANALYTICS
    # ══════════════════════════════════════════════════════════════════════════
    with tab_visuals:
        st.markdown('<div class="sec-title">📈 Visual Analytics</div>', unsafe_allow_html=True)
        num_cols = df_filtered.select_dtypes(include="number").columns
        if len(num_cols) > 0:
            col = st.selectbox("Select Feature", num_cols, key="vis_feat")
            c1, c2 = st.columns(2)
            with c1:
                fig = apply_theme(px.histogram(df_filtered, x=col,
                    title=f"Distribution of {col}", color_discrete_sequence=["#818cf8"]))
                fig.update_traces(marker_line_color="#6366f1", marker_line_width=1)
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                fig2 = apply_theme(px.box(df_filtered, y=col,
                    title=f"Box Plot — {col}", color_discrete_sequence=["#c084fc"]))
                st.plotly_chart(fig2, use_container_width=True)

            if len(num_cols) >= 2:
                st.markdown("---")
                st.markdown('<div class="sec-title">🔗 Scatter Matrix</div>', unsafe_allow_html=True)
                scatter_cols = st.multiselect(
                    "Select columns for scatter matrix (2-4)", num_cols,
                    default=list(num_cols[:min(4, len(num_cols))]), key="scatter_matrix")
                if len(scatter_cols) >= 2:
                    cat_cols_list = df_filtered.select_dtypes(include="object").columns.tolist()
                    color_col = cat_cols_list[0] if cat_cols_list else None
                    fig3 = apply_theme(px.scatter_matrix(df_filtered, dimensions=scatter_cols,
                        color=color_col, title="Scatter Matrix", color_discrete_sequence=PLOTLY_COLORS))
                    st.plotly_chart(fig3, use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4 — DATA QUALITY
    # ══════════════════════════════════════════════════════════════════════════
    with tab_quality:
        st.markdown('<div class="sec-title">🔍 Data Quality Report</div>', unsafe_allow_html=True)
        quality_df, quality_summary = get_data_quality_report(df_filtered)

        q1, q2, q3, q4, q5 = st.columns(5)
        q1.metric("Total Rows", f"{quality_summary['total_rows']:,}")
        q2.metric("Total Columns", quality_summary["total_columns"])
        q3.metric("Duplicate Rows", quality_summary["duplicate_rows"])
        q4.metric("Complete Rows", quality_summary["complete_rows"])
        q5.metric("Cols with Missing", quality_summary["columns_with_missing"])

        st.markdown("---")
        st.markdown('<div class="sec-title">Per-Column Profile</div>', unsafe_allow_html=True)

        def highlight_issues(val):
            if val == "OK":
                return "color: #34d399; font-weight:600"
            return "color: #f87171; font-weight: bold"

        # Use .map() for newer pandas, fallback to .applymap() for older
        try:
            styled = quality_df.style.map(highlight_issues, subset=["Issues"])
        except AttributeError:
            styled = quality_df.style.applymap(highlight_issues, subset=["Issues"])

        st.dataframe(styled, use_container_width=True)

        st.markdown("---")
        st.markdown('<div class="sec-title">Fill Rate by Column</div>', unsafe_allow_html=True)
        fill_fig = apply_theme(px.bar(quality_df, x="Column", y="Fill Rate (%)",
            color="Fill Rate (%)", color_continuous_scale=["#f43f5e","#fbbf24","#34d399"],
            range_color=[0, 100], title="Column Fill Rate (%)"))
        fill_fig.update_traces(marker_line_width=0)
        st.plotly_chart(fill_fig, use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 5 — ADVANCED ANALYSIS
    # ══════════════════════════════════════════════════════════════════════════
    with tab_advanced:
        st.markdown('<div class="sec-title">🧪 Advanced Analysis</div>', unsafe_allow_html=True)
        num_df = df_filtered.select_dtypes(include="number")

        if num_df.shape[1] >= 2:
            st.markdown("#### Correlation Heatmap")
            corr = num_df.corr().round(2)
            heatmap_fig = apply_theme(px.imshow(corr, text_auto=".2f",
                color_continuous_scale=["#6366f1","#1e1b4b","#ec4899"],
                title="Correlation Matrix", aspect="auto"))
            st.plotly_chart(heatmap_fig, use_container_width=True)

            st.markdown("**Top correlations:**")
            corr_pairs = corr.where(~(corr == 1.0)).stack().reset_index()
            corr_pairs.columns = ["Feature A", "Feature B", "Correlation"]
            corr_pairs["abs"] = corr_pairs["Correlation"].abs()
            corr_pairs = corr_pairs.sort_values("abs", ascending=False).drop_duplicates(
                subset=["abs"]).drop(columns="abs").head(8)
            st.dataframe(corr_pairs, use_container_width=True)

        st.markdown("---")
        st.markdown("#### Outlier Detection (IQR method)")
        num_col_list = num_df.columns.tolist()
        if num_col_list:
            outlier_col = st.selectbox("Select column", num_col_list, key="outlier_col")
            col_data = df_filtered[outlier_col].dropna()
            q1_v, q3_v = col_data.quantile(0.25), col_data.quantile(0.75)
            iqr = q3_v - q1_v
            lower, upper = q1_v - 1.5 * iqr, q3_v + 1.5 * iqr
            n_out = ((col_data < lower) | (col_data > upper)).sum()
            oc1, oc2, oc3 = st.columns(3)
            oc1.metric("Lower Bound", f"{lower:,.2f}")
            oc2.metric("Upper Bound", f"{upper:,.2f}")
            oc3.metric("Outliers Found", int(n_out))
            out_fig = apply_theme(px.box(df_filtered, y=outlier_col, points="all",
                title=f"Outlier Detection — {outlier_col}", color_discrete_sequence=["#818cf8"]))
            st.plotly_chart(out_fig, use_container_width=True)

        st.markdown("---")
        st.markdown("#### Distribution Statistics")
        if num_col_list:
            dist_col = st.selectbox("Select column", num_col_list, key="dist_col")
            s = df_filtered[dist_col].dropna()
            ds1, ds2, ds3, ds4 = st.columns(4)
            ds1.metric("Mean", f"{s.mean():,.2f}")
            ds2.metric("Median", f"{s.median():,.2f}")
            ds3.metric("Std Dev", f"{s.std():,.2f}")
            ds4.metric("Skewness", f"{s.skew():,.2f}")
            dist_fig = apply_theme(px.histogram(df_filtered, x=dist_col, marginal="box",
                nbins=40, title=f"Distribution — {dist_col}", color_discrete_sequence=["#c084fc"]))
            st.plotly_chart(dist_fig, use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 6 — AI ASSISTANT
    # ══════════════════════════════════════════════════════════════════════════
    with tab_chat:
        st.markdown('<div class="sec-title">🤖 AI Assistant</div>', unsafe_allow_html=True)

        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "last_result" not in st.session_state:
            st.session_state.last_result = None
        if "last_explanation" not in st.session_state:
            st.session_state.last_explanation = None
        if "last_plan" not in st.session_state:
            st.session_state.last_plan = {}
        if "last_insights" not in st.session_state:
            st.session_state.last_insights = []

        for m in st.session_state.messages:
            with st.chat_message(m["role"]):
                st.write(m["content"])

        user_input = st.chat_input("Ask your data...", key="chat_main")

        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            schema = get_schema(df_filtered)
            try:
                plan = call_planner(schema, user_input, st.session_state.messages)
                valid, msg = validate_plan(plan, df_filtered)
                if not valid:
                    st.error(msg)
                    st.stop()
                result = run_analysis(df_filtered, plan)
                chart = generate_chart(result, plan)
                explanation = call_explainer(user_input, plan, result.to_dict("records"))
            except Exception as e:
                st.error(str(e))
                st.stop()

            with st.chat_message("assistant"):
                st.markdown('<div class="sec-title">📊 Results</div>', unsafe_allow_html=True)
                st.dataframe(result, use_container_width=True)

                target = plan.get("target_column")
                if target and target in result.columns:
                    k1, k2, k3 = st.columns(3)
                    k1.metric("Total", f"{result[target].sum():,.2f}")
                    k2.metric("Avg", f"{result[target].mean():,.2f}")
                    k3.metric("Max", f"{result[target].max():,.2f}")

                    auto = generate_auto_insights(result, target)
                    st.markdown('<div class="sec-title" style="margin-top:1rem;">⚡ Auto Insights</div>', unsafe_allow_html=True)
                    pills_html = '<div class="insight-grid">' + "".join(
                        f'<span class="insight-pill">{esc(i)}</span>' for i in auto
                    ) + "</div>"
                    st.markdown(pills_html, unsafe_allow_html=True)
                    st.session_state.last_insights = auto

                if chart is not None:
                    apply_theme(chart)
                    st.plotly_chart(chart, use_container_width=True)

                # ── AI explanation — ALL text escaped before injecting into HTML ──
                if isinstance(explanation, dict):
                    summary_safe = esc(explanation.get("summary", ""))
                    rec_safe     = esc(explanation.get("recommendation", ""))

                    st.markdown(f"""
                    <div style="background:rgba(99,102,241,0.15);border-radius:14px;
                                padding:1.2rem 1.4rem;margin:0.8rem 0;
                                border:1px solid rgba(139,92,246,0.35);">
                        <div style="font-size:13px;font-weight:600;color:#a5b4fc;margin-bottom:6px;">
                            📌 Summary
                        </div>
                        <div style="color:#e2e8f0;font-size:14px;">{summary_safe}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown('<div class="sec-title" style="margin-top:0.8rem;">📊 Key Insights</div>', unsafe_allow_html=True)
                    for i in explanation.get("insights", []):
                        st.write(f"• {esc(i)}")

                    st.markdown(f"""
                    <div style="background:rgba(52,211,153,0.1);border-radius:12px;
                                padding:1rem 1.2rem;margin-top:0.8rem;
                                border:1px solid rgba(52,211,153,0.3);">
                        <div style="font-size:13px;font-weight:600;color:#6ee7b7;">
                            🚀 Recommendation
                        </div>
                        <div style="color:#e2e8f0;font-size:14px;margin-top:4px;">{rec_safe}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.write(esc(str(explanation)))

                ex1, ex2 = st.columns(2)
                with ex1:
                    csv = result.to_csv(index=False)
                    st.download_button("📥 Download CSV", data=csv,
                        file_name="analysis_result.csv", mime="text/csv")
                with ex2:
                    buf = _io.BytesIO()
                    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                        result.to_excel(writer, index=False, sheet_name="Results")
                    buf.seek(0)
                    st.download_button("📊 Download Excel", data=buf.getvalue(),
                        file_name="analysis_result.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

                st.session_state.last_result = result
                st.session_state.last_explanation = explanation
                st.session_state.last_plan = plan

            st.session_state.messages.append({
                "role": "assistant",
                "content": str(explanation),
            })

        if st.session_state.last_result is not None:
            st.markdown("---")
            st.markdown('<div class="sec-title">📄 Export Full Report</div>', unsafe_allow_html=True)
            _, q_summary = get_data_quality_report(df_filtered)
            pdf_bytes = generate_pdf_report(
                df_filtered,
                st.session_state.last_result,
                st.session_state.last_explanation,
                st.session_state.last_plan,
                st.session_state.last_insights,
                q_summary,
            )
            st.download_button("📄 Download PDF Report", data=pdf_bytes,
                file_name="deep_analyst_report.pdf", mime="application/pdf")

else:
    st.markdown("""
    <div style="text-align:center;padding:3rem 1rem;">
        <div style="font-size:4rem;margin-bottom:1rem;">📂</div>
        <div style="font-size:1.3rem;font-weight:600;color:#a5b4fc;margin-bottom:0.5rem;">
            Upload a file to get started
        </div>
        <div style="color:#94a3b8;font-size:14px;max-width:420px;margin:0 auto;">
            Supports CSV, Excel, and JSON. The platform will automatically profile
            your data and make it ready for AI-powered analysis.
        </div>
        <div style="margin-top:2rem;display:flex;justify-content:center;gap:20px;flex-wrap:wrap;">
            <div style="background:rgba(255,255,255,0.07);border:1px solid rgba(139,92,246,0.3);
                        border-radius:14px;padding:1.2rem 1.6rem;min-width:160px;
                        backdrop-filter:blur(8px);">
                <div style="font-size:1.8rem;">⚡</div>
                <div style="font-weight:600;color:#a5b4fc;margin-top:6px;">Smart Snapshot</div>
                <div style="font-size:12px;color:#94a3b8;margin-top:4px;">Instant executive summary</div>
            </div>
            <div style="background:rgba(255,255,255,0.07);border:1px solid rgba(139,92,246,0.3);
                        border-radius:14px;padding:1.2rem 1.6rem;min-width:160px;
                        backdrop-filter:blur(8px);">
                <div style="font-size:1.8rem;">🤖</div>
                <div style="font-weight:600;color:#a5b4fc;margin-top:6px;">AI Assistant</div>
                <div style="font-size:12px;color:#94a3b8;margin-top:4px;">Ask questions in plain English</div>
            </div>
            <div style="background:rgba(255,255,255,0.07);border:1px solid rgba(139,92,246,0.3);
                        border-radius:14px;padding:1.2rem 1.6rem;min-width:160px;
                        backdrop-filter:blur(8px);">
                <div style="font-size:1.8rem;">📄</div>
                <div style="font-weight:600;color:#a5b4fc;margin-top:6px;">PDF Reports</div>
                <div style="font-size:12px;color:#94a3b8;margin-top:4px;">Export for stakeholders</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
