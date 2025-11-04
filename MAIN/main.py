import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import date, datetime
import calendar
import math
import io
import json
import os
from scipy import stats

def load_data():
    try:
        if os.path.exists('user_data.json'):
            with open('user_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                for record in data.get("records", []):
                    if "Date" in record:
                        record["Date"] = pd.to_datetime(record["Date"])
                return data
    except Exception as e:
        st.error(f"Error loading saved data: {e}")
    return {
        "records": [],
        "categories": ["Food", "Transport", "Entertainment", "Shopping", "Bills", "Healthcare", "Other"]
    }

def save_data():
    try:
        data_to_save = {
            "records": st.session_state.records,
            "categories": st.session_state.categories
        }
        with open('user_data.json', 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, default=str)
    except Exception as e:
        st.error(f"Could not save data: {e}")

def save_data_silent():
    try:
        data_to_save = {
            "records": st.session_state.records,
            "categories": st.session_state.categories
        }
        with open('user_data.json', 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, default=str)
    except Exception:
        pass

def sanitize_records(records):
    if not records:
        return pd.DataFrame(columns=["Date", "Expense Label", "Expense Amount", "Category"])
    
    df = pd.DataFrame(records)
    
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

    df = df[~df["Date"].isna()].copy()
    today = pd.Timestamp.today()
    df = df[df["Date"].between("2018-01-01", today)]
    
    if len(df) > 5:
        amount_std = df["Expense Amount"].std()
        amount_mean = df["Expense Amount"].mean()
        if amount_std > 0:
            df = df[np.abs(df["Expense Amount"] - amount_mean) <= (3 * amount_std)]
    
    return df.reset_index(drop=True)

def limit_date_range(df, days_limit=120):
    if df.empty:
        return df
        
    span = (df["Date"].max() - df["Date"].min()).days
    if span > days_limit:
        st.warning(f"📅 Date range too wide ({span} days). Showing last {days_limit} days only.")
        cutoff = df["Date"].max() - pd.Timedelta(days=days_limit)
        return df[df["Date"] > cutoff].copy().reset_index(drop=True)
    return df

def create_spending_metrics(df, daily_allowance):
    if df.empty:
        return {}
        
    total_spent = df["Expense Amount"].sum()
    avg_daily_spend = df.groupby("Date")["Expense Amount"].sum().mean()
    max_daily_spend = df.groupby("Date")["Expense Amount"].sum().max()
    total_days = df["Date"].nunique()
    
    total_allowance = total_days * daily_allowance
    total_savings = total_allowance - total_spent
    savings_rate = (total_savings / total_allowance * 100) if total_allowance > 0 else 0
    
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

st.set_page_config(page_title="FourCast. - Smart Budget", layout="wide", initial_sidebar_state="expanded")

FOURCAST_CSS = """
[data-testid='stAppViewContainer'] {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
  color-scheme: dark;
}

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

[data-testid='stSidebar'] {
  background: linear-gradient(180deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.03) 100%);
  backdrop-filter: blur(16px);
  border-radius: 16px;
  padding: 16px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  box-shadow: 0 12px 40px rgba(0,0,0,0.35);
}

div.stButton > button, .stDownloadButton>button {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
  color: white !important;
  border: none;
  padding: 12px 16px;
  border-radius: 12px;
  font-weight: 600;
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.3);
  transition: all 0.1s ease;
  width: 100%;
}

div.stButton > button:hover, .stDownloadButton>button:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(99, 102, 241, 0.4);
}

div.stButton > button[kind="secondary"] {
  background: linear-gradient(135deg, #475569 0%, #64748b 100%);
}

div.stButton > button[kind="secondary"]:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(71, 85, 105, 0.4);
}

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

.stNumberInput input {
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 8px !important;
  color: white !important;
}

.stSelectbox div[data-baseweb="select"] {
  background: rgba(255, 255, 255, 0.05) !important;
  border-radius: 8px !important;
}

.css-1d391kg, .stDataFrameContainer {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

[data-testid="metric-container"] {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 16px;
}

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

.fourcast-gradient {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.st-emotion-cache-px2xcf h1,
[data-testid="stHeader"] h1,
div[data-testid="stVerticalBlock"] h1 {
    font-size: 48px !important;
    font-weight: 900 !important;
}

.status-positive { color: #10b981; font-weight: 600; }
.status-warning { color: #f59e0b; font-weight: 600; }
.status-negative { color: #ef4444; font-weight: 600; }
"""

st.markdown(f"<style>{FOURCAST_CSS}</style>", unsafe_allow_html=True)

if "records" not in st.session_state:
    saved_data = load_data()
    st.session_state.records = saved_data.get("records", [])
    st.session_state.categories = saved_data.get("categories", ["Food", "Transport", "Entertainment", "Shopping", "Bills", "Healthcare", "Other"])

if "history" not in st.session_state:
    st.session_state.history = []
if "redo_stack" not in st.session_state:
    st.session_state.redo_stack = []
if "page" not in st.session_state:
    st.session_state.page = "tracker"

with st.sidebar:
    st.markdown("<h1 class='fourcast-gradient'>FourCast.</h1>", unsafe_allow_html=True)
    st.markdown("<div class='header-muted'>Smart Budget Dashboard</div>", unsafe_allow_html=True)
    
    st.markdown("### 🧭 Navigation")
    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        tracker_active = st.session_state.page == "tracker"
        if st.button("🏠 Tracker", use_container_width=True, 
                    type="primary" if tracker_active else "secondary",
                    key="nav_tracker"):
            st.session_state.page = "tracker"
            st.rerun()
    with nav_col2:
        analyzer_active = st.session_state.page == "analyzer"
        if st.button("📊 Analyzer", use_container_width=True,
                    type="primary" if analyzer_active else "secondary",
                    key="nav_analyzer"):
            st.session_state.page = "analyzer"
            st.rerun()

    st.markdown("---")
    
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

    if st.session_state.records:
        df_temp = sanitize_records(st.session_state.records)
        metrics = create_spending_metrics(df_temp, monthly_allowance / 20)
        st.markdown("### 📈 Quick Stats")
        st.metric("Total Spent", f"₱{metrics['total_spent']:,.0f}")
        st.metric("Savings Rate", f"{metrics['savings_rate']:.1f}%")

    st.markdown("---")
    
    st.markdown("### ⚡ Quick Actions")
    
    if st.button("🔄 Reset All Data", use_container_width=True, key="reset_all"):
        st.session_state.records = []
        st.session_state.history = []
        st.session_state.redo_stack = []
        save_data()
        st.success("🎉 All data cleared!")
        st.rerun()
        
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
                save_data()
            st.success("✅ Data loaded successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Load failed: {e}")

    if st.session_state.records:
        df_export = pd.DataFrame(st.session_state.records)
        csv_bytes = df_export.to_csv(index=False).encode("utf-8")
        st.download_button("💾 Export Data", csv_bytes, "fourcast_data.csv", "text/csv",
                          use_container_width=True, key="export_data")

if st.session_state.page == "tracker":
    st.markdown("<h1 class='fourcast-gradient'>💳 FourCast. Budget Tracker</h1>", unsafe_allow_html=True)
    
    month_num = list(calendar.month_name).index(month)
    month_range = pd.date_range(start=f"{year}-{month_num:02d}-01",
                                end=f"{year}-{month_num:02d}-{calendar.monthrange(year, month_num)[1]}",
                                freq="B")
    num_weekdays = len(month_range)
    daily_allowance = monthly_allowance / num_weekdays if num_weekdays else 0.0
    
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

    st.markdown("### 🛠️ Data Management")
    
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
                save_data()
            st.success("✅ CSV loaded successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Load failed: {e}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 Reset Data", use_container_width=True, type="secondary", key="reset_tracker"):
            st.session_state.records = []
            st.session_state.history = []
            st.session_state.redo_stack = []
            save_data()
            st.success("🎉 Tracker cleared successfully!")
            st.rerun()
    with c2:
        if st.session_state.records:
            df_export = pd.DataFrame(st.session_state.records)
            csv_bytes = df_export.to_csv(index=False).encode("utf-8")
            st.download_button(
                "💾 Download CSV", 
                csv_bytes, 
                "fourcast_tracker.csv", 
                "text/csv", 
                use_container_width=True,
                key="download_top"
            )
        else:
            st.button("💾 Download CSV", disabled=True, use_container_width=True, key="disabled_download")

    st.markdown("---")

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

    btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([3, 1, 1, 1])
    last_action = None
    
    with btn_col1:
        if st.button("💰 Add Expense", use_container_width=True, type="primary", key="add_expense"):
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
                save_data()
                last_action = ("success", f"✅ Added: {expense_label} - ₱{expense_amount:,.2f}")
                st.rerun()
                
    with btn_col2:
        if st.button("↩️ Undo", use_container_width=True, 
                    disabled=not st.session_state.history, key="undo_btn") and st.session_state.history:
            st.session_state.redo_stack.append(st.session_state.records.copy())
            st.session_state.records = st.session_state.history.pop()
            save_data()
            last_action = ("warning", "↩️ Last action undone")
            st.rerun()
            
    with btn_col3:
        if st.button("↪️ Redo", use_container_width=True,
                    disabled=not st.session_state.redo_stack, key="redo_btn") and st.session_state.redo_stack:
            st.session_state.history.append(st.session_state.records.copy())
            st.session_state.records = st.session_state.redo_stack.pop()
            save_data()
            last_action = ("info", "↪️ Action redone")
            st.rerun()
            
    with btn_col4:
        if st.button("➕ Category", use_container_width=True, key="add_cat_btn"):
            with st.form("new_category"):
                new_cat = st.text_input("New category name", key="new_cat_input")
                if st.form_submit_button("Add", key="add_cat_submit"):
                    if new_cat and new_cat not in st.session_state.categories:
                        st.session_state.categories.append(new_cat)
                        save_data()
                        st.success(f"✅ Added category: {new_cat}")
                        st.rerun()

    if last_action:
        alert_type, message = last_action
        getattr(st, alert_type)(message)

    st.markdown("---")

    if st.session_state.records:
        with st.spinner("🔄 Crunching numbers..."):
            df = sanitize_records(st.session_state.records)
            df = limit_date_range(df, days_limit=120)

            tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📝 Expense Log", "📈 Analytics", "🔮 Forecast"])

            with tab1:
                st.markdown("### 📊 Spending Overview")
                
                category_totals = df.groupby("Category")["Expense Amount"].sum().sort_values(ascending=False)
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    fig1, ax1 = plt.subplots(figsize=(8, 6))
                    colors = plt.cm.Set3(np.linspace(0, 1, len(category_totals)))
                    wedges, texts, autotexts = ax1.pie(category_totals.values, labels=category_totals.index, 
                                                    autopct='%1.1f%%', colors=colors, startangle=90)
                    ax1.set_title('Spending by Category', color='white', fontsize=14, pad=20)
                    
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
                st.markdown("### 📝 Expense Logs & Summary")
                
                summary_tab1, summary_tab2 = st.tabs(["📊 Daily Summary", "📋 Detailed Log"])
                
                with summary_tab1:
                    st.markdown("#### 📅 Daily Spending Summary")
                    
                    daily_summary = df.groupby("Date").agg({
                        "Expense Amount": ["sum", "count"]
                    }).reset_index()
                    
                    daily_summary.columns = ["Date", "Total Spent", "Number of Expenses"]
                    
                    daily_summary["Daily Allowance"] = daily_allowance
                    daily_summary["Daily Savings"] = daily_summary["Daily Allowance"] - daily_summary["Total Spent"]
                    daily_summary["Status"] = daily_summary["Daily Savings"].apply(
                        lambda x: "✅ Under Budget" if x >= 0 else "❌ Over Budget"
                    )
                    
                    display_summary = daily_summary.copy()
                    display_summary["Date"] = display_summary["Date"].dt.strftime("%Y-%m-%d (%a)")
                    
                    st.dataframe(
                        display_summary[["Date", "Total Spent", "Number of Expenses", "Daily Savings", "Status"]].style.format({
                            "Total Spent": "₱{:,.2f}",
                            "Daily Savings": "₱{:,.2f}"
                        }),
                        use_container_width=True,
                        height=300
                    )
                    
                    st.markdown("#### 📈 Quick Stats")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        total_days = len(daily_summary)
                        st.metric("Days Tracked", total_days)
                        
                    with col2:
                        avg_daily_spend = daily_summary["Total Spent"].mean()
                        st.metric("Avg Daily Spend", f"₱{avg_daily_spend:,.0f}")
                        
                    with col3:
                        days_under_budget = (daily_summary["Daily Savings"] >= 0).sum()
                        st.metric("Days Under Budget", f"{days_under_budget}/{total_days}")
                        
                    with col4:
                        total_savings = daily_summary["Daily Savings"].sum()
                        st.metric("Total Savings", f"₱{total_savings:,.0f}")
                    
                    st.markdown("#### 🏷️ Daily Category Breakdown")
                    
                    category_daily = df.pivot_table(
                        values="Expense Amount",
                        index="Date",
                        columns="Category",
                        aggfunc="sum",
                        fill_value=0
                    ).reset_index()
                    
                    category_daily_display = category_daily.copy()
                    category_daily_display["Date"] = category_daily_display["Date"].dt.strftime("%Y-%m-%d")
                    
                    numeric_columns = [col for col in category_daily_display.columns if col != "Date"]
                    format_dict = {col: "₱{:,.0f}" for col in numeric_columns}
                    
                    st.dataframe(
                        category_daily_display.style.format(format_dict),
                        use_container_width=True,
                        height=400
                    )
                
                with summary_tab2:
                    st.markdown("#### 📋 Detailed Expense Log")
                    
                    df_display = df.copy()
                    df_display["Date"] = df_display["Date"].dt.strftime("%Y-%m-%d (%a)")
                    df_display["Amount"] = df_display["Expense Amount"].map(lambda x: f"₱{x:,.2f}")
                    
                    st.dataframe(
                        df_display[["Date", "Expense Label", "Category", "Amount"]], 
                        use_container_width=True, 
                        height=500
                    )
                    
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        csv_detailed = df_display[["Date", "Expense Label", "Category", "Expense Amount"]].to_csv(index=False)
                        st.download_button(
                            "📥 Download Detailed Log",
                            csv_detailed,
                            "fourcast_detailed.csv",
                            "text/csv",
                            use_container_width=True
                        )
                        
                    with col2:
                        csv_summary = daily_summary[["Date", "Total Spent", "Number of Expenses", "Daily Savings"]].to_csv(index=False)
                        st.download_button(
                            "📥 Download Daily Summary", 
                            csv_summary,
                            "fourcast_summary.csv",
                            "text/csv",
                            use_container_width=True
                        )

            with tab3:
                st.markdown("### 📈 Advanced Analytics")
                
                daily_data = df.groupby("Date").agg({"Expense Amount": "sum"}).reset_index()
                
                if len(daily_data) > 0:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    dates = daily_data["Date"].dt.strftime('%m/%d')
                    amounts = daily_data["Expense Amount"]
                    
                    bars = ax.bar(dates, amounts, color='#6366f1', alpha=0.7)
                    
                    ax.set_xlabel("DATE", color='white', fontsize=12, fontweight='bold')
                    ax.set_ylabel("AMOUNT (₱)", color='white', fontsize=12, fontweight='bold')
                    ax.set_title("Daily Spending", color='white', fontsize=14, fontweight='bold')
                    
                    ax.tick_params(colors='white', labelsize=10)
                    plt.xticks(rotation=45)
                    
                    for bar, amount in zip(bars, amounts):
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height + max(amounts)*0.01,
                            f'₱{height:,.0f}', ha='center', va='bottom', color='white', fontweight='bold')
                    
                    ax.spines['bottom'].set_color('white')
                    ax.spines['top'].set_color('white') 
                    ax.spines['right'].set_color('white')
                    ax.spines['left'].set_color('white')
                    ax.grid(alpha=0.3, color='white')
                    
                    fig.patch.set_facecolor('#1f2937')
                    ax.set_facecolor('#1f2937')
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                    
                    st.markdown("#### 📊 Daily Breakdown")
                    display_data = daily_data.copy()
                    display_data["Date"] = display_data["Date"].dt.strftime("%Y-%m-%d")
                    display_data["Amount (₱)"] = display_data["Expense Amount"]
                    st.dataframe(display_data[["Date", "Amount (₱)"]].style.format({"Amount (₱)": "₱{:,.0f}"}))
                    
                else:
                    st.warning("No data available for charts")

            with tab4:
                st.markdown("### 🔮 Smart Forecast")
                
                daily_spending = df.groupby("Date").agg({"Expense Amount": "sum"}).reset_index()
                
                if len(daily_spending) >= 2:
                    avg_spending = daily_spending["Expense Amount"].mean()
                    future_days = 7
                    future_dates = pd.date_range(daily_spending["Date"].iloc[-1] + pd.Timedelta(days=1), periods=future_days)
                    
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    hist_dates = daily_spending["Date"].dt.strftime('%m/%d')
                    hist_amounts = daily_spending["Expense Amount"]
                    
                    future_date_str = [d.strftime('%m/%d') for d in future_dates]
                    forecast_amounts = [avg_spending] * future_days
                    
                    ax.bar(hist_dates, hist_amounts, alpha=0.7, color='#6366f1', label='Past Spending')
                    ax.bar(future_date_str, forecast_amounts, alpha=0.7, color='#f59e0b', label='Forecast')
                    
                    ax.set_xlabel("DATE", color='white', fontsize=12, fontweight='bold')
                    ax.set_ylabel("AMOUNT (₱)", color='white', fontsize=12, fontweight='bold') 
                    ax.set_title("Spending Forecast", color='white', fontsize=14, fontweight='bold')
                    
                    ax.tick_params(colors='white', labelsize=10)
                    ax.legend(facecolor='#1f2937', edgecolor='white', labelcolor='white', fontsize=10)
                    plt.xticks(rotation=45)
                    
                    ax.spines['bottom'].set_color('white')
                    ax.spines['top'].set_color('white') 
                    ax.spines['right'].set_color('white')
                    ax.spines['left'].set_color('white')
                    ax.grid(alpha=0.3, color='white')
                    
                    fig.patch.set_facecolor('#1f2937')
                    ax.set_facecolor('#1f2937')
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                    
                    st.markdown("#### 📅 Next 7 Days Forecast")
                    forecast_df = pd.DataFrame({
                        "Date": future_dates.strftime("%a, %b %d"),
                        "Expected Spending (₱)": forecast_amounts,
                        "Your Allowance (₱)": [daily_allowance] * future_days,
                        "Status": ["✅ Under Budget" if spend <= daily_allowance else "❌ Over Budget" 
                                for spend in forecast_amounts]
                    })
                    st.dataframe(forecast_df.style.format({
                        "Expected Spending (₱)": "₱{:,.0f}",
                        "Your Allowance (₱)": "₱{:,.0f}"
                    }), use_container_width=True)
                    
                    st.markdown("#### 💡 Insights")
                    if avg_spending > daily_allowance:
                        st.error(f"**Warning:** You're spending ₱{avg_spending - daily_allowance:,.0f} per day over your budget!")
                    else:
                        st.success(f"**Good job!** You're ₱{daily_allowance - avg_spending:,.0f} per day under your budget!")
                            
                else:
                    st.warning(f"Need at least 2 days of data for forecasting. You have {len(daily_spending)} days.")

    else:
        st.markdown("""
        <div style='text-align: center; padding: 40px; background: rgba(255,255,255,0.03); border-radius: 12px;'>
            <h3 style='color: #cbd5e1; margin-bottom: 20px;'>🚀 Ready to Start Tracking?</h3>
            <p style='color: #94a3b8; margin-bottom: 30px;'>
                Add your first expense above or upload a CSV file to begin your financial journey!
            </p>
            <p style='color: #64748b; font-size: 0.9em;'>
                💡 <strong>Your data is now automatically saved</strong> and will persist between sessions!
            </p>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.page == "analyzer":
    st.markdown("<h1 class='fourcast-gradient'>📊 FourCast Data Analyzer</h1>", unsafe_allow_html=True)
    st.markdown("Upload any CSV file for powerful data analysis and visualization")
    
    uploaded = st.file_uploader("Drag & drop your CSV file here", type=["csv"], 
                               key="flex_upload", help="Supports any CSV format with automatic column detection")
    
    if uploaded is not None:
        try:
            with st.spinner("🔍 Analyzing your data..."):
                df_any = pd.read_csv(uploaded)
                
            st.success(f"✅ Successfully loaded {len(df_any)} rows × {len(df_any.columns)} columns")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Rows", f"{len(df_any):,}")
            with col2:
                st.metric("Total Columns", len(df_any.columns))
            with col3:
                st.metric("Memory Usage", f"{df_any.memory_usage(deep=True).sum() / 1024 ** 2:.1f} MB")
            
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
            
            st.markdown("---")
            st.markdown("### 🎯 Advanced Analysis")
            
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
                try:
                    analysis_df = df_any[[date_col, value_col]].copy()
                    analysis_df[date_col] = pd.to_datetime(analysis_df[date_col], errors='coerce')
                    analysis_df = analysis_df.dropna()
                    
                    if not analysis_df.empty:
                        st.markdown("#### 📈 Time Series Analysis")
                        
                        fig, ax = plt.subplots(figsize=(12, 6))
                        ax.plot(analysis_df[date_col], analysis_df[value_col], 
                               marker='o', linewidth=2, markersize=4, color='#6366f1')
                        ax.set_title(f"Time Series: {value_col} over Time", color='white', fontsize=14)
                        ax.grid(alpha=0.3)
                        ax.tick_params(colors='white')
                        plt.xticks(rotation=45)
                        st.pyplot(fig)
                        
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
            
            st.markdown("---")
            st.markdown("### 💾 Export Results")
            processed_csv = df_any.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Processed Data", processed_csv, 
                             "fourcast_analysis.csv", "text/csv", use_container_width=True)
                
        except Exception as e:
            st.error(f"❌ Failed to process CSV: {e}")
    else:
        st.markdown("""
        <div style='text-align: center; padding: 60px; background: rgba(255,255,255,0.03); border-radius: 12px;'>
            <h3 style='color: #cbd5e1; margin-bottom: 20px;'>📂 Upload Your Data</h3>
            <p style='color: #94a3b8; margin-bottom: 30px;'>
                Drag and drop any CSV file to unlock powerful analysis features including:<br>
                • Automatic column detection • Time series analysis • Statistical insights • Data visualization
            </p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns([2, 1, 1])
with footer_col1:
    st.caption("🚀 **FourCast** • Smart Budget Dashboard • Your data never leaves your browser")
with footer_col2:
    st.caption("💾 Auto-save enabled")
with footer_col3:
    st.caption("🔒 Privacy first")