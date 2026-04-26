import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

df = pd.read_csv(Path(__file__).parent.parent / 'SCS_2015_2024_data.csv')
df['Begin_Date'] = pd.to_datetime(df['Begin_Date'], format='%Y%m%d')

monthly = (df.groupby(df['Begin_Date'].dt.month)[['Num_Tornado', 'Num_Hail', 'Num_Wind']]
             .sum().reindex(range(1, 13), fill_value=0))

MONTHS       = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
STORM_COLS   = ['Num_Tornado', 'Num_Hail', 'Num_Wind']
STORM_COLORS = ['#C0392B', '#27AE60', '#2980B9']
STORM_LABELS = ['Tornado', 'Hail', 'Wind']

SEASONS = [
    ('Winter', '#4A90D9', [11, 0, 1]),
    ('Spring', '#2ECC71', [2, 3, 4]),
    ('Summer', '#F1C40F', [5, 6, 7]),
    ('Fall',   '#E67E22', [8, 9, 10]),
]

def polar_chart(ax, data, cols, colors, norm, title):
    angles = np.linspace(np.pi/2, np.pi/2 - 2*np.pi, 12, endpoint=False)
    inner, max_h, bar_w = 0.55, 2.2, 0.45

    ax.set_theta_direction(-1)
    ax.set_theta_offset(np.pi/2)
    ax.set_facecolor('#f7f7f7')
    ax.set(yticks=[], xticks=[])
    ax.spines['polar'].set_visible(False)

    # Grid rings
    for r in np.linspace(inner, inner + max_h, 5):
        ax.plot(np.linspace(0, 2*np.pi, 300), [r]*300, color='#c0c0c0', lw=0.7)
    ax.fill(np.linspace(0, 2*np.pi, 300), [inner]*300, color='#f7f7f7')

    # Bars
    for i, (angle, (_, row)) in enumerate(zip(angles, data.iterrows())):
        bottom = inner
        for col, color in zip(cols, colors):
            h = (row[col] / norm) * max_h
            ax.bar(angle, h, width=bar_w, bottom=bottom, color=color, alpha=0.82,
                   edgecolor='white', linewidth=0.6)
            bottom += h
        ax.text(angle, bottom + 0.05, f"{int(row[cols].sum()):,}",
                ha='center', va='bottom', fontsize=9, fontweight='bold')
        ax.text(angle, inner + max_h + 0.30, MONTHS[i],
                ha='center', va='center', fontsize=9, fontweight='bold', color='#333333')

    r_base = inner + max_h + 0.44
    for name, color, idxs in SEASONS:

        season_angles = [angles[i] for i in idxs]
        if name == 'Winter':
            season_angles = [a if a > 0 else a + 2*np.pi for a in season_angles]
        a_l = max(season_angles) + 0.18
        a_r = min(season_angles) - 0.18
        a_mid = np.mean(season_angles)
        ax.plot(np.linspace(a_r, a_l, 50), [r_base]*50, color=color, lw=2)
        for a in [a_l, a_r]:
            ax.plot([a, a], [r_base, r_base + 0.08], color=color, lw=2)
        ax.plot([a_mid, a_mid], [r_base, r_base + 0.08], color=color, lw=2)
        ax.text(a_mid, r_base + 0.12, name, ha='center', fontsize=9,
                fontweight='bold', color=color)

    ax.set(ylim=(0, inner + max_h + 1.0))
    ax.set_title(title, y=1.03, fontsize=12, fontweight='bold', color='#222222')

# Combined chart
fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))
polar_chart(ax, monthly, STORM_COLS, STORM_COLORS,
            norm=monthly[STORM_COLS].sum(axis=1).max(),
            title='Storm Reports by Month (2015–2024)')
ax.legend(handles=[mpatches.Patch(color=c, label=l, alpha=0.82)
                   for c, l in zip(STORM_COLORS, STORM_LABELS)],
          loc='lower center', bbox_to_anchor=(0.5, -0.03),
          ncol=3, frameon=False, fontsize=9)
plt.tight_layout()
plt.show()

# Individual charts
for col, color, label in zip(STORM_COLS, STORM_COLORS, STORM_LABELS):
    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))
    polar_chart(ax, monthly, [col], [color],
                norm=monthly[col].max(),
                title=f'{label} Reports by Month (2015–2024)')
    ax.legend(handles=[mpatches.Patch(color=color, label=label, alpha=0.82)],
              loc='lower center', bbox_to_anchor=(0.5, -0.03), frameon=False, fontsize=9)
    plt.tight_layout()
    plt.show()
