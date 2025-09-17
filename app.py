import io
from typing import List, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="CSV → Scatter", layout="centered")

TITLE = "Scatter Plotter (inputs → outputs)"

def parse_numeric(value) -> Tuple[bool, float | None, str | None]:
    """Return (ok, number|None, reason|None). Reasons: empty | non-numeric | zero."""
    if pd.isna(value):
        return False, None, "empty"
    try:
        num = float(str(value).strip())
    except ValueError:
        return False, None, "non-numeric"
    if num == 0:
        return False, None, "zero"
    return True, num, None

def validate_and_prepare(df: pd.DataFrame):
    """Validate CSV-level rules and prepare indices. Raises ValueError with clear messages."""
    if not isinstance(df, pd.DataFrame):
        raise ValueError("The uploaded file could not be read as a CSV.")
    cols = list(df.columns)

    if "inputs" not in cols or "outputs" not in cols:
        raise ValueError("The CSV must contain header columns named exactly 'inputs' and 'outputs'.")

    if df.shape[0] == 0:
        raise ValueError("The CSV has the required columns but contains no records.")

    ix_label = cols.index("labels") if "labels" in cols else None
    return cols.index("inputs"), cols.index("outputs"), ix_label

def main():
    st.title(TITLE)
    st.markdown("Upload a `.csv` with **inputs**, **outputs**, and optional **labels** columns.")

    uploaded = st.file_uploader("Choose CSV file", type=["csv"])
    if not uploaded:
        st.info("Awaiting upload…")
        return

    # Read CSV safely
    try:
        df = pd.read_csv(uploaded)
    except Exception:
        st.error("The file is not a valid .csv (parse error).")
        return

    try:
        ix_in, ix_out, ix_label = validate_and_prepare(df)
    except ValueError as e:
        st.error(str(e))
        return

    # Summaries
    total_records = int(df.shape[0])  # excludes header by definition

    x_vals, y_vals = [], []
    skipped: List[Tuple[int, str, List[str]]] = []

    # Iterate rows; keep spreadsheet-friendly row numbers (header would be row 1 → first data row = 2)
    for i, row in df.iterrows():
        row_number = i + 2
        label = ""
        if ix_label is not None:
            maybe = row.iloc[ix_label]
            if pd.notna(maybe):
                label = str(maybe).strip()

        in_ok, in_num, in_reason = parse_numeric(row.iloc[ix_in])
        out_ok, out_num, out_reason = parse_numeric(row.iloc[ix_out])

        if in_ok and out_ok:
            x_vals.append(in_num)
            y_vals.append(out_num)
        else:
            reasons = []
            if not in_ok: reasons.append(f"inputs is {in_reason}")
            if not out_ok: reasons.append(f"outputs is {out_reason}")
            skipped.append((row_number, label, reasons))

    plotted_count = len(x_vals)
    skipped_count = len(skipped)

    # Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Records (excluding header)", f"{total_records}")
    c2.metric("Records plotted", f"{plotted_count}")
    c3.metric("Records skipped", f"{skipped_count}")

    # Skipped details
    if skipped_count:
        st.subheader("Skipped records")
        for row_number, label, reasons in skipped:
            reason_text = "; ".join(reasons)
            if label:
                st.write(f"• Record in row **{row_number}**, **{label}**: {reason_text}")
            else:
                st.write(f"• Record in row **{row_number}**: {reason_text}")

    # Plot
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

if __name__ == "__main__":
    main()
