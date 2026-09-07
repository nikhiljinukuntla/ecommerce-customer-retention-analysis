"""
================================================================================
E-Commerce Customer Segmentation & Retention Analysis
Python EDA Notebook
================================================================================
Dataset: 50K customers, 250K orders, 750K order items, 100K reviews
Skills: Pandas, NumPy, Matplotlib, Seaborn, Statistical Analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from operator import attrgetter
import warnings
warnings.filterwarnings('ignore')

# Set visual style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 6)
plt.rcParams['font.size'] = 10

# ==============================================================================
# 1. DATA LOADING
# ==============================================================================
print("=" * 70)
print("LOADING DATA")
print("=" * 70)

customers = pd.read_csv('customers.csv')
orders = pd.read_csv('orders.csv')
products = pd.read_csv('products.csv')
order_items = pd.read_csv('order_items.csv')
reviews = pd.read_csv('reviews.csv')

print(f"\nCustomers:    {customers.shape[0]:,} rows x {customers.shape[1]} cols")
print(f"Orders:       {orders.shape[0]:,} rows x {orders.shape[1]} cols")
print(f"Order Items:  {order_items.shape[0]:,} rows x {order_items.shape[1]} cols")
print(f"Products:     {products.shape[0]:,} rows x {products.shape[1]} cols")
print(f"Reviews:      {reviews.shape[0]:,} rows x {reviews.shape[1]} cols")

# ==============================================================================
# 2. DATA EXPLORATION & QUALITY CHECKS
# ==============================================================================
print("\n" + "=" * 70)
print("DATA EXPLORATION & QUALITY CHECKS")
print("=" * 70)

# Convert dates
orders['order_date'] = pd.to_datetime(orders['order_date'])
customers['registration_date'] = pd.to_datetime(customers['registration_date'])
reviews['review_date'] = pd.to_datetime(reviews['review_date'])

print("\n--- Missing Values ---")
for name, df in [('customers', customers), ('orders', orders), 
                  ('products', products), ('order_items', order_items), ('reviews', reviews)]:
    missing = df.isnull().sum().sum()
    print(f"{name:<15}: {missing} missing values")

print("\n--- Duplicate Records ---")
for name, df, key in [('customers', customers, 'customer_id'), 
                       ('orders', orders, 'order_id'),
                       ('products', products, 'product_id'),
                       ('order_items', order_items, 'order_item_id'),
                       ('reviews', reviews, 'review_id')]:
    dups = df.duplicated(subset=[key]).sum()
    print(f"{name:<15}: {dups} duplicates")

print("\n--- Order Status Distribution ---")
print(orders['order_status'].value_counts())
print(f"\nOrder Status Percentage:")
print((orders['order_status'].value_counts(normalize=True) * 100).round(2))

print("\n--- Order Amount Statistics (Completed) ---")
completed_orders = orders[orders['order_status'] == 'Completed']
print(completed_orders['order_amount'].describe().round(2))

print("\n--- Product Category Distribution ---")
print(products['category'].value_counts())

print("\n--- Country Distribution (Top 10) ---")
print(customers['country'].value_counts().head(10))

# ==============================================================================
# 3. RFM ANALYSIS & CUSTOMER SEGMENTATION
# ==============================================================================
print("\n" + "=" * 70)
print("RFM ANALYSIS & CUSTOMER SEGMENTATION")
print("=" * 70)

reference_date = orders['order_date'].max() + pd.Timedelta(days=1)
print(f"Reference Date: {reference_date.date()}")

# Calculate RFM metrics
rfm = completed_orders.groupby('customer_id').agg({
    'order_date': lambda x: (reference_date - x.max()).days,  # Recency
    'order_id': 'count',                                        # Frequency
    'order_amount': 'sum'                                       # Monetary
}).rename(columns={
    'order_date': 'recency',
    'order_id': 'frequency',
    'order_amount': 'monetary'
})

# Add quintile scores (1-5)
rfm['r_score'] = pd.qcut(rfm['recency'].rank(method='first'), 5, labels=[5,4,3,2,1], duplicates='drop')
rfm['f_score'] = pd.qcut(rfm['frequency'].rank(method='first'), 5, labels=[1,2,3,4,5], duplicates='drop')
rfm['m_score'] = pd.qcut(rfm['monetary'], 5, labels=[1,2,3,4,5], duplicates='drop')

rfm['r_score'] = rfm['r_score'].astype(int)
rfm['f_score'] = rfm['f_score'].astype(int)
rfm['m_score'] = rfm['m_score'].astype(int)
rfm['rfm_score'] = (rfm['r_score'] + rfm['f_score'] + rfm['m_score']) / 3

# Segment customers
def segment_customers(row):
    r, f, m = row['r_score'], row['f_score'], row['m_score']
    if r >= 4 and f >= 4 and m >= 4:
        return 'Champions'
    elif r >= 3 and f >= 3 and m >= 3:
        return 'Loyal Customers'
    elif r <= 2:
        return 'At Risk'
    elif f == 1:
        return 'New Customers'
    else:
        return 'Potential'

rfm['segment'] = rfm.apply(segment_customers, axis=1)

print("\n--- RFM Segment Distribution ---")
segment_counts = rfm['segment'].value_counts()
print(segment_counts)
print(f"\n--- RFM Segment Percentage ---")
print((segment_counts / len(rfm) * 100).round(2))

# ==============================================================================
# VISUALIZATION 1: Customer Segmentation Dashboard
# ==============================================================================
print("\nGenerating Visualization 1: Customer Segmentation...")

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Customer Segmentation Dashboard (RFM Analysis)', fontsize=16, fontweight='bold', y=1.02)

# 1. Segment distribution
segment_counts = rfm['segment'].value_counts()
colors = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c', '#9b59b6']
axes[0, 0].bar(segment_counts.index, segment_counts.values, color=colors)
axes[0, 0].set_title('Customer Segment Distribution', fontsize=13, fontweight='bold')
axes[0, 0].set_ylabel('Number of Customers')
axes[0, 0].tick_params(axis='x', rotation=15)
for i, v in enumerate(segment_counts.values):
    axes[0, 0].text(i, v + max(segment_counts.values)*0.01, f'{v:,}', ha='center', fontweight='bold')

# 2. Revenue by segment
revenue_by_segment = rfm.groupby('segment')['monetary'].sum().sort_values(ascending=False)
axes[0, 1].bar(revenue_by_segment.index, revenue_by_segment.values, color=colors)
axes[0, 1].set_title('Total Revenue by Segment', fontsize=13, fontweight='bold')
axes[0, 1].set_ylabel('Revenue ($)')
axes[0, 1].tick_params(axis='x', rotation=15)
for i, v in enumerate(revenue_by_segment.values):
    axes[0, 1].text(i, v + max(revenue_by_segment.values)*0.01, f'${v/1e6:.1f}M', ha='center', fontweight='bold')

# 3. Recency vs Monetary scatter
segment_colors = {'Champions': '#2ecc71', 'Loyal Customers': '#3498db', 
                  'Potential': '#f39c12', 'At Risk': '#e74c3c', 'New Customers': '#9b59b6'}
for segment in rfm['segment'].unique():
    data = rfm[rfm['segment'] == segment]
    axes[1, 0].scatter(data['recency'], data['monetary'], 
                       label=segment, alpha=0.5, s=20, c=segment_colors.get(segment, '#333'))
axes[1, 0].set_xlabel('Recency (days since last purchase)')
axes[1, 0].set_ylabel('Monetary (total spending)')
axes[1, 0].set_title('Recency vs Monetary by Segment', fontsize=13, fontweight='bold')
axes[1, 0].legend(loc='upper right', fontsize=8)
axes[1, 0].set_yscale('log')

# 4. Frequency distribution by segment
for segment in rfm['segment'].unique():
    data = rfm[rfm['segment'] == segment]['frequency']
    axes[1, 1].hist(data, bins=30, alpha=0.6, label=segment, color=segment_colors.get(segment, '#333'))
axes[1, 1].set_xlabel('Purchase Frequency')
axes[1, 1].set_ylabel('Number of Customers')
axes[1, 1].set_title('Purchase Frequency Distribution', fontsize=13, fontweight='bold')
axes[1, 1].legend(fontsize=8)
axes[1, 1].set_yscale('log')

plt.tight_layout()
plt.savefig('01_customer_segmentation.png', dpi=300, bbox_inches='tight')
print("  Saved: 01_customer_segmentation.png")

# ==============================================================================
# VISUALIZATION 2: Product Performance
# ==============================================================================
print("\nGenerating Visualization 2: Product Performance...")

# Merge for analysis
order_analysis = order_items.merge(products, on='product_id', how='left')
order_analysis = order_analysis.merge(
    orders[['order_id', 'order_date', 'order_status']], on='order_id', how='left'
)
order_analysis = order_analysis[order_analysis['order_status'] == 'Completed']
order_analysis['line_revenue'] = order_analysis['quantity'] * order_analysis['unit_price']

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Product Performance Dashboard', fontsize=16, fontweight='bold', y=1.02)

# 1. Top 10 products by revenue
product_revenue = order_analysis.groupby('product_name')['line_revenue'].sum().sort_values(ascending=True).tail(10)
axes[0, 0].barh(product_revenue.index, product_revenue.values, color='#3498db')
axes[0, 0].set_title('Top 10 Products by Revenue', fontsize=13, fontweight='bold')
axes[0, 0].set_xlabel('Revenue ($)')

# 2. Revenue by category
category_revenue = order_analysis.groupby('category')['line_revenue'].sum().sort_values(ascending=False)
colors_cat = plt.cm.Set3(np.linspace(0, 1, len(category_revenue)))
axes[0, 1].pie(category_revenue.values, labels=category_revenue.index, autopct='%1.1f%%', 
               colors=colors_cat, startangle=90)
axes[0, 1].set_title('Revenue Distribution by Category', fontsize=13, fontweight='bold')

# 3. Units sold by category
units_by_category = order_analysis.groupby('category')['quantity'].sum().sort_values(ascending=False)
axes[1, 0].bar(units_by_category.index, units_by_category.values, color='#2ecc71')
axes[1, 0].set_title('Total Units Sold by Category', fontsize=13, fontweight='bold')
axes[1, 0].set_ylabel('Units Sold')
axes[1, 0].tick_params(axis='x', rotation=30)

# 4. Price vs quantity sold
product_stats = order_analysis.groupby('product_id').agg({
    'unit_price': 'first',
    'quantity': 'sum'
}).merge(products[['product_id', 'category']], on='product_id')
cat_colors = {cat: plt.cm.tab10(i) for i, cat in enumerate(product_stats['category'].unique())}
for cat in product_stats['category'].unique():
    data = product_stats[product_stats['category'] == cat]
    axes[1, 1].scatter(data['unit_price'], data['quantity'], alpha=0.6, s=50, 
                       label=cat, c=cat_colors[cat])
axes[1, 1].set_xlabel('Product Unit Price ($)')
axes[1, 1].set_ylabel('Total Quantity Sold')
axes[1, 1].set_title('Price vs Sales Volume by Category', fontsize=13, fontweight='bold')
axes[1, 1].legend(fontsize=8)

plt.tight_layout()
plt.savefig('02_product_performance.png', dpi=300, bbox_inches='tight')
print("  Saved: 02_product_performance.png")

# ==============================================================================
# VISUALIZATION 3: Time Series & Trends
# ==============================================================================
print("\nGenerating Visualization 3: Time Series & Trends...")

daily_revenue = completed_orders.groupby(completed_orders['order_date'].dt.date).agg({
    'order_amount': 'sum',
    'order_id': 'count'
}).reset_index()
daily_revenue.columns = ['date', 'revenue', 'order_count']
daily_revenue['date'] = pd.to_datetime(daily_revenue['date'])
daily_revenue = daily_revenue.sort_values('date')

fig, axes = plt.subplots(2, 1, figsize=(16, 10))
fig.suptitle('Revenue & Order Trends', fontsize=16, fontweight='bold', y=1.02)

# 1. Daily revenue with 7-day moving average
axes[0].plot(daily_revenue['date'], daily_revenue['revenue'], alpha=0.4, label='Daily Revenue', color='#3498db')
axes[0].plot(daily_revenue['date'], daily_revenue['revenue'].rolling(7, min_periods=1).mean(), 
             label='7-Day Moving Average', linewidth=2, color='#e74c3c')
axes[0].set_title('Daily Revenue Trend', fontsize=13, fontweight='bold')
axes[0].set_ylabel('Revenue ($)')
axes[0].legend()
axes[0].tick_params(axis='x', rotation=30)

# 2. Daily order count
axes[1].bar(daily_revenue['date'], daily_revenue['order_count'], color='#2ecc71', alpha=0.7, width=0.8)
axes[1].plot(daily_revenue['date'], daily_revenue['order_count'].rolling(7, min_periods=1).mean(), 
             color='#e74c3c', linewidth=2, label='7-Day MA')
axes[1].set_title('Daily Order Count', fontsize=13, fontweight='bold')
axes[1].set_xlabel('Date')
axes[1].set_ylabel('Number of Orders')
axes[1].legend()
axes[1].tick_params(axis='x', rotation=30)

plt.tight_layout()
plt.savefig('03_time_series_trends.png', dpi=300, bbox_inches='tight')
print("  Saved: 03_time_series_trends.png")

# ==============================================================================
# VISUALIZATION 4: Cohort Retention Heatmap
# ==============================================================================
print("\nGenerating Visualization 4: Cohort Retention...")

cohort_data = completed_orders.copy()
cohort_data['order_month'] = cohort_data['order_date'].dt.to_period('M')
cohort_data['cohort_month'] = cohort_data.groupby('customer_id')['order_date'].transform('min').dt.to_period('M')
cohort_data['cohort_index'] = (cohort_data['order_month'] - cohort_data['cohort_month']).apply(attrgetter('n'))

cohort = cohort_data.groupby(['cohort_month', 'cohort_index'])['customer_id'].nunique().unstack(fill_value=0)
cohort_size = cohort.iloc[:, 0]
retention_table = cohort.divide(cohort_size, axis=0)

plt.figure(figsize=(16, 10))
sns.heatmap(retention_table.iloc[:, :13], annot=True, fmt='.0%', cmap='RdYlGn', 
            cbar_kws={'label': 'Retention Rate'}, linewidths=0.5)
plt.title('Customer Retention by Cohort (Completed Orders)', fontsize=14, fontweight='bold')
plt.xlabel('Months Since First Purchase')
plt.ylabel('Cohort Month')
plt.tight_layout()
plt.savefig('04_cohort_retention.png', dpi=300, bbox_inches='tight')
print("  Saved: 04_cohort_retention.png")

# ==============================================================================
# 4. STATISTICAL INSIGHTS
# ==============================================================================
print("\n" + "=" * 70)
print("KEY INSIGHTS & STATISTICAL ANALYSIS")
print("=" * 70)

# 1. Segment analysis
print("\n1. CUSTOMER SEGMENT ANALYSIS")
print("-" * 60)
segment_summary = rfm.groupby('segment').agg({
    'recency': 'mean',
    'frequency': 'mean',
    'monetary': ['mean', 'sum', 'count']
}).round(2)
print(segment_summary)

# 2. Revenue concentration (Pareto)
print("\n2. REVENUE CONCENTRATION (80/20 Rule)")
print("-" * 60)
sorted_revenue = rfm['monetary'].sort_values(ascending=False)
cumsum = sorted_revenue.cumsum() / sorted_revenue.sum()
customers_for_80pct = (cumsum >= 0.8).argmax() + 1
pct_customers = 100 * customers_for_80pct / len(rfm)
print(f"Top {customers_for_80pct:,} customers ({pct_customers:.1f}%) generate 80% of revenue")
print(f"Total customers with purchases: {len(rfm):,}")

# 3. Churn analysis
print("\n3. CHURN ANALYSIS")
print("-" * 60)
reference_date = orders['order_date'].max()
last_purchase = completed_orders.groupby('customer_id')['order_date'].max()
days_inactive = (reference_date - last_purchase).dt.days
churn_30 = (days_inactive > 30).mean() * 100
churn_90 = (days_inactive > 90).mean() * 100
churn_180 = (days_inactive > 180).mean() * 100
print(f"Customers inactive > 30 days:  {churn_30:.1f}%")
print(f"Customers inactive > 90 days:  {churn_90:.1f}%")
print(f"Customers inactive > 180 days: {churn_180:.1f}%")

# 4. Correlation analysis
print("\n4. RFM CORRELATION ANALYSIS")
print("-" * 60)
correlation_data = rfm[['recency', 'frequency', 'monetary']].corr()
print(correlation_data.round(3))

# 5. Average metrics by segment
print("\n5. AVERAGE METRICS BY SEGMENT")
print("-" * 60)
segment_metrics = rfm.groupby('segment')[['recency', 'frequency', 'monetary']].mean().round(2)
print(segment_metrics)

# 6. Monthly growth summary
print("\n6. MONTHLY REVENUE GROWTH SUMMARY")
print("-" * 60)
monthly_rev = completed_orders.groupby(completed_orders['order_date'].dt.to_period('M'))['order_amount'].sum()
monthly_growth = monthly_rev.pct_change() * 100
print(f"Average monthly growth rate: {monthly_growth.mean():.2f}%")
print(f"Best month growth: {monthly_growth.max():.2f}%")
print(f"Worst month growth: {monthly_growth.min():.2f}%")

# 7. Product insights
print("\n7. PRODUCT INSIGHTS")
print("-" * 60)
product_revenue_all = order_analysis.groupby('product_name')['line_revenue'].sum().sort_values(ascending=False)
print(f"Top product revenue: ${product_revenue_all.iloc[0]:,.2f} ({product_revenue_all.index[0]})")
cat_rev = order_analysis.groupby('category')['line_revenue'].sum().sort_values(ascending=False)
print(f"Top category: {cat_rev.index[0]} (${cat_rev.iloc[0]:,.2f})")

# 8. Review insights
print("\n8. REVIEW INSIGHTS")
print("-" * 60)
review_stats = reviews.groupby('product_id')['rating'].agg(['mean', 'count']).merge(products[['product_id', 'product_name']], on='product_id')
review_stats = review_stats.sort_values('mean', ascending=False)
print(f"Highest rated product: {review_stats.iloc[0]['product_name']} ({review_stats.iloc[0]['mean']:.2f}*, {review_stats.iloc[0]['count']} reviews)")
print(f"Overall average rating: {reviews['rating'].mean():.2f}*")

print("\n" + "=" * 70)
print("EDA NOTEBOOK COMPLETE")
print("=" * 70)
