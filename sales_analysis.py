"""
Sales Data Analysis - Python & SQL
Author: Praveena
Description: Analyzes 50,000+ sales records to identify revenue trends,
             customer behavior, and seasonal sales patterns using Python & SQL.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import sqlite3
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────
# 1. DATA GENERATION (simulates real data)
# ─────────────────────────────────────────
np.random.seed(42)
N = 50000

regions    = ['North', 'South', 'East', 'West', 'Central']
categories = ['Electronics', 'Clothing', 'Furniture', 'Food', 'Sports', 'Books']
segments   = ['Consumer', 'Corporate', 'Home Office']

dates = pd.date_range(start='2021-01-01', end='2023-12-31', periods=N)

df = pd.DataFrame({
    'order_id'       : range(1, N + 1),
    'order_date'     : dates,
    'customer_id'    : np.random.randint(1000, 5000, N),
    'region'         : np.random.choice(regions, N, p=[0.25, 0.20, 0.20, 0.20, 0.15]),
    'category'       : np.random.choice(categories, N, p=[0.25, 0.20, 0.18, 0.15, 0.12, 0.10]),
    'segment'        : np.random.choice(segments, N, p=[0.50, 0.33, 0.17]),
    'sales'          : np.random.exponential(scale=250, size=N).round(2),
    'quantity'       : np.random.randint(1, 15, N),
    'discount'       : np.random.choice([0, 0.05, 0.10, 0.15, 0.20, 0.30], N,
                                         p=[0.40, 0.20, 0.15, 0.12, 0.08, 0.05]),
    'profit'         : np.random.normal(loc=50, scale=80, size=N).round(2),
})

# Derived columns
df['year']        = df['order_date'].dt.year
df['month']       = df['order_date'].dt.month
df['month_name']  = df['order_date'].dt.strftime('%b')
df['quarter']     = df['order_date'].dt.quarter
df['profit_margin'] = ((df['profit'] / df['sales']) * 100).round(2)

print("=" * 55)
print("        SALES DATA ANALYSIS — PRAVEENA")
print("=" * 55)
print(f"\n✅ Dataset loaded: {len(df):,} records | {df.shape[1]} columns")
print(f"   Date range  : {df['order_date'].min().date()} → {df['order_date'].max().date()}")
print(f"   Total Sales : ₹{df['sales'].sum():,.0f}")
print(f"   Total Profit: ₹{df['profit'].sum():,.0f}")

# ─────────────────────────────────────────
# 2. DATA CLEANING & EDA
# ─────────────────────────────────────────
print("\n── DATA QUALITY ──────────────────────────────────────")
print(f"   Missing values : {df.isnull().sum().sum()}")
print(f"   Duplicate rows : {df.duplicated().sum()}")

# Remove negative sales (data error)
before = len(df)
df = df[df['sales'] > 0]
print(f"   Removed {before - len(df)} rows with invalid sales values")

print("\n── DESCRIPTIVE STATISTICS ────────────────────────────")
print(df[['sales', 'quantity', 'discount', 'profit']].describe().round(2))

# ─────────────────────────────────────────
# 3. SQL ANALYSIS (via SQLite)
# ─────────────────────────────────────────
conn = sqlite3.connect(":memory:")
df.to_sql("sales", conn, index=False, if_exists="replace")

queries = {
    "Top 5 Regions by Revenue": """
        SELECT region,
               ROUND(SUM(sales), 2)  AS total_sales,
               ROUND(AVG(profit), 2) AS avg_profit,
               COUNT(*)              AS orders
        FROM sales
        GROUP BY region
        ORDER BY total_sales DESC
        LIMIT 5
    """,
    "Revenue by Category (Window Function)": """
        SELECT category,
               ROUND(SUM(sales), 2) AS total_sales,
               ROUND(SUM(sales) * 100.0 / SUM(SUM(sales)) OVER (), 2) AS pct_of_total
        FROM sales
        GROUP BY category
        ORDER BY total_sales DESC
    """,
    "Monthly Revenue Trend (CTE)": """
        WITH monthly AS (
            SELECT year, month,
                   ROUND(SUM(sales), 2) AS monthly_sales
            FROM sales
            GROUP BY year, month
        )
        SELECT year, month, monthly_sales,
               ROUND(monthly_sales - LAG(monthly_sales) OVER (
                   PARTITION BY year ORDER BY month), 2) AS mom_change
        FROM monthly
        ORDER BY year, month
        LIMIT 12
    """,
    "Top 5 Customers by Lifetime Value": """
        SELECT customer_id,
               COUNT(DISTINCT order_id) AS total_orders,
               ROUND(SUM(sales), 2)     AS lifetime_value,
               ROUND(AVG(sales), 2)     AS avg_order_value
        FROM sales
        GROUP BY customer_id
        ORDER BY lifetime_value DESC
        LIMIT 5
    """,
}

print("\n── SQL QUERY RESULTS ─────────────────────────────────")
for title, query in queries.items():
    print(f"\n📊 {title}")
    result = pd.read_sql_query(query, conn)
    print(result.to_string(index=False))

conn.close()

# ─────────────────────────────────────────
# 4. VISUALIZATIONS
# ─────────────────────────────────────────
sns.set_theme(style="darkgrid", palette="muted")
fig, axes = plt.subplots(2, 3, figsize=(18, 11))
fig.suptitle("Sales Data Analysis Dashboard — Praveena", fontsize=16,
             fontweight='bold', y=0.98)

# 4a. Monthly Revenue Trend
monthly = df.groupby(['year', 'month'])['sales'].sum().reset_index()
for yr, grp in monthly.groupby('year'):
    axes[0, 0].plot(grp['month'], grp['sales'] / 1000, marker='o', label=str(yr), linewidth=2)
axes[0, 0].set_title("Monthly Revenue Trend by Year")
axes[0, 0].set_xlabel("Month"); axes[0, 0].set_ylabel("Sales (₹ Thousands)")
axes[0, 0].legend(); axes[0, 0].set_xticks(range(1, 13))
axes[0, 0].set_xticklabels(['J','F','M','A','M','J','J','A','S','O','N','D'])

# 4b. Sales by Region
region_sales = df.groupby('region')['sales'].sum().sort_values(ascending=True)
colors = sns.color_palette("Blues_d", len(region_sales))
axes[0, 1].barh(region_sales.index, region_sales.values / 1000, color=colors)
axes[0, 1].set_title("Total Sales by Region")
axes[0, 1].set_xlabel("Sales (₹ Thousands)")
for i, v in enumerate(region_sales.values):
    axes[0, 1].text(v / 1000 + 50, i, f"₹{v/1000:.0f}K", va='center', fontsize=8)

# 4c. Category-wise Revenue Pie
cat_sales = df.groupby('category')['sales'].sum()
axes[0, 2].pie(cat_sales, labels=cat_sales.index, autopct='%1.1f%%',
               startangle=140, colors=sns.color_palette("Set2", len(cat_sales)))
axes[0, 2].set_title("Revenue Share by Category")

# 4d. Profit vs Sales scatter
sample = df.sample(2000, random_state=42)
axes[1, 0].scatter(sample['sales'], sample['profit'], alpha=0.4,
                   c=sample['discount'], cmap='RdYlGn_r', s=15)
axes[1, 0].set_title("Profit vs Sales (colored by Discount)")
axes[1, 0].set_xlabel("Sales (₹)"); axes[1, 0].set_ylabel("Profit (₹)")
axes[1, 0].axhline(0, color='red', linestyle='--', linewidth=0.8)

# 4e. Quarterly Sales Heatmap
pivot = df.groupby(['year', 'quarter'])['sales'].sum().unstack() / 1000
sns.heatmap(pivot, ax=axes[1, 1], annot=True, fmt='.0f', cmap='YlOrRd',
            linewidths=0.5, cbar_kws={'label': '₹ Thousands'})
axes[1, 1].set_title("Quarterly Sales Heatmap (₹K)")
axes[1, 1].set_xlabel("Quarter"); axes[1, 1].set_ylabel("Year")

# 4f. Segment Sales Distribution
seg_data = [df[df['segment'] == s]['sales'].values for s in segments]
bp = axes[1, 2].boxplot(seg_data, labels=segments, patch_artist=True,
                         notch=True, showfliers=False)
colors_box = sns.color_palette("pastel", 3)
for patch, color in zip(bp['boxes'], colors_box):
    patch.set_facecolor(color)
axes[1, 2].set_title("Sales Distribution by Segment")
axes[1, 2].set_ylabel("Sales (₹)")

plt.tight_layout()
plt.savefig("sales_dashboard.png", dpi=150, bbox_inches='tight')
print("\n✅ Dashboard saved → sales_dashboard.png")
plt.show()

print("\n" + "=" * 55)
print("  Analysis complete. All charts & insights generated.")
print("=" * 55)
