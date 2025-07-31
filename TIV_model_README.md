# 📄 Academic Model Formulation

## **Total Insured Value (TIV) Loss Prediction Model**

### **Mathematical Framework**

The Total Insured Value loss percentage for property $i$ at location $(\phi_i, \lambda_i)$ during storm event $d$ is modeled as:

$$
\boxed{
\text{TIV}_{\text{Loss},i}(d, \phi_i, \lambda_i) = F(\mathbf{X}_i) \cdot 100\%
}
$$

where $F: \mathbb{R}^{12} \rightarrow [0, 1]$ is a Random Forest regression model mapping a 12-dimensional feature vector $\mathbf{X}_i$ to expected loss proportion, and the result is scaled to percentage.

### **Feature Vector Specification**

The feature vector $\mathbf{X}_i \in \mathbb{R}^{12}$ comprises three categories:

#### **Weather Features** $\mathbf{W}_i \in \mathbb{R}^4$:
$$
\mathbf{W}_i = \begin{bmatrix}
\text{MESH}_i \\
P_{\text{PPH},i} \\
D_{\text{NCEI},i} \\
T_{\text{storm},i}
\end{bmatrix}
$$

where:
- $\text{MESH}_i$ = Maximum Estimated Size of Hail (inches) at property $i$
- $P_{\text{PPH},i}$ = Practically Perfect Hindcast probability $\in [0,1]$ 
- $D_{\text{NCEI},i}$ = Distance to nearest NCEI severe weather report (km)
- $T_{\text{storm},i}$ = Storm duration at location (hours)

#### **Property Features** $\mathbf{P}_i \in \mathbb{R}^5$:
$$
\mathbf{P}_i = \begin{bmatrix}
V_{\text{market},i} \\
A_{\text{building},i} \\
S_{\text{living},i} \\
Q_{\text{construction},i} \\
F_{\text{frame},i}
\end{bmatrix}
$$

where:
- $V_{\text{market},i}$ = Market value (USD) from tax appraisal
- $A_{\text{building},i}$ = Building age (years) = $2024 - \text{Year Built}$
- $S_{\text{living},i}$ = Living area (square feet)
- $Q_{\text{construction},i} \in \{0,1,2,3,4\}$ = Construction quality (Poor=0, Excellent=4)
- $F_{\text{frame},i} \in \{1,2,3\}$ = Frame type (Wood=1, Metal=2, Masonry=3)

#### **Building Features** $\mathbf{B}_i \in \mathbb{R}^3$:
$$
\mathbf{B}_i = \begin{bmatrix}
A_{\text{footprint},i} \\
C_{\text{complexity},i} \\
\rho_{\text{density},i}
\end{bmatrix}
$$

where:
- $A_{\text{footprint},i}$ = Building footprint area (square feet) from Microsoft ML footprints
- $C_{\text{complexity},i}$ = Building complexity ratio = $\frac{\text{Perimeter}}{\sqrt{\text{Area}}}$
- $\rho_{\text{density},i}$ = Local building density (buildings per hectare)

### **Complete Feature Vector**
$$
\mathbf{X}_i = \begin{bmatrix} \mathbf{W}_i \\ \mathbf{P}_i \\ \mathbf{B}_i \end{bmatrix} \in \mathbb{R}^{12}
$$

### **Synthetic Loss Function** (Training Labels)

For model training, synthetic TIV losses are generated using domain knowledge:

$$
L_{\text{synthetic},i} = \beta_0(\text{MESH}_i) \cdot \beta_1(A_{\text{building},i}) \cdot \beta_2(Q_{\text{construction},i}) \cdot \beta_3(F_{\text{frame},i}) \cdot \beta_4(P_{\text{PPH},i}) \cdot \beta_5(D_{\text{NCEI},i}) \cdot \beta_6(V_{\text{market},i}) + \epsilon_i
$$

where:

**Base Damage Function:**
$$
\beta_0(\text{MESH}) = \begin{cases}
0.005 & \text{if MESH} < 0.5 \text{ inches} \\
0.02 & \text{if } 0.5 \leq \text{MESH} < 1.0 \\
0.08 & \text{if } 1.0 \leq \text{MESH} < 1.5 \\
0.20 & \text{if } 1.5 \leq \text{MESH} < 2.0 \\
0.45 & \text{if MESH} \geq 2.0
\end{cases}
$$

**Age Vulnerability Multiplier:**
$$
\beta_1(A) = \min\left(1.0 + \max(0, (A - 20) \times 0.015), 2.5\right)
$$

**Quality Factor:**
$$
\beta_2(Q) = 1.5 - (Q \times 0.15)
$$

**Frame Type Factor:**
$$
\beta_3(F) = \begin{cases}
1.3 & \text{if } F = 1 \text{ (Wood)} \\
1.0 & \text{if } F = 2 \text{ (Metal)} \\
0.7 & \text{if } F = 3 \text{ (Masonry)}
\end{cases}
$$

**Forecast Factor:**
$$
\beta_4(P) = 0.5 + 1.5P
$$

**Distance Decay:**
$$
\beta_5(D) = e^{-D/4.0}
$$

**Exposure Factor:**
$$
\beta_6(V) = \begin{cases}
0.8 & \text{if } V < \$100,000 \\
1.0 & \text{if } \$100,000 \leq V \leq \$500,000 \\
1.2 & \text{if } V > \$500,000
\end{cases}
$$

**Noise Term:**
$$
\epsilon_i \sim \mathcal{N}(0, (0.25 \cdot L_{\text{base},i})^2)
$$

**Final Constraint:**
$$
L_{\text{synthetic},i} = \min(\max(L_{\text{synthetic},i}, 0), 0.85)
$$

### **Model Implementation**

**Algorithm:** Random Forest Regressor with hyperparameters:
- Number of estimators: $n_{\text{trees}} = 100$
- Maximum depth: $d_{\max} = 12$  
- Minimum samples per split: $n_{\min,\text{split}} = 10$
- Minimum samples per leaf: $n_{\min,\text{leaf}} = 5$

**Training Objective:**
$$
\hat{F} = \arg\min_F \frac{1}{n} \sum_{i=1}^{n} \left( L_{\text{synthetic},i} - F(\mathbf{X}_i) \right)^2
$$

**Prediction:**
$$
\hat{L}_i = \hat{F}(\mathbf{X}_i)
$$

**Dollar Loss Estimate:**
$$
\text{TIV}_{\text{Dollar},i} = V_{\text{market},i} \times \hat{L}_i
$$

### **Model Validation Metrics**

1. **Coefficient of Determination:** $R^2 = 1 - \frac{\sum_{i=1}^{n}(y_i - \hat{y}_i)^2}{\sum_{i=1}^{n}(y_i - \bar{y})^2}$

2. **Root Mean Square Error:** $\text{RMSE} = \sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_i - \hat{y}_i)^2}$

3. **Physical Validation Correlations:**
   - $\rho(\text{MESH}, \hat{L}) > 0.3$ (larger hail → higher losses)
   - $\rho(A_{\text{building}}, \hat{L}) > 0.1$ (older buildings → higher vulnerability)  
   - $\rho(D_{\text{NCEI}}, \hat{L}) < -0.1$ (closer to reports → higher losses)

### **Data Sources**

- **Spatial Parcels:** Texas Strategic Mapping Program (StratMap) 2024
- **Property Values:** Dallas County Appraisal District (DCAD) 2024
- **Building Footprints:** Microsoft Global ML Building Footprints
- **Weather Data:** PPH (Practically Perfect Hindcasts), MESH radar, NCEI storm reports
- **Target Event:** May 19-20, 2023 Texas Hailstorm

### **Limitations**

1. **Synthetic Training Labels:** Model trained on physics-based synthetic losses rather than actual insurance claims
2. **Temporal Scope:** Single storm event validation  
3. **Spatial Scope:** Dallas County, Texas only
4. **Weather Simulation:** Proof-of-concept uses simulated weather features pending integration with actual storm data