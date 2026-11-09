
import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "yottaflex.db"

st.set_page_config(
    page_title="YottaFlex Production Scheduler",
    page_icon="🏭",
    layout="wide"
)

st.title("🏭 YottaFlex Production Scheduler")
st.caption("Production Planning and Scheduling Dashboard")

@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)

    scheduled = pd.read_sql_query(
        "SELECT * FROM ScheduledOperationResult", conn
    )

    unscheduled = pd.read_sql_query(
        "SELECT * FROM UnscheduledOperationResult", conn
    )

    conn.close()
    return scheduled, unscheduled


def show_table(df, title, limit=30):
    st.subheader(title)

    if df.empty:
        st.info("No records available.")
        return

    # Display records as Markdown, avoiding dataframe components.
    columns = list(df.columns)
    display_df = df.head(limit).fillna("")

    lines = [
        "| " + " | ".join(str(c) for c in columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |"
    ]

    for _, row in display_df.iterrows():
        values = [
            str(row[c]).replace("|", "/").replace("\n", " ")
            for c in columns
        ]
        lines.append("| " + " | ".join(values) + " |")

    st.markdown("\n".join(lines))

    if len(df) > limit:
        st.caption(
            f"Showing first {limit} of {len(df)} records."
        )


try:
    scheduled, unscheduled = load_data()

except Exception as error:
    st.error(f"Database loading error: {error}")
    st.stop()

# KPI metrics
scheduled_count = len(scheduled)
unscheduled_count = len(unscheduled)
total = scheduled_count + unscheduled_count

rate = scheduled_count / total * 100 if total else 0

st.header("Scheduling Summary")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Operations", total)
c2.metric("Scheduled", scheduled_count)
c3.metric("Unscheduled", unscheduled_count)
c4.metric("Scheduling Rate", f"{rate:.2f}%")

st.divider()

# Scheduling progress
st.subheader("Scheduling Progress")
st.write(f"Scheduled: {rate:.2f}%")
st.progress(rate / 100)

st.write(
    f"Unscheduled: "
    f"{100 - rate:.2f}%"
)

st.divider()

# Unscheduled reasons
st.header("Unscheduled Analysis")

if "reason" in unscheduled.columns and not unscheduled.empty:
    reasons = unscheduled["reason"].value_counts()

    for reason, count in reasons.items():
        st.write(f"**{reason}:** {count}")

else:
    st.info("No unscheduled reasons available.")

st.divider()

# Results
show_table(
    scheduled,
    "Scheduled Operations",
    limit=30
)

st.divider()

show_table(
    unscheduled,
    "Unscheduled Operations",
    limit=30
)

st.divider()

# CSV downloads
st.header("Download Reports")

c1, c2 = st.columns(2)

with c1:
    st.download_button(
        "Download Scheduled CSV",
        scheduled.to_csv(index=False).encode("utf-8"),
        "operation_schedule.csv",
        "text/csv"
    )

with c2:
    st.download_button(
        "Download Unscheduled CSV",
        unscheduled.to_csv(index=False).encode("utf-8"),
        "unscheduled_operations.csv",
        "text/csv"
    )

st.divider()

st.success("YottaFlex Dashboard Loaded Successfully!")

st.caption("YottaFlex Production Scheduler | 2026")
