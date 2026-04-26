import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

bdd_df = pd.read_csv(Path(__file__).parent.parent / 'SCS_2015_2024_data.csv')

mask = bdd_df['BDD'] == 1.0
bdd_df.loc[mask, 'month'] = bdd_df.loc[mask, 'Begin_Date'].astype(str).str.zfill(8).str[4:6]

month_counts = bdd_df.loc[mask, 'month'].value_counts().sort_index()

month_names = {
    '01': 'Jan', 
    '02': 'Feb', 
    '03': 'Mar', 
    '04': 'Apr',
    '05': 'May', 
    '06': 'Jun', 
    '07': 'Jul', 
    '08': 'Aug',
    '09': 'Sep', 
    '10': 'Oct', 
    '11': 'Nov', 
    '12': 'Dec'
}

month_counts.index = month_counts.index.map(month_names)

season_colors = {'Winter': '#4A90D9', 'Spring': '#2ECC71', 'Summer': '#F1C40F', 'Fall': '#E67E22'}
month_to_season = {
    'Jan': 'Winter', 'Feb': 'Winter', 'Mar': 'Spring',
    'Apr': 'Spring', 'May': 'Spring', 'Jun': 'Summer',
    'Jul': 'Summer', 'Aug': 'Summer', 'Sep': 'Fall',
    'Oct': 'Fall', 'Nov': 'Fall', 'Dec': 'Winter'
}
month_bar_colors = [season_colors[month_to_season[m]] for m in month_counts.index]

#Bar
plt.figure(figsize=(10, 6))
bars = plt.bar(month_counts.index, month_counts.values, color=month_bar_colors, edgecolor='black')

for bar in bars:
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.3,
        str(int(bar.get_height())),
        ha='center', va='bottom', fontweight='bold'
    )

plt.title('BDD Events by Month')
plt.xlabel('Month')
plt.ylabel('Number of BDD Events')
plt.tight_layout()
plt.show()

season_map = {
    'Jan': 'Winter', 
    'Feb': 'Winter', 
    'Mar': 'Spring',
    'Apr': 'Spring', 
    'May': 'Spring',
    'Jun': 'Summer',
    'Jul': 'Summer', 
    'Aug': 'Summer', 
    'Sep': 'Fall',
    'Oct': 'Fall', 
    'Nov': 'Fall', 
    'Dec': 'Winter'
}

season_counts = month_counts.copy()
season_counts.index = season_counts.index.map(season_map)
season_counts = season_counts.groupby(season_counts.index).sum()

season_order = ['Winter', 'Spring', 'Summer', 'Fall']
season_counts = season_counts.reindex(season_order)


plt.figure(figsize=(8, 6))
bars = plt.bar(season_counts.index, season_counts.values,
               color=[season_colors[s] for s in season_counts.index], edgecolor='black')
for bar in bars:
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.3,
        str(int(bar.get_height())),
        ha='center', va='bottom', fontweight='bold'
    )

plt.title('BDD Events by Season')
plt.xlabel('Season')
plt.ylabel('Number of BDD Events')
plt.tight_layout()
plt.show()