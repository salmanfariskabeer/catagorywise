import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Sales Dashboard", layout="wide")
st.title("📊 Sales & Profit Dashboard")

# --- Load and Clean Function ---
def load_and_clean(filepath, month_name):
    df = pd.read_excel(filepath, engine="openpyxl")
    
    # Strip spaces in category columns
    df["Category"] = df["Category"].astype(str).str.strip()
    df["Unnamed: 1"] = df["Unnamed: 1"].astype(str).str.strip()
    
    # Drop total rows
    df = df[~df["Category"].str.contains("Total", case=False, na=False)]
    
    # Clean numeric columns
    numeric_cols = ["Total Sales", "Total Profit", "Total Cost Excise", "Discount", 
                    "Gross Sales", "VAT", "Net Sales (incl. VAT)"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(",", "").str.replace(" ", "").astype(float)
        else:
            df[col] = 0.0
    
    # Combine category and subcategory
    df["Category_Full"] = df["Category"] + " / " + df["Unnamed: 1"]
    df["Month"] = month_name
    return df

# --- Load all months ---
files_months = [
    ("JUN Category Sales Summary.Xlsx", "JUN"),
    ("JUL Category Sales Summary.Xlsx", "JUL"),
    ("AUG Category Sales Summary.Xlsx", "AUG"),
    ("SEP Category Sales Summary.Xlsx", "SEP")
]

dfs = [load_and_clean(path, month) for path, month in files_months]
merged_df = pd.concat(dfs, ignore_index=True)

# --- Sidebar Filters ---
st.sidebar.header("Filters")

# Month filter
months = ["All"] + sorted(merged_df["Month"].unique())
selected_month = st.sidebar.selectbox("Select Month", months)

# Main Category filter
main_categories = ["All"] + sorted(merged_df["Category"].unique())
selected_main_cat = st.sidebar.selectbox("Select Main Category", main_categories)

# Subcategory filter (depends on main category)
if selected_main_cat != "All":
    subcats = ["All"] + sorted(
        merged_df.loc[merged_df["Category"] == selected_main_cat, "Unnamed: 1"].unique()
    )
else:
    subcats = ["All"] + sorted(merged_df["Unnamed: 1"].unique())
selected_subcat = st.sidebar.selectbox("Select Subcategory", subcats)

# Apply filters
filtered_df = merged_df.copy()
if selected_month != "All":
    filtered_df = filtered_df[filtered_df["Month"] == selected_month]
if selected_main_cat != "All":
    filtered_df = filtered_df[filtered_df["Category"] == selected_main_cat]
if selected_subcat != "All":
    filtered_df = filtered_df[filtered_df["Unnamed: 1"] == selected_subcat]

# --- Metrics ---
st.subheader("🔎 Key Metrics")
total_sales = filtered_df["Total Sales"].sum()
total_profit = filtered_df["Total Profit"].sum()
profit_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("💵 Total Sales", f"{total_sales:,.2f}")
col2.metric("💰 Total Profit", f"{total_profit:,.2f}")
col3.metric("📈 Profit Margin %", f"{profit_margin:.2f}%")
col4.metric("📊 Unique Categories", filtered_df["Category_Full"].nunique())

# --- Top 10 Sales ---
st.subheader("🏆 Top 10 Categories / Subcategories by Sales")
top_sales = filtered_df.groupby("Category_Full")["Total Sales"].sum().reset_index()
fig_sales = px.bar(top_sales.sort_values("Total Sales", ascending=False).head(10),
                   x="Total Sales", y="Category_Full", orientation="h",
                   color="Total Sales", color_continuous_scale="Blues",
                   title="Top 10 by Sales")
st.plotly_chart(fig_sales, use_container_width=True)

# --- Top 10 Profit ---
st.subheader("💹 Top 10 Categories / Subcategories by Profit")
top_profit = filtered_df.groupby("Category_Full")["Total Profit"].sum().reset_index()
fig_profit = px.bar(top_profit.sort_values("Total Profit", ascending=False).head(10),
                    x="Total Profit", y="Category_Full", orientation="h",
                    color="Total Profit", color_continuous_scale="Greens",
                    title="Top 10 by Profit")
st.plotly_chart(fig_profit, use_container_width=True)

# --- Bottom 10 Profit Margin ---
st.subheader("📉 Bottom 10 Categories / Subcategories by Profit Margin")
filtered_df["Profit Margin %"] = filtered_df.apply(
    lambda x: (x["Total Profit"] / x["Total Sales"] * 100) if x["Total Sales"] > 0 else 0, axis=1
)

# Only subcategories (ignore totals)
subcat_df = filtered_df[~filtered_df["Category"].str.contains("Total", case=False, na=False)]
bottom_margin = subcat_df.groupby("Category_Full")["Profit Margin %"].mean().reset_index()
bottom_margin = bottom_margin.sort_values("Profit Margin %").head(10)

fig_bottom_margin = px.bar(
    bottom_margin,
    x="Profit Margin %",
    y="Category_Full",
    orientation="h",
    color="Profit Margin %",
    color_continuous_scale=px.colors.sequential.Reds,
    title="Bottom 10 Categories / Subcategories by Profit Margin"
)
st.plotly_chart(fig_bottom_margin, use_container_width=True)

# --- Monthly Trend ---
st.subheader("📅 Monthly Performance")
monthly = filtered_df.groupby(["Month", "Category_Full"]).agg(
    {"Total Sales": "sum", "Total Profit": "sum"}).reset_index()
fig_monthly = px.line(monthly, x="Month", y="Total Profit", color="Category_Full",
                      markers=True, title="Profit Trend by Month & Category")
st.plotly_chart(fig_monthly, use_container_width=True)

# --- Profit Margin Chart ---
st.subheader("📊 Top Profit Margin Categories")
profit_margin_chart = filtered_df.groupby("Category_Full")["Profit Margin %"].mean().reset_index()
fig_margin = px.bar(profit_margin_chart.sort_values("Profit Margin %", ascending=False).head(10),
                    x="Profit Margin %", y="Category_Full", orientation="h",
                    color="Profit Margin %", color_continuous_scale="Oranges",
                    title="Top 10 Profit Margin Categories")
st.plotly_chart(fig_margin, use_container_width=True)
