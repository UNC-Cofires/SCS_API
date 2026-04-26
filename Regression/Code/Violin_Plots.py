import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

df = pd.read_csv(Path(__file__).parent.parent / 'SCS_2015_2024_data.csv')

storm_types    = ['Num_Tornado', 'Num_Hail', 'Num_Wind']
labels         = ['Tornado', 'Hail', 'Severe Wind']
colors         = ['steelblue', 'firebrick']

df['Num_Total'] = df[storm_types].sum(axis=1)
all_storm_cols  = storm_types + ['Num_Total']
all_labels      = labels + ['Total']

non_bdd_df = df[df['BDD'] == 0.0]
bdd_df     = df[df['BDD'] == 1.0]

def styled_violin(ax, data, pos, color):
    parts = ax.violinplot(data, positions=[pos],
                          showmedians=True, showextrema=True, widths=0.75)
    for pc in parts['bodies']:
        pc.set_facecolor(color)
        pc.set_edgecolor('black')
        pc.set_alpha(0.82)
    parts['cmedians'].set_color('white')
    parts['cmedians'].set_linewidth(2)
    for key in ('cbars', 'cmins', 'cmaxes'):
        parts[key].set_color('black')
        parts[key].set_linewidth(1.2)

legend_handles = [
    mpatches.Patch(facecolor=colors[0], edgecolor='black', label='Non-BDD (0.0)'),
    mpatches.Patch(facecolor=colors[1], edgecolor='black', label='BDD (1.0)'),
]

for col, label in zip(all_storm_cols, all_labels):
    fig, ax = plt.subplots(figsize=(6, 7))

    styled_violin(ax, non_bdd_df[col].dropna(), -0.45, colors[0])
    styled_violin(ax, bdd_df[col].dropna(),      0.45, colors[1])

    ax.set_xticks([-0.45, 0.45])
    ax.set_xticklabels(['Non-BDD (0.0)', 'BDD (1.0)'], fontsize=12)
    ax.set_ylabel('Number of Reports per Day', fontsize=12)
    ax.set_title(f'Distribution of {label} Reports: BDD vs Non-BDD\n(2015–2024)',
                 fontsize=13, pad=10)
    ax.yaxis.grid(True, linestyle='--', alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(handles=legend_handles, fontsize=11, loc='upper right')

    plt.tight_layout()
    plt.show()