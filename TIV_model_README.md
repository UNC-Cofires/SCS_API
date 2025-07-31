# 📄 Total Insured Value (TIV) Loss Prediction Model

## 🎯 Overview

This repository contains a machine learning model for predicting Total Insured Value (TIV) losses from severe weather events, specifically hailstorms. The model integrates weather data, property characteristics, and building features to estimate percentage losses for insurance applications.

## 📊 Mathematical Framework

The Total Insured Value loss percentage for property *i* at location (φ_i, λ_i) during storm event *d* is modeled as:

```
TIV_Loss,i(d, φ_i, λ_i) = F(X_i) × 100%
```

where:
- **F**: ℝ¹² → [0, 1] is a Random Forest regression model 
- **X_i**: 12-dimensional feature vector for property *i*
- Result is scaled to percentage loss

## 🔧 Feature Vector Specification

The 12-dimensional feature vector **X_i** ∈ ℝ¹² comprises three categories:

### 🌪️ Weather Features (4 features)

| Feature | Symbol | Description | Units |
|---------|--------|-------------|-------|
| MESH Value | MESH_i | Maximum Estimated Size of Hail | inches |
| PPH Probability | P_PPH,i | Practically Perfect Hindcast probability | [0,1] |
| NCEI Distance | D_NCEI,i | Distance to nearest NCEI severe weather report | km |
| Storm Duration | T_storm,i | Storm duration at location | hours |

**Weather Feature Vector:**
```
W_i = [MESH_i, P_PPH,i, D_NCEI,i, T_storm,i]ᵀ
```

### 🏠 Property Features (5 features)

| Feature | Symbol | Description | Values/Units |
|---------|--------|-------------|--------------|
| Market Value | V_market,i | Market value from tax appraisal | USD |
| Building Age | A_building,i | Building age = 2024 - Year Built | years |
| Living Area | S_living,i | Living area | square feet |
| Construction Quality | Q_construction,i | Construction quality rating | {0,1,2,3,4} |
| Frame Type | F_frame,i | Frame type encoding | {1,2,3} |

**Construction Quality Scale:**
- 0 = Poor
- 1 = Fair  
- 2 = Average
- 3 = Good
- 4 = Excellent

**Frame Type Encoding:**
- 1 = Wood
- 2 = Metal
- 3 = Masonry

**Property Feature Vector:**
```
P_i = [V_market,i, A_building,i, S_living,i, Q_construction,i, F_frame,i]ᵀ
```

### 🏗️ Building Features (3 features)

| Feature | Symbol | Description | Units |
|---------|--------|-------------|-------|
| Footprint Area | A_footprint,i | Building footprint area (Microsoft ML) | square feet |
| Building Complexity | C_complexity,i | Complexity ratio = Perimeter/√Area | dimensionless |
| Building Density | ρ_density,i | Local building density | buildings/hectare |

**Building Feature Vector:**
```
B_i = [A_footprint,i, C_complexity,i, ρ_density,i]ᵀ
```

### 📐 Complete Feature Vector

```
X_i = [W_i; P_i; B_i] ∈ ℝ¹²
```

## 🧮 Synthetic Loss Function (Training Labels)

For model training, synthetic TIV losses are generated using domain knowledge:

```
L_synthetic,i = β₀(MESH_i) × β₁(A_building,i) × β₂(Q_construction,i) × β₃(F_frame,i) × β₄(P_PPH,i) × β₅(D_NCEI,i) × β₆(V_market,i) + εᵢ
```

### 📊 Loss Function Components

#### 1. Base Damage Function β₀(MESH)

| MESH Range (inches) | Base Damage |
|---------------------|-------------|
| < 0.5 | 0.005 (0.5%) |
| 0.5 - 1.0 | 0.02 (2%) |
| 1.0 - 1.5 | 0.08 (8%) |
| 1.5 - 2.0 | 0.20 (20%) |
| ≥ 2.0 | 0.45 (45%) |

#### 2. Age Vulnerability Multiplier β₁(A)

```
β₁(A) = min(1.0 + max(0, (A - 20) × 0.015), 2.5)
```
- Buildings over 20 years old get 1.5% vulnerability increase per year
- Capped at 2.5× multiplier

#### 3. Quality Factor β₂(Q)

```
β₂(Q) = 1.5 - (Q × 0.15)
```
- Better construction quality reduces damage
- Range: 0.9 (Excellent) to 1.5 (Poor)

#### 4. Frame Type Factor β₃(F)

| Frame Type | Factor |
|------------|--------|
| Wood (1) | 1.3 |
| Metal (2) | 1.0 |
| Masonry (3) | 0.7 |

#### 5. Forecast Factor β₄(P)

```
β₄(P) = 0.5 + 1.5P
```
- Higher PPH probability correlates with higher actual damage
- Range: 0.5 to 2.0

#### 6. Distance Decay β₅(D)

```
β₅(D) = e^(-D/4.0)
```
- Exponential decay with distance from NCEI reports
- Properties closer to reports have higher losses

#### 7. Exposure Factor β₆(V)

| Property Value | Factor |
|----------------|--------|
| < $100,000 | 0.8 |
| $100,000 - $500,000 | 1.0 |
| > $500,000 | 1.2 |

#### 8. Noise Term

```
εᵢ ~ N(0, (0.25 × L_base,i)²)
```
- Gaussian noise proportional to base loss
- Adds realistic variability

#### 9. Final Constraint

```
L_synthetic,i = min(max(L_synthetic,i, 0), 0.85)
```
- Losses bounded between 0% and 85%

## 🤖 Model Implementation

### Algorithm: Random Forest Regressor

| Hyperparameter | Value | Description |
|----------------|-------|-------------|
| n_estimators | 100 | Number of decision trees |
| max_depth | 12 | Maximum tree depth |
| min_samples_split | 10 | Minimum samples to split node |
| min_samples_leaf | 5 | Minimum samples per leaf |
| random_state | 42 | Reproducibility seed |

### Training Objective

The model minimizes mean squared error:

```
F̂ = argmin_F (1/n) Σᵢ₌₁ⁿ (L_synthetic,i - F(Xᵢ))²
```

### Prediction Process

1. **Loss Percentage Prediction:**
   ```
   L̂ᵢ = F̂(Xᵢ)
   ```

2. **Dollar Loss Estimate:**
   ```
   TIV_Dollar,i = V_market,i × L̂ᵢ
   ```

## 📈 Model Validation

### Performance Metrics

1. **Coefficient of Determination:**
   ```
   R² = 1 - (Σ(yᵢ - ŷᵢ)²) / (Σ(yᵢ - ȳ)²)
   ```

2. **Root Mean Square Error:**
   ```
   RMSE = √((1/n) Σ(yᵢ - ŷᵢ)²)
   ```

### Physical Validation Tests

The model must pass these correlation tests:

| Relationship | Expected | Interpretation |
|-------------|----------|----------------|
| ρ(MESH, L̂) | > 0.3 | Larger hail → higher losses |
| ρ(Age, L̂) | > 0.1 | Older buildings → higher vulnerability |
| ρ(Distance, L̂) | < -0.1 | Closer to reports → higher losses |

## 📊 Data Sources

| Category | Source | Description |
|----------|--------|-------------|
| **Spatial Parcels** | Texas Strategic Mapping Program (StratMap) 2024 | Property boundaries and identifiers |
| **Property Values** | Dallas County Appraisal District (DCAD) 2024 | Tax assessments and building characteristics |
| **Building Footprints** | Microsoft Global ML Building Footprints | Precise building geometry |
| **Weather Data** | PPH, MESH radar, NCEI storm reports | Storm characteristics and impact |
| **Target Event** | May 19-20, 2023 Texas Hailstorm | Validation case study |

## ⚠️ Current Limitations

| Limitation | Impact | Future Resolution |
|------------|--------|-------------------|
| **Synthetic Training Labels** | Model trained on physics-based estimates, not actual claims | Integrate real insurance claims data |
| **Temporal Scope** | Single storm event validation | Expand to multi-year validation dataset |
| **Spatial Scope** | Dallas County, Texas only | Scale to multi-state implementation |
| **Weather Simulation** | Proof-of-concept uses simulated weather | Integrate real-time weather data APIs |

## 🚀 Getting Started

### Prerequisites

```bash
pip install pandas geopandas numpy scikit-learn matplotlib shapely
```

### Basic Usage

```python
from tiv_model import TIVLossPredictor

# Initialize model
model = TIVLossPredictor()

# Load your property data
properties = load_property_data("path/to/parcels.shp")

# Add weather features for storm event
properties = add_weather_features(properties, storm_date="2023-05-19")

# Predict losses
losses = model.predict(properties)

# Calculate dollar losses
dollar_losses = properties['market_value'] * losses
```

### Example Results

For a typical Dallas property:
- **Market Value:** $250,000
- **MESH:** 1.2 inches
- **Building Age:** 15 years
- **Construction:** Good quality, wood frame

**Predicted Loss:** 12.3% → **$30,750**

## 📝 Citation

If you use this model in academic research, please cite:

```
TIV Loss Prediction Model for Severe Weather Events
Dallas County Implementation, 2024
GitHub: UNC-Cofires/SCS_API
```

## 📞 Contact

For questions or collaboration opportunities:
- Repository: [UNC-Cofires/SCS_API](https://github.com/UNC-Cofires/SCS_API)
- Issues: [GitHub Issues](https://github.com/UNC-Cofires/SCS_API/issues)