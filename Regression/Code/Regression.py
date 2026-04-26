import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from sklearn.metrics import roc_curve, auc, f1_score
from pathlib import Path

df = pd.read_csv(Path(__file__).parent.parent / 'SCS_2015_2024_data.csv')

df['log_Hail_Pop_PPH_Sum'] = np.log1p(df['Hail_Pop_PPH_Sum'] / 1e5)
df['log_Torn_Pop_PPH_Sum'] = np.log1p(df['Torn_Pop_PPH_Sum'] / 1e5)
df['log_Wind_Pop_PPH_Sum'] = np.log1p(df['Wind_Pop_PPH_Sum'] / 1e5)
df['log_spread_lat']       = np.log1p(df['spread_lat'])
df['log_Wind_x_day']       = np.log1p(df['Num_Wind'] * df['abs_days_from_july1'])


y = df['BDD']

X = sm.add_constant(df[[
    # Exposure Data
    'log_Hail_Pop_PPH_Sum',
    'log_Torn_Pop_PPH_Sum',
    'log_Wind_Pop_PPH_Sum',
    # Raw numbers
    'Num_Hail',
    'Num_Wind',
    # Seasonal distance
    'abs_days_from_may15',
    'log_Wind_x_day',
    # Outlook
    'cat_risk',
    # Location
    'centroid_lat_center',
    'centroid_lon_center',
    'log_spread_lat',
    # Temporal trend
    'YEAR',
]])

results = sm.Logit(y, X).fit()
print(results.summary())

df['pred_prob'] = results.predict(X)

y_pred = (df['pred_prob'] >= .25).astype(int)

# ROC
fpr, tpr, _ = roc_curve(y, df['pred_prob'])
roc_auc = auc(fpr, tpr)

plt.figure(figsize=(8, 6))
plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'AUC = {roc_auc:.3f}')
plt.plot([0, 1], [0, 1], 'k--', lw=1)
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve — Combined Regression')
plt.legend()
plt.tight_layout()
plt.show()

# Confusion Matrix
cm = confusion_matrix(y, y_pred)
ConfusionMatrixDisplay(cm, display_labels=['No BDD', 'BDD']).plot(cmap='Blues')
plt.title('Confusion Matrix — Combined Regression')
plt.tight_layout()
plt.show()

tn, fp, fn, tp = cm.ravel()
precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall    = tp / (tp + fn) if (tp + fn) > 0 else 0
f1        = f1_score(y, y_pred, zero_division=0)
accuracy  = (tp + tn) / len(y)


print(f"F1        : {f1:.4f}")
print(f"Precision : {precision:.4f}")
print(f"Recall    : {recall:.4f}")
print(f"Accuracy  : {accuracy:.4f}")
print(f"TP={tp}  FP={fp}  TN={tn}  FN={fn}")

# VIF
vif = pd.DataFrame({'Feature': X.columns})
vif['VIF'] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
print(f"\nVIF:\n{vif.to_string(index=False)}\n")
