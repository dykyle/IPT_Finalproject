# main.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MultipleLocator
from datetime import date
import calendar
import math

st.set_page_config(layout="centered")
st.title("💰 Allowance Tracker & Forecasting")

# --- CSS for bigger rounded buttons ---
st.markdown(
    """
    <style>
    div.stButton > button {
        height: 60px;
        min-width: 100%;
        font-size: 18px;
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Step 1: Monthly Allowance Input ---
monthly_allowance = st.number_input(
    "Enter your monthly allowance (₱):", min_value=0.0, value=5000.0, step=100.0
)

year = st.number_input("Select Year:", min_value=2020, max_value=2100, value=date.today().year)
month = st.selectbox("Select Month:", list(calendar.month_name)[1:], index=date.today().month - 1)
month_num = list(calendar.month_name).index(month)

# Count weekdays (Mon-Fri) for this month
month_range = pd.date_range(
    start=f"{year}-{month_num:02d}-01",
    end=f"{year}-{month_num:02d}-{calendar.monthrange(year, month_num)[1]}",
    freq="B"
)
num_weekdays = len(month_range)
daily_allowance = monthly_allowance / num_weekdays if num_weekdays > 0 else 0

st.markdown(
    f"📅 **{calendar.month_name[month_num]} {year}:** {num_weekdays} weekdays → "
    f"Daily allowance = ₱{daily_allowance:,.2f}"
)

# --- Step 2: Expense Entry ---
st.subheader("Add Daily Expense")
expense_date = st.date_input("Date of expense:", value=date.today())
expense_label = st.text_input("Expense label (e.g., Food, Transport):")
expense_amount = st.number_input("Expense amount (₱):", min_value=0.0, value=0.0, step=10.0)

# --- Initialize session state ---
if "records" not in st.session_state:
    st.session_state.records = []
if "history" not in st.session_state:
    st.session_state.history = []
if "redo_stack" not in st.session_state:
    st.session_state.redo_stack = []

# --- Buttons row with Undo/Redo ---
col1, col2, col3 = st.columns([2, 1, 1])
last_alert = None

with col1:
    if st.button("➕ Add Expense Record", use_container_width=True):
        st.session_state.history.append(st.session_state.records.copy())
        st.session_state.redo_stack.clear()
        st.session_state.records.append(
            {
                "Date": pd.to_datetime(expense_date),
                "Expense Label": expense_label.strip() or "No Label",
                "Expense Amount": float(expense_amount),
            }
        )
        last_alert = ("success", f"Added: {expense_label or 'No Label'} - Expense ₱{expense_amount:.2f}")

with col2:
    if st.button("↩️ Undo", use_container_width=True) and st.session_state.history:
        st.session_state.redo_stack.append(st.session_state.records.copy())
        st.session_state.records = st.session_state.history.pop()
        last_alert = ("warning", "Last action undone.")

with col3:
    if st.button("↪️ Redo", use_container_width=True) and st.session_state.redo_stack:
        st.session_state.history.append(st.session_state.records.copy())
        st.session_state.records = st.session_state.redo_stack.pop()
        last_alert = ("info", "Action redone.")

st.markdown("---")

# --- Show alert below buttons ---
if last_alert:
    type_, msg = last_alert
    if type_ == "success":
        st.success(msg)
    elif type_ == "warning":
        st.warning(msg)
    elif type_ == "info":
        st.info(msg)

# --- Step 3: Build dataframe and daily summary ---
if st.session_state.records:
    df = pd.DataFrame(st.session_state.records)
    df["Date"] = pd.to_datetime(df["Date"]).dt.normalize()

    with st.expander("📝 Raw Expense Log (all entries)"):
        df_display = df.copy()
        df_display["Date"] = df_display["Date"].dt.strftime("%Y-%m-%d")
        df_display["Expense Amount"] = df_display["Expense Amount"].map(lambda x: f"₱{x:,.2f}")
        st.dataframe(df_display, use_container_width=True)

    grouped = df.groupby("Date").agg({"Expense Amount": "sum"}).reset_index()

    full_dates = pd.date_range(
        start=grouped["Date"].min(),
        end=grouped["Date"].max(),
        freq="B"
    )

    grouped = (
        grouped.set_index("Date")
        .reindex(full_dates, fill_value=0)
        .rename_axis("Date")
        .reset_index()
    )

    grouped["Daily Allowance"] = daily_allowance
    grouped["Savings"] = grouped["Daily Allowance"] - grouped["Expense Amount"]

    grouped_display = grouped.copy()
    grouped_display["Date"] = grouped_display["Date"].dt.strftime("%Y-%m-%d")
    grouped_display["Expense Amount"] = grouped_display["Expense Amount"].map(lambda x: f"₱{x:,.2f}")
    grouped_display["Daily Allowance"] = grouped_display["Daily Allowance"].map(lambda x: f"₱{x:,.2f}")
    grouped_display["Savings"] = grouped_display["Savings"].map(lambda x: f"₱{x:,.2f}")

    st.subheader("📊 Daily Summary (Weekdays Only)")
    st.dataframe(grouped_display, use_container_width=True)

    # --- Y-axis step dynamically ---
    if daily_allowance <= 250:
        step = 10
    elif daily_allowance <= 500:
        step = 20
    else:
        step = 25

    max_data_val = max(
        grouped["Expense Amount"].max(),
        grouped["Savings"].max(),
        daily_allowance,
    )
    ymax = max(math.ceil(max_data_val / step) * step, step)

    # --- Step 4: Graphs ---
    st.subheader("📉 Expenses & Savings Over Time")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(grouped["Date"], grouped["Expense Amount"], marker="o", label="Expenses", color="#d62728")
    ax.plot(grouped["Date"], grouped["Savings"], marker="o", label="Savings", color="#2ca02c")

    ax.set_xlabel("Date")
    ax.set_ylabel("Amount (₱)")
    ax.set_title("Expenses vs Savings (Weekdays Only)")
    ax.legend(loc="upper right")

    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
    fig.autofmt_xdate(rotation=90)

    ax.yaxis.set_major_locator(MultipleLocator(step))
    ax.set_ylim(bottom=0, top=ymax)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    st.pyplot(fig)

    # --- Step 5: Forecast ---
    st.subheader("🔮 Savings Forecast (Next 5 Weekdays)")
    if len(grouped) > 1:
        forecast_days = 5
        avg_saving = grouped["Savings"].mean()

        future_dates = pd.date_range(
            start=grouped["Date"].iloc[-1] + pd.Timedelta(days=1),
            periods=forecast_days * 2,
            freq="B"
        )[:forecast_days]

        forecast_savings = [avg_saving] * forecast_days
        forecast_df = pd.DataFrame({"Date": future_dates, "Forecast Savings": forecast_savings})

        max_future = max(forecast_df["Forecast Savings"].max(), 0)
        ymax2_candidate = max(max_data_val, max_future, daily_allowance)
        ymax2 = math.ceil(ymax2_candidate / step) * step

        fig2, ax2 = plt.subplots(figsize=(9, 5))
        ax2.plot(grouped["Date"], grouped["Savings"], marker="o", label="Actual Savings", color="#2ca02c")
        ax2.plot(forecast_df["Date"], forecast_df["Forecast Savings"], marker="x", linestyle="--", label="Forecasted Savings", color="#ff7f0e")

        ax2.set_xlabel("Date")
        ax2.set_ylabel("Amount (₱)")
        ax2.set_title("Savings Forecast (Next 5 Weekdays)")
        ax2.legend()

        ax2.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        fig2.autofmt_xdate(rotation=90)

        ax2.yaxis.set_major_locator(MultipleLocator(step))
        ax2.set_ylim(bottom=0, top=ymax2)
        ax2.grid(axis="y", linestyle="--", alpha=0.4)

        st.dataframe(
            pd.DataFrame({
                "Date": forecast_df["Date"].dt.strftime("%Y-%m-%d"),
                "Predicted Savings (₱)": forecast_df["Forecast Savings"].map(lambda x: f"₱{x:,.2f}")
            }),
            use_container_width=True
        )

        st.pyplot(fig2)
    else:
        st.info("Not enough data for forecasting. Add more expenses (at least 2 days) to enable forecast.")

else:
    st.info("No expense records yet. Add some expenses to see summary, charts, and forecast.")
