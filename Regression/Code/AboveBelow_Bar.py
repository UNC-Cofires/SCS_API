import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

df = pd.read_csv(Path(__file__).parent.parent / 'SCS_2015_2024_data.csv')

storm_types = ['Num_Tornado', 'Num_Hail', 'Num_Wind']
labels      = ['Tornado', 'Hail', 'Severe Wind']

non_bdd_df = df[df['BDD'] == 0.0]
bdd_df     = df[df['BDD'] == 1.0]
overall_avg = df[storm_types].mean()

bar_colors = ['#2166ac', '#d6604d', '#f4a582', '#92c5de']
bar_labels  = [
    'Non-BDD above avg',
    'BDD above avg',
    'BDD below avg',
    'Non-BDD below avg',
]

counts = {col: {} for col in storm_types}
for col in storm_types:
    avg = overall_avg[col]
    counts[col]['non_bdd_above'] = (non_bdd_df[col] > avg).sum()
    counts[col]['bdd_above']     = (bdd_df[col]     > avg).sum()
    counts[col]['bdd_below']     = (bdd_df[col]     <= avg).sum()
    counts[col]['non_bdd_below'] = (non_bdd_df[col] <= avg).sum()

x       = np.arange(len(storm_types))
width   = 0.18
offsets = [-1.5, -0.5, 0.5, 1.5]
keys    = ['non_bdd_above', 'bdd_above', 'bdd_below', 'non_bdd_below']

fig, ax = plt.subplots(figsize=(12, 6))

for j, (key, color, blabel) in enumerate(zip(keys, bar_colors, bar_labels)):
    vals = [counts[col][key] for col in storm_types]
    bars = ax.bar(x + offsets[j] * width, vals, width=width,
                  color=color, edgecolor='black', alpha=0.88, label=blabel)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 2,
                str(val),
                ha='center', va='bottom', fontsize=8.5, fontweight='bold')

ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=13)
ax.set_ylabel('Number of Days', fontsize=12)
ax.set_title('Day Counts Above/Below Average Storm Reports: BDD vs Non-BDD (2015–2024)',
             fontsize=13, pad=12)
ax.legend(fontsize=10, loc='upper right')
ax.yaxis.grid(True, linestyle='--', alpha=0.5)
ax.set_axisbelow(True)
plt.tight_layout()
plt.show()