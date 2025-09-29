# app.py
import io
from pathlib import Path
from typing import List, Tuple, Optional

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# ---------- Page config & basic theme ----------
st.set_page_config(
    page_title="Scatter Plotter",
    page_icon="📈",
    layout="centered",
)

# Optional logo (put your file at assets/logo.png)
LOGO = Path("assets/logo.png")

# ---------- Helper functions ----------
def parse_numeric(value) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    Return (ok, number|None, reason|None).
    Reasons: empty | non-numeric | zero
    """
    if pd.isna(value):
        return False, None, "empty"
    try:
        num = float(str(value).strip())
    except ValueError:
        return False, None, "non-numeric"
    if num == 0:
        return False, None, "zero"
    return True, num, None

def validate_and_prepare(df: pd.DataFrame) -> Tuple[int, int, Optional[int]]:
    """
    Validate CSV-level rules and return column indices.
    Requires 'inputs' and 'outputs'; 'labels' is optional.
    Raises ValueError with clear messages.
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError("The uploaded file could not be read as a CSV.")

    cols = list(df.columns)
    if "inputs" not in cols or "outputs" not in cols:
        raise ValueError("The CSV must contain header columns named exactly 'inputs' and 'outputs'.")

    if df.shape[0] == 0:
        raise ValueError("The CSV has the required columns but contains no records.")

    ix_in = cols.index("inputs")
    ix_out = cols.index("outputs")
    ix_label = cols.index("labels") if "labels" in cols else None
    return ix_in, ix_out, ix_label

# ---------- Branding / styling (Parts 1–3) ----------
# Theme variables with fallbacks (so CSS adapts to light/dark)
primary = st.get_option("theme.primaryColor") or "#0F766E"
secondary_bg = st.get_option("theme.secondaryBackgroundColor") or "#F6F8FA"

st.markdown(
    f"""
    <style>
      :root {{
        --primary-color: {primary};
        --secondary-background-color: {secondary_bg};
      }}
      .hero {{
        padding: 1.25rem 1.25rem;
        border-radius: 14px;
        background: none;
        border: 1px solid rgba(128,24,135,0.06);
        margin-bottom: 1rem;
      }}
      .badge {{
        display:inline-block; padding: 4px 10px; border-radius: 999px;
        background: var(--primary-color); color: white; font-size: 12px;
        margin-bottom: 6px;
      }}
      .hero h1 {{ margin: 0.2rem 0 0.4rem 0; }}
      .hero p {{ margin: 0; opacity: 0.75; }}
    </style>
    """,
    unsafe_allow_html=True,
)

if LOGO.exists():
    st.image(str(LOGO), width=180)

st.markdown(
    """
    <div class="hero">
      <span class="badge">CSV → Scatter</span>
      <h1>Scatter Plotter</h1>
      <p>Upload a <strong>.csv</strong> with <code>inputs</code>, <code>outputs</code>, and
      optional <code>labels</code>. We’ll validate, plot, and let you download the figure.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("About")
    st.write(
        "This tool validates your CSV and plots **inputs vs outputs**.\n\n"
        "• Required columns: `inputs`, `outputs`\n"
        "• Optional: `labels`\n"
        "• Skips empty, zero, or non-numeric rows"
    )
    st.divider()
    st.caption("© 2025 Your Lab / Dept • v1.0")

# ---------- Main UI ----------
uploaded = st.file_uploader("Choose CSV file", type=["csv"])

if not uploaded:
    st.info("Awaiting upload…")
    st.stop()

# Read CSV safely
try:
    df = pd.read_csv(uploaded)
except Exception:
    st.error("The file is not a valid .csv (parse error).")
    st.stop()

# Validate structure
try:
    ix_in, ix_out, ix_label = validate_and_prepare(df)
except ValueError as e:
    st.error(str(e))
    st.stop()

# ---------- Process rows ----------
total_records = int(df.shape[0])  # header is implicit, so records = number of rows
x_vals: List[float] = []
y_vals: List[float] = []
skipped: List[Tuple[int, str, List[str]]] = []  # (row_number, label, reasons)

for i, row in df.iterrows():
    # Spreadsheet-friendly row numbers: header row is 1 → first data row is 2
    row_number = i + 2
    label = ""
    if ix_label is not None:
        maybe = row.iloc[ix_label]
        if pd.notna(maybe):
            label = str(maybe).strip()

    in_ok, in_num, in_reason = parse_numeric(row.iloc[ix_in])
    out_ok, out_num, out_reason = parse_numeric(row.iloc[ix_out])

    if in_ok and out_ok:
        x_vals.append(in_num)  # type: ignore[arg-type]
        y_vals.append(out_num)  # type: ignore[arg-type]
    else:
        reasons = []
        if not in_ok:
            reasons.append(f"inputs is {in_reason}")
        if not out_ok:
            reasons.append(f"outputs is {out_reason}")
        skipped.append((row_number, label, reasons))

plotted_count = len(x_vals)
skipped_count = len(skipped)

# ---------- Metric cards (Part 5 replaces st.metric) ----------
c1, c2, c3 = st.columns(3)
for c, title, value in [
    (c1, "Records", total_records),
    (c2, "Plotted", plotted_count),
    (c3, "Skipped", skipped_count),
]:
    with c:
        st.markdown(
            f"""
            <div style="border:1px solid rgba(0,0,0,0.06); padding:12px; border-radius:12px;
                        background: var(--secondary-background-color); text-align:center;">
              <div style="font-size:12px; opacity:.7;">{title}</div>
              <div style="font-size:24px; font-weight:700;">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---------- Tabs for plot vs details (Part 4 replaces the old plot+list block) ----------
st.divider()
tab_plot, tab_details = st.tabs(["📊 Plot", "🧾 Details"])

with tab_plot:
    st.subheader("Scatter plot")
    fig, ax = plt.subplots()
    ax.scatter(x_vals, y_vals)
    ax.set_xlabel("inputs")
    ax.set_ylabel("outputs")
    ax.set_title("Scatter Plot of inputs vs outputs")
    ax.grid(True)
    st.pyplot(fig, clear_figure=True)

    # Download PNG
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
    buf.seek(0)
    st.download_button("Download plot (PNG)", buf, file_name="output.png", mime="image/png")

with tab_details:
    st.subheader("Skipped records")
    if skipped_count:
        for row_number, label, reasons in skipped:
            reason_text = "; ".join(reasons)
            if label:
                st.write(f"• Record in row **{row_number}**, **{label}**: {reason_text}")
            else:
                st.write(f"• Record in row **{row_number}**: {reason_text}")
    else:
        st.write("No records skipped.")
