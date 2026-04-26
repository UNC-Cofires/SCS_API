import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

scs = pd.read_csv(Path(__file__).parent.parent / 'SCS_2015_2024_data.csv')
scs['date'] = pd.to_datetime(scs['Begin_Date'], format='%Y%m%d')

full_range = pd.DataFrame({'date': pd.date_range('2015-01-01', '2024-12-31')})
full_range['Month_Num'] = full_range['date'].dt.month
full_range['Day_Num']   = full_range['date'].dt.day

counts_df = full_range.merge(
    scs[['date', 'Num_Hail', 'Num_Torn', 'Num_Wind']],
    on='date', how='left'
).fillna(0)

# Buckets for Hail, Tornado
def assign_bucket_may15(row):
    m, d = int(row['Month_Num']), int(row['Day_Num'])
    if m < 5:
        return f'{m:02d}_pre'
    elif m == 5 and d <= 15:
        return '05_pre'
    elif m == 5 and d > 15:
        return '05_post'
    else:
        return f'{m:02d}_post'

# Buckets for Wind
def assign_bucket_jul1(row):
    m = int(row['Month_Num'])
    if m < 7:
        return f'{m:02d}_pre'
    else:
        return f'{m:02d}_post'

counts_df['bucket_may15'] = counts_df.apply(assign_bucket_may15, axis=1)
counts_df['bucket_jul1']  = counts_df.apply(assign_bucket_jul1,  axis=1)

bucket_order_may15 = (
    ['01_pre','02_pre','03_pre','04_pre','05_pre']
    + ['CENTER']
    + ['05_post','06_post','07_post','08_post','09_post','10_post','11_post','12_post']
)
x_labels_may15 = (
    ['Jan','Feb','Mar','Apr','May\n(1–15)']
    + ['May 15']
    + ['May\n(16–31)','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
)

bucket_order_jul1 = (
    ['01_pre','02_pre','03_pre','04_pre','05_pre','06_pre']
    + ['CENTER']
    + ['07_post','08_post','09_post','10_post','11_post','12_post']
)
x_labels_jul1 = (
    ['Jan','Feb','Mar','Apr','May','Jun']
    + ['Jul 1']
    + ['Jul','Aug','Sep','Oct','Nov','Dec']
)

#Plotting
storm_types = [('Num_Hail',    'Hail',    'seagreen',  'bucket_may15', bucket_order_may15, x_labels_may15, 'May 15'),
               ('Num_Torn',    'Tornado', 'firebrick', 'bucket_may15', bucket_order_may15, x_labels_may15, 'May 15'),
               ('Num_Wind',    'Wind',    'steelblue', 'bucket_jul1',  bucket_order_jul1,  x_labels_jul1,  'Jul 1')]

for report_col, label, color, bucket_col, bucket_order, x_labels, divider_label in storm_types:
    
    bucket_means = counts_df.groupby(bucket_col)[report_col].mean()

    avg_reports = []
    for b in bucket_order:
        if b == 'CENTER':
            avg_reports.append(np.nan)
        else:
            avg_reports.append(bucket_means.get(b, np.nan))

    x = np.arange(len(bucket_order))

    fig, ax = plt.subplots(figsize=(14, 6))

    for i, val in enumerate(avg_reports):
        if np.isnan(val):
            continue
        ax.bar(i, val, width=0.7, color=color, edgecolor='black', alpha=0.85)
        ax.text(i, val + 0.02, f'{val:.1f}', ha='center', va='bottom', fontsize=8.5)

    center_pos = bucket_order.index('CENTER')
    ax.axvline(x=center_pos, color='black', linestyle='--', linewidth=1.8, label=divider_label)

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, fontsize=9.5)
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel(f'Avg {label} Reports per Day', fontsize=12)
    ax.set_title(f'Avg Daily {label} Reports by Month\n(Jan → {divider_label} | {divider_label} → Dec, 2015–2024)',
                 fontsize=13, pad=10)
    ax.yaxis.grid(True, linestyle='--', alpha=0.4)
    ax.set_axisbelow(True)
    ax.legend(fontsize=10)

    plt.tight_layout()
    plt.show()