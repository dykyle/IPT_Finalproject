# main.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MultipleLocator
from datetime import date, datetime
import calendar
import math
import io
from scipy import stats

# --------------------------
# Page config & CSS (premium dark)
# --------------------------
st.set_page_config(page_title="Smart Budget Dashboard", layout="wide", initial_sidebar_state="expanded")

PREMIUM_CSS = """
/* App background - premium gradient */
[data-testid='stAppViewContainer'] {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
  color-scheme: dark;
}

/* Main content card - glass morphism */
[data-testid='stMain'] {
  background: rgba(30, 41, 59, 0.85);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 20px 24px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
  margin: 8px;
  color: #f8fafc;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
}

/* Sidebar - enhanced glass */
[data-testid='stSidebar'] {
  background: linear-gradient(180deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.03) 100%);
  backdrop-filter: blur(16px);
  border-radius: 16px;
  padding: 16px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  box-shadow: 0 12px 40px rgba(0,0,0,0.35);
}

/* Premium buttons with gradient */
div.stButton > button, .stDownloadButton>button {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
  color: white !important;
  border: none;
  padding: 12px 16px;
  border-radius: 12px;
  font-weight: 600;
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  width: 100%;
  position: relative;
  overflow: hidden;
}

div.stButton > button::before, .stDownloadButton>button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  transition: left 0.5s;
}

div.stButton > button:hover::before, .stDownloadButton>button:hover::before {
  left: 100%;
}

div.stButton > button:hover, .stDownloadButton>button:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 40px rgba(99, 102, 241, 0.4);
}

/* Secondary buttons */
div.stButton > button[kind="secondary"] {
  background: linear-gradient(135deg, #475569 0%, #64748b 100%);
}

/* File uploader - premium style */
div[data-testid='stFileUploader'] > label {
  border: 2px dashed rgba(99, 102, 241, 0.4);
  padding: 20px;
  border-radius: 12px;
  background: rgba(99, 102, 241, 0.05);
  display: block;
  transition: all 0.3s ease;
  text-align: center;
}

div[data-testid='stFileUploader'] > label:hover {
  background: rgba(99, 102, 241, 0.1);
  border-color: rgba(99, 102, 241, 0.7);
  transform: translateY(-2px);
}

/* Number input styling */
.stNumberInput input {
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 8px !important;
  color: white !important;
}

/* Selectbox styling */
.stSelectbox div[data-baseweb="select"] {
  background: rgba(255, 255, 255, 0.05) !important;
  border-radius: 8px !important;
}

/* Dataframes - premium */
.css-1d391kg, .stDataFrameContainer {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

/* Metrics cards */
[data-testid="metric-container"] {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 16px;
}

/* Tabs - premium */
.stTabs [role="tab"] {
  background: rgba(255,255,255,0.02) !important;
  border-radius: 10px;
  padding: 10px 16px;
  color: #e6eef6 !important;
  margin: 4px;
  border: 1px solid transparent;
  transition: all 0.3s ease;
}

.stTabs [role="tab"][data-selected="true"] {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%) !important;
  border-color: rgba(99, 102, 241, 0.4);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.2);
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: rgba(99, 102, 241, 0.5);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(99, 102, 241, 0.7);
}

/* Headers with gradient text */
.gradient-text {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Status indicators */
.status-positive { color: #10b981; font-weight: 600; }
.status-warning { color: #f59e0b; font-weight: 600; }
.status-negative { color: #ef4444; font-weight: 600; }

/* Loading animation */
@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.loading-pulse {
  animation: pulse 2s infinite;
}
"""

st.markdown(f"<style>{PREMIUM_CSS}</style>", unsafe_allow_html=True)

# --------------------------
# Enhanced helper functions
# --------------------------
def sanitize_records(records):
    """Return a cleaned DataFrame from records list/dict with enhanced validation."""
    if not records:
        return pd.DataFrame(columns=["Date", "Expense Label", "Expense Amount", "Category"])
    
    df = pd.DataFrame(records)
    
    # Ensure required columns exist
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.normalize()
    else:
        df["Date"] = pd.NaT
        
    if "Expense Amount" in df.columns:
        df["Expense Amount"] = pd.to_numeric(df["Expense Amount"], errors="coerce").fillna(0.0)
    else:
        df["Expense Amount"] = 0.0
        
    if "Expense Label" not in df.columns:
        df["Expense Label"] = "No Label"
        
    if "Category" not in df.columns:
        df["Category"] = "Uncategorized"

    # Enhanced filtering
    df = df[~df["Date"].isna()].copy()
    today = pd.Timestamp.today()
    df = df[df["Date"].between("2018-01-01", today)]
    
    # Remove extreme outliers (beyond 3 standard deviations)
    if len(df) > 5:
        amount_std = df["Expense Amount"].std()
        amount_mean = df["Expense Amount"].mean()
        if amount_std > 0:
            df = df[np.abs(df["Expense Amount"] - amount_mean) <= (3 * amount_std)]
    
    return df.reset_index(drop=True)

def limit_date_range(df, days_limit=120):
    """Limit dataframe to recent dates with smart detection."""
    if df.empty:
        return df
        
    span = (df["Date"].max() - df["Date"].min()).days
    if span > days_limit:
        st.warning(f"📅 Date range too wide ({span} days). Showing last {days_limit} days only.")
        cutoff = df["Date"].max() - pd.Timedelta(days=days_limit)
        return df[df["Date"] > cutoff].copy().reset_index(drop=True)
    return df

def create_spending_metrics(df, daily_allowance):
    """Create comprehensive spending metrics."""
    if df.empty:
        return {}
        
    total_spent = df["Expense Amount"].sum()
    avg_daily_spend = df.groupby("Date")["Expense Amount"].sum().mean()
    max_daily_spend = df.groupby("Date")["Expense Amount"].sum().max()
    total_days = df["Date"].nunique()
    
    # Savings calculation
    total_allowance = total_days * daily_allowance
    total_savings = total_allowance - total_spent
    savings_rate = (total_savings / total_allowance * 100) if total_allowance > 0 else 0
    
    # Spending patterns
    category_breakdown = df.groupby("Category")["Expense Amount"].sum().sort_values(ascending=False)
    top_category = category_breakdown.index[0] if not category_breakdown.empty else "None"
    
    return {
        "total_spent": total_spent,
        "avg_daily_spend": avg_daily_spend,
        "max_daily_spend": max_daily_spend,
        "total_savings": total_savings,
        "savings_rate": savings_rate,
        "top_category": top_category,
        "total_days": total_days
    }

# --------------------------
# Enhanced session state
# --------------------------
if "records" not in st.session_state:
    st.session_state.records = []
if "history" not in st.session_state:
    st.session_state.history = []
if "redo_stack" not in st.session_state:
    st.session_state.redo_stack = []
if "page" not in st.session_state:
    st.session_state.page = "tracker"
if "categories" not in st.session_state:
    st.session_state.categories = ["Food", "Transport", "Entertainment", "Shopping", "Bills", "Healthcare", "Other"]

# --------------------------
# Premium Sidebar
# --------------------------
with st.sidebar:
    st.markdown("<h1 class='gradient-text'>💎 Smart Budget</h1>", unsafe_allow_html=True)
    st.markdown("<div class='header-muted'>Premium Financial Dashboard</div>", unsafe_allow_html=True)
    
    # Navigation
    st.markdown("### 🧭 Navigation")
    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        if st.button("🏠 Tracker", use_container_width=True, 
                    type="primary" if st.session_state.page == "tracker" else "secondary"):
            st.session_state.page = "tracker"
    with nav_col2:
        if st.button("📊 Analyzer", use_container_width=True,
                    type="primary" if st.session_state.page == "analyzer" else "secondary"):
            st.session_state.page = "analyzer"

    st.markdown("---")
    
    # Allowance Setup
    st.markdown("### 💰 Allowance Setup")
    monthly_allowance = st.number_input("Monthly allowance (₱)", min_value=0.0, value=5000.0, step=100.0, 
                                       key="sidebar_monthly")
    
    col_year, col_month = st.columns(2)
    with col_year:
        year = st.number_input("Year", min_value=2020, max_value=2100, value=date.today().year, 
                              key="sidebar_year")
    with col_month:
        month = st.selectbox("Month", list(calendar.month_name)[1:], 
                            index=date.today().month - 1, key="sidebar_month")

    # Quick Stats
    if st.session_state.records:
        df_temp = sanitize_records(st.session_state.records)
        metrics = create_spending_metrics(df_temp, monthly_allowance / 20)  # Rough daily estimate
        st.markdown("### 📈 Quick Stats")
        st.metric("Total Spent", f"₱{metrics['total_spent']:,.0f}")
        st.metric("Savings Rate", f"{metrics['savings_rate']:.1f}%")

    st.markdown("---")
    
    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    
    if st.button("🔄 Reset All Data", use_container_width=True):
        st.session_state.records = []
        st.session_state.history = []
        st.session_state.redo_stack = []
        st.success("🎉 All data cleared!")
        
    uploaded_sidebar = st.file_uploader("📤 Upload CSV", type=["csv"], key="sidebar_upload",
                                       help="Upload your expense data")
    if uploaded_sidebar is not None:
        try:
            with st.spinner("🔄 Processing your data..."):
                preview = pd.read_csv(uploaded_sidebar, nrows=0)
                parsed = pd.read_csv(uploaded_sidebar, parse_dates=["Date"]) if "Date" in preview.columns else pd.read_csv(uploaded_sidebar)
                recs = parsed.to_dict("records")
                cleaned = sanitize_records(recs)
                st.session_state.history.append(st.session_state.records.copy())
                st.session_state.records = cleaned.to_dict("records")
            st.success("✅ Data loaded successfully!")
        except Exception as e:
            st.error(f"❌ Load failed: {e}")

    # Export current data
    if st.session_state.records:
        df_export = pd.DataFrame(st.session_state.records)
        csv_bytes = df_export.to_csv(index=False).encode("utf-8")
        st.download_button("💾 Export Data", csv_bytes, "financial_data.csv", "text/csv",
                          use_container_width=True)

# --------------------------
# Main content: Enhanced pages
# --------------------------

# ----- Page: Allowance Tracker -----
if st.session_state.page == "tracker":
    # Header with dynamic metrics
    st.markdown("<h1 class='gradient-text'>💳 Premium Allowance Tracker</h1>", unsafe_allow_html=True)
    
    month_num = list(calendar.month_name).index(month)
    month_range = pd.date_range(start=f"{year}-{month_num:02d}-01",
                                end=f"{year}-{month_num:02d}-{calendar.monthrange(year, month_num)[1]}",
                                freq="B")
    num_weekdays = len(month_range)
    daily_allowance = monthly_allowance / num_weekdays if num_weekdays else 0.0
    
    # Key metrics at the top
    if st.session_state.records:
        df_current = sanitize_records(st.session_state.records)
        metrics = create_spending_metrics(df_current, daily_allowance)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📅 Weekdays", num_weekdays, f"₱{daily_allowance:,.0f}/day")
        with col2:
            st.metric("💰 Total Spent", f"₱{metrics['total_spent']:,.0f}")
        with col3:
            status_class = "status-positive" if metrics['savings_rate'] >= 0 else "status-negative"
            st.metric("🎯 Savings Rate", f"{metrics['savings_rate']:.1f}%")
        with col4:
            st.metric("📊 Top Category", metrics['top_category'])

    st.markdown("---")

    # Enhanced Controls Section
    st.markdown("### 🛠️ Data Management")
    
    # Row 1: Full width upload
    uploaded = st.file_uploader(
        "**📤 Upload Expense CSV**", 
        type=["csv"], 
        key="tracker_upload",
        help="Upload CSV with columns: Date, Expense Label, Expense Amount, Category (optional)"
    )
    if uploaded is not None:
        try:
            with st.spinner("🔄 Processing your CSV..."):
                preview = pd.read_csv(uploaded, nrows=0)
                parsed = pd.read_csv(uploaded, parse_dates=["Date"]) if "Date" in preview.columns else pd.read_csv(uploaded)
                recs = parsed.to_dict("records")
                cleaned = sanitize_records(recs)
                st.session_state.history.append(st.session_state.records.copy())
                st.session_state.records = cleaned.to_dict("records")
            st.success("✅ CSV loaded successfully!")
        except Exception as e:
            st.error(f"❌ Load failed: {e}")

    # Row 2: 50/50 split for reset and download
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 Reset Data", use_container_width=True, type="secondary"):
            st.session_state.records = []
            st.session_state.history = []
            st.session_state.redo_stack = []
            st.success("🎉 Tracker cleared successfully!")
    with c2:
        if st.session_state.records:
            df_export = pd.DataFrame(st.session_state.records)
            csv_bytes = df_export.to_csv(index=False).encode("utf-8")
            st.download_button(
                "💾 Download CSV", 
                csv_bytes, 
                "financial_tracker.csv", 
                "text/csv", 
                use_container_width=True,
                key="download_top"
            )
        else:
            st.button("💾 Download CSV", disabled=True, use_container_width=True)

    st.markdown("---")

    # Enhanced Expense Input
    st.markdown("### ➕ Add New Expense")
    
    input_col1, input_col2, input_col3, input_col4 = st.columns([2, 3, 2, 2])
    with input_col1:
        expense_date = st.date_input("**Date**", value=date.today(), key="in_date")
    with input_col2:
        expense_label = st.text_input("**Description**", placeholder="Lunch, Transport, Shopping...", key="in_label")
    with input_col3:
        expense_amount = st.number_input("**Amount (₱)**", min_value=0.0, value=0.0, step=10.0, key="in_amount")
    with input_col4:
        expense_category = st.selectbox("**Category**", st.session_state.categories, key="in_category")

    # Action buttons with enhanced feedback
    btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([3, 1, 1, 1])
    last_action = None
    
    with btn_col1:
        if st.button("💰 Add Expense", use_container_width=True, type="primary"):
            if expense_amount <= 0:
                st.warning("⚠️ Please enter an amount greater than ₱0.")
            elif not expense_label.strip():
                st.warning("⚠️ Please enter a description.")
            else:
                st.session_state.history.append(st.session_state.records.copy())
                st.session_state.redo_stack.clear()
                st.session_state.records.append({
                    "Date": pd.to_datetime(expense_date),
                    "Expense Label": expense_label.strip(),
                    "Expense Amount": float(expense_amount),
                    "Category": expense_category
                })
                last_action = ("success", f"✅ Added: {expense_label} - ₱{expense_amount:,.2f}")
                
    with btn_col2:
        if st.button("↩️ Undo", use_container_width=True, 
                    disabled=not st.session_state.history) and st.session_state.history:
            st.session_state.redo_stack.append(st.session_state.records.copy())
            st.session_state.records = st.session_state.history.pop()
            last_action = ("warning", "↩️ Last action undone")
            
    with btn_col3:
        if st.button("↪️ Redo", use_container_width=True,
                    disabled=not st.session_state.redo_stack) and st.session_state.redo_stack:
            st.session_state.history.append(st.session_state.records.copy())
            st.session_state.records = st.session_state.redo_stack.pop()
            last_action = ("info", "↪️ Action redone")
            
    with btn_col4:
        if st.button("➕ Category", use_container_width=True):
            with st.form("new_category"):
                new_cat = st.text_input("New category name")
                if st.form_submit_button("Add"):
                    if new_cat and new_cat not in st.session_state.categories:
                        st.session_state.categories.append(new_cat)
                        st.success(f"✅ Added category: {new_cat}")

    if last_action:
        alert_type, message = last_action
        getattr(st, alert_type)(message)

    st.markdown("---")

    # Data Visualization & Analysis
    if st.session_state.records:
        with st.spinner("🔄 Crunching numbers..."):
            df = sanitize_records(st.session_state.records)
            df = limit_date_range(df, days_limit=120)

            # Enhanced Data Display
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📝 Expense Log", "📈 Analytics", "🔮 Forecast"])

            with tab1:
                # Spending Overview
                st.markdown("### 📊 Spending Overview")
                
                # Category breakdown
                category_totals = df.groupby("Category")["Expense Amount"].sum().sort_values(ascending=False)
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    # Category pie chart
                    fig1, ax1 = plt.subplots(figsize=(8, 6))
                    colors = plt.cm.Set3(np.linspace(0, 1, len(category_totals)))
                    wedges, texts, autotexts = ax1.pie(category_totals.values, labels=category_totals.index, 
                                                      autopct='%1.1f%%', colors=colors, startangle=90)
                    ax1.set_title('Spending by Category', color='white', fontsize=14, pad=20)
                    
                    # Improve text visibility
                    for text in texts:
                        text.set_color('white')
                        text.set_fontsize(10)
                    for autotext in autotexts:
                        autotext.set_color('white')
                        autotext.set_fontweight('bold')
                    
                    st.pyplot(fig1)

                with col2:
                    st.markdown("#### Category Breakdown")
                    for category, amount in category_totals.items():
                        percentage = (amount / category_totals.sum()) * 100
                        st.metric(category, f"₱{amount:,.0f}", f"{percentage:.1f}%")

            with tab2:
                st.markdown("### 📝 Detailed Expense Log")
                df_display = df.copy()
                df_display["Date"] = df_display["Date"].dt.strftime("%Y-%m-%d")
                df_display["Amount"] = df_display["Expense Amount"].map(lambda x: f"₱{x:,.2f}")
                st.dataframe(df_display[["Date", "Expense Label", "Category", "Amount"]], 
                           use_container_width=True, height=400)

            with tab3:
                st.markdown("### 📈 Advanced Analytics")
                
                # Daily trends
                daily_data = df.groupby("Date").agg({"Expense Amount": "sum"}).reset_index()
                full_dates = pd.date_range(start=daily_data["Date"].min(), end=daily_data["Date"].max(), freq="B")
                daily_data = daily_data.set_index("Date").reindex(full_dates, fill_value=0).rename_axis("Date").reset_index()
                daily_data["Daily Allowance"] = daily_allowance
                daily_data["Savings"] = daily_data["Daily Allowance"] - daily_data["Expense Amount"]
                
                # Enhanced chart
                fig2, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
                
                # Spending vs Allowance
                ax1.fill_between(daily_data["Date"], 0, daily_data["Expense Amount"], 
                               alpha=0.6, color="#ef4444", label="Expenses")
                ax1.fill_between(daily_data["Date"], daily_data["Expense Amount"], daily_data["Daily Allowance"],
                               alpha=0.6, color="#10b981", label="Savings")
                ax1.axhline(y=daily_allowance, color='yellow', linestyle='--', alpha=0.7, label="Daily Allowance")
                ax1.set_title("Daily Spending vs Allowance", color='white', fontsize=14)
                ax1.legend(facecolor='#1f2937', edgecolor='none', labelcolor='white')
                ax1.grid(alpha=0.2)
                
                # Cumulative savings
                daily_data["Cumulative Savings"] = daily_data["Savings"].cumsum()
                ax2.plot(daily_data["Date"], daily_data["Cumulative Savings"], 
                        color="#8b5cf6", linewidth=2.5, marker='o', markersize=3)
                ax2.fill_between(daily_data["Date"], 0, daily_data["Cumulative Savings"], 
                               alpha=0.3, color="#8b5cf6")
                ax2.set_title("Cumulative Savings Over Time", color='white', fontsize=14)
                ax2.grid(alpha=0.2)
                
                # Styling
                for ax in [ax1, ax2]:
                    ax.tick_params(colors='white')
                    ax.yaxis.label.set_color('white')
                    ax.xaxis.label.set_color('white')
                    ax.spines['bottom'].set_color('white')
                    ax.spines['top'].set_color('white') 
                    ax.spines['right'].set_color('white')
                    ax.spines['left'].set_color('white')
                
                plt.tight_layout()
                st.pyplot(fig2)

            with tab4:
                st.markdown("### 🔮 Smart Forecast")
                
                if len(daily_data) > 5:
                    # Enhanced forecasting with multiple methods
                    future_days = 7
                    
                    # Linear regression
                    x = np.arange(len(daily_data))
                    y = daily_data["Cumulative Savings"].values
                    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                    
                    future_x = np.arange(len(daily_data), len(daily_data) + future_days)
                    linear_forecast = slope * future_x + intercept
                    
                    # Simple moving average
                    window = min(5, len(y))
                    last_ma = np.mean(y[-window:])
                    ma_forecast = [last_ma + (slope * i) for i in range(1, future_days + 1)]
                    
                    # Plot forecasts
                    fig3, ax = plt.subplots(figsize=(12, 6))
                    
                    # Historical data
                    ax.plot(daily_data["Date"], y, label='Historical Savings', 
                           color='#10b981', linewidth=3, marker='o')
                    
                    # Forecasts
                    future_dates = pd.bdate_range(daily_data["Date"].iloc[-1] + pd.Timedelta(days=1), 
                                                periods=future_days)
                    ax.plot(future_dates, linear_forecast, label='Linear Forecast', 
                           color='#f59e0b', linestyle='--', marker='s')
                    ax.plot(future_dates, ma_forecast, label='Trend Forecast', 
                           color='#8b5cf6', linestyle='--', marker='^')
                    
                    ax.fill_between(future_dates, linear_forecast, ma_forecast, alpha=0.2, color='yellow')
                    
                    ax.set_title("Savings Forecast (Next 7 Days)", color='white', fontsize=14)
                    ax.legend(facecolor='#1f2937', edgecolor='none', labelcolor='white')
                    ax.grid(alpha=0.2)
                    ax.tick_params(colors='white')
                    
                    st.pyplot(fig3)
                    
                    # Forecast summary
                    forecast_df = pd.DataFrame({
                        "Date": future_dates.strftime("%Y-%m-%d"),
                        "Linear Forecast (₱)": linear_forecast,
                        "Trend Forecast (₱)": ma_forecast
                    })
                    st.dataframe(forecast_df.style.format({
                        "Linear Forecast (₱)": "₱{:,.2f}",
                        "Trend Forecast (₱)": "₱{:,.2f}"
                    }), use_container_width=True)
                else:
                    st.info("📊 Need more data (at least 5 days) for accurate forecasting.")

    else:
        # Empty state with guidance
        st.markdown("""
        <div style='text-align: center; padding: 40px; background: rgba(255,255,255,0.03); border-radius: 12px;'>
            <h3 style='color: #cbd5e1; margin-bottom: 20px;'>🚀 Ready to Start Tracking?</h3>
            <p style='color: #94a3b8; margin-bottom: 30px;'>
                Add your first expense above or upload a CSV file to begin your financial journey!
            </p>
        </div>
        """, unsafe_allow_html=True)

# ----- Page: Enhanced CSV Analyzer -----
elif st.session_state.page == "analyzer":
    st.markdown("<h1 class='gradient-text'>📊 Advanced CSV Analyzer</h1>", unsafe_allow_html=True)
    st.markdown("Upload any CSV file for powerful data analysis and visualization")
    
    # Enhanced file upload with drag & drop styling
    uploaded = st.file_uploader("Drag & drop your CSV file here", type=["csv"], 
                               key="flex_upload", help="Supports any CSV format with automatic column detection")
    
    if uploaded is not None:
        try:
            with st.spinner("🔍 Analyzing your data..."):
                df_any = pd.read_csv(uploaded)
                
            # Enhanced data preview
            st.success(f"✅ Successfully loaded {len(df_any)} rows × {len(df_any.columns)} columns")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Rows", f"{len(df_any):,}")
            with col2:
                st.metric("Total Columns", len(df_any.columns))
            with col3:
                st.metric("Memory Usage", f"{df_any.memory_usage(deep=True).sum() / 1024 ** 2:.1f} MB")
            
            # Data preview with tabs
            preview_tab1, preview_tab2, preview_tab3 = st.tabs(["📋 Data Preview", "🔍 Column Info", "📈 Basic Stats"])
            
            with preview_tab1:
                st.dataframe(df_any.head(10), use_container_width=True)
                
            with preview_tab2:
                col_info = pd.DataFrame({
                    'Column': df_any.columns,
                    'Data Type': df_any.dtypes.values,
                    'Non-Null Count': df_any.notna().sum().values,
                    'Null Count': df_any.isna().sum().values,
                    'Unique Values': [df_any[col].nunique() for col in df_any.columns]
                })
                st.dataframe(col_info, use_container_width=True)
                
            with preview_tab3:
                st.write(df_any.describe())
            
            # Enhanced analysis section
            st.markdown("---")
            st.markdown("### 🎯 Advanced Analysis")
            
            # Automatic column detection
            date_candidates = [col for col in df_any.columns 
                             if pd.to_datetime(df_any[col], errors='coerce').notna().any()]
            numeric_candidates = df_any.select_dtypes(include=[np.number]).columns.tolist()
            
            analysis_col1, analysis_col2 = st.columns(2)
            
            with analysis_col1:
                date_col = st.selectbox("📅 Date Column (for time series)", 
                                      options=['None'] + date_candidates if date_candidates else ['None'],
                                      index=0)
                
            with analysis_col2:
                value_col = st.selectbox("💰 Value Column (to analyze)", 
                                       options=['None'] + numeric_candidates if numeric_candidates else ['None'],
                                       index=0)
            
            if value_col != 'None' and date_col != 'None':
                # Enhanced time series analysis
                try:
                    analysis_df = df_any[[date_col, value_col]].copy()
                    analysis_df[date_col] = pd.to_datetime(analysis_df[date_col], errors='coerce')
                    analysis_df = analysis_df.dropna()
                    
                    if not analysis_df.empty:
                        st.markdown("#### 📈 Time Series Analysis")
                        
                        # Interactive chart
                        fig, ax = plt.subplots(figsize=(12, 6))
                        ax.plot(analysis_df[date_col], analysis_df[value_col], 
                               marker='o', linewidth=2, markersize=4, color='#6366f1')
                        ax.set_title(f"Time Series: {value_col} over Time", color='white', fontsize=14)
                        ax.grid(alpha=0.3)
                        ax.tick_params(colors='white')
                        plt.xticks(rotation=45)
                        st.pyplot(fig)
                        
                        # Statistical insights
                        st.markdown("#### 📊 Statistical Insights")
                        insights_col1, insights_col2, insights_col3 = st.columns(3)
                        
                        with insights_col1:
                            st.metric("Mean", f"{analysis_df[value_col].mean():.2f}")
                            st.metric("Median", f"{analysis_df[value_col].median():.2f}")
                            
                        with insights_col2:
                            st.metric("Std Dev", f"{analysis_df[value_col].std():.2f}")
                            st.metric("Variance", f"{analysis_df[value_col].var():.2f}")
                            
                        with insights_col3:
                            st.metric("Min", f"{analysis_df[value_col].min():.2f}")
                            st.metric("Max", f"{analysis_df[value_col].max():.2f}")
                
                except Exception as e:
                    st.error(f"Analysis error: {e}")
            
            # Export processed data
            st.markdown("---")
            st.markdown("### 💾 Export Results")
            processed_csv = df_any.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Processed Data", processed_csv, 
                             "analyzed_data.csv", "text/csv", use_container_width=True)
                
        except Exception as e:
            st.error(f"❌ Failed to process CSV: {e}")
    else:
        # Analyzer empty state
        st.markdown("""
        <div style='text-align: center; padding: 60px; background: rgba(255,255,255,0.03); border-radius: 12px;'>
            <h3 style='color: #cbd5e1; margin-bottom: 20px;'>📂 Upload Your Data</h3>
            <p style='color: #94a3b8; margin-bottom: 30px;'>
                Drag and drop any CSV file to unlock powerful analysis features including:<br>
                • Automatic column detection • Time series analysis • Statistical insights • Data visualization
            </p>
        </div>
        """, unsafe_allow_html=True)

# --------------------------
# Enhanced Footer
# --------------------------
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns([2, 1, 1])
with footer_col1:
    st.caption("💎 **Premium Financial Dashboard** • Built with Streamlit • Your data never leaves your browser")
with footer_col2:
    st.caption("🔄 Real-time processing")
with footer_col3:
    st.caption("🔒 Privacy first")