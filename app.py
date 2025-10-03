import io
from pathlib import Path
from typing import List, Tuple, Optional

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# ---------- Page config ----------
st.set_page_config(
    page_title="Scatter Plotter",
    page_icon="📈",
    layout="centered",
)

# ---------- Helpers ----------
def parse_numeric(value) -> Tuple[bool, Optional[float], Optional[str]]:
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

# ---------- Main UI ----------
uploaded = st.file_uploader("Choose CSV file", type=["csv"])
if not uploaded:
    st.info("Awaiting upload…")
    st.stop()

# Step 1: Load and validate
try:
    df = pd.read_csv(uploaded)
except Exception:
    st.error("The file is not a valid .csv (parse error).")
    st.stop()

try:
    ix_in, ix_out, ix_label = validate_and_prepare(df)
except ValueError as e:
    st.error(str(e))
    st.stop()

# Step 2: Process rows (count valid/invalid + prepare adj_outputs)
x_vals: List[float] = []
y_vals: List[float] = []
skipped: List[Tuple[int, str, List[str]]] = []

adj_outputs: List[Optional[float]] = []

for i, row in df.iterrows():
    row_number = i + 2  # header row = 1
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
        adj_outputs.append(out_num * 1.6)
    else:
        reasons = []
        if not in_ok:
            reasons.append(f"inputs is {in_reason}")
        if not out_ok:
            reasons.append(f"outputs is {out_reason}")
        skipped.append((row_number, label, reasons))
        # keep adj_outputs aligned with DataFrame
        adj_outputs.append(None)

df["adj_outputs"] = adj_outputs

valid_count = len(x_vals)
invalid_count = len(skipped)

# Step 3: Show metrics (as badges/cards)
c1, c2 = st.columns(2)
for c, title, value in [
    (c1, "Valid Rows", valid_count),
    (c2, "Invalid Rows", invalid_count),
]:
    with c:
        st.markdown(
            f"""
            <div style="border:0; padding:12px; border-radius:12px;
                        background: var(--primary-color, #0F766E);
                        color:white; text-align:center;">
              <div style="font-size:12px; opacity:.9;">{title}</div>
              <div style="font-size:24px; font-weight:800;">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# Step 4: Download updated CSV
csv_buf = io.BytesIO()
df.to_csv(csv_buf, index=False)
csv_buf.seek(0)
st.download_button(
    "Download updated CSV (with adj_outputs)",
    csv_buf,
    file_name="updated_with_adj_outputs.csv",
    mime="text/csv"
)

# Step 5: Proceed button
if st.button("Proceed to plotting"):
    st.subheader("Scatter plot (inputs vs outputs)")
    fig, ax = plt.subplots()
    ax.scatter(x_vals, y_vals)
    ax.set_xlabel("inputs")
    ax.set_ylabel("outputs")
    ax.set_title("Scatter Plot of inputs vs outputs")
    ax.grid(True)
    st.pyplot(fig, clear_figure=True)

    # Optionally: download the PNG
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
    buf.seek(0)
    st.download_button("Download plot (PNG)", buf, file_name="output.png", mime="image/png")
