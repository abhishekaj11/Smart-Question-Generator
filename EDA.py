# ==========================================================
# 📊 COMPLETE EDA VISUALIZATION SCRIPT
# ==========================================================

# Importing the essentials
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px


df = pd.read_csv('college_syllabus_dataset_35000.csv')  # replace with your dataset path

# Optional: make plots look clean
sns.set(style="whitegrid", palette="pastel", font_scale=1.1)
plt.rcParams['figure.figsize'] = (10, 6)

# ==========================================================
# 1️⃣ Basic Info & Summary
# ==========================================================

print("Dataset Shape:", df.shape)
print("\nData Types:\n", df.dtypes)
print("\nMissing Values:\n", df.isnull().sum())
print("\nDuplicate Rows:", df.duplicated().sum())
print(df.describe(include='all'))

# ==========================================================
# 2️⃣ Univariate Analysis
# ==========================================================

# Separate numerical and categorical columns
num_cols = df.select_dtypes(include=np.number).columns.tolist()
cat_cols = df.select_dtypes(exclude=np.number).columns.tolist()

# --- Numerical features: Histogram, Boxplot, KDE
for col in num_cols:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    sns.histplot(df[col], kde=True, ax=axes[0], color='skyblue')
    axes[0].set_title(f'Distribution of {col}')
    sns.boxplot(x=df[col], ax=axes[1], color='lightcoral')
    axes[1].set_title(f'Boxplot of {col}')
    plt.show()

# --- Categorical features: Count plot
for col in cat_cols:
    plt.figure(figsize=(8, 4))
    sns.countplot(y=df[col], order=df[col].value_counts().index, palette="viridis")
    plt.title(f'Count Plot of {col}')
    plt.show()

# ==========================================================
# 3️⃣ Bivariate Analysis
# ==========================================================

# --- Correlation Heatmap (for numerical features)
plt.figure(figsize=(10, 6))
sns.heatmap(df[num_cols].corr(), annot=True, cmap='coolwarm', fmt='.2f')
plt.title('Correlation Heatmap')
plt.show()

# --- Scatter plots (numerical vs numerical)
if len(num_cols) >= 2:
    for i in range(min(len(num_cols), 3)):  # limit for readability
        for j in range(i+1, min(len(num_cols), 4)):
            sns.scatterplot(x=df[num_cols[i]], y=df[num_cols[j]], alpha=0.7)
            plt.title(f'{num_cols[i]} vs {num_cols[j]}')
            plt.show()

# --- Boxplots (numerical vs categorical)
for cat in cat_cols:
    for num in num_cols:
        if df[cat].nunique() < 10:  # only for small number of categories
            plt.figure(figsize=(8, 4))
            sns.boxplot(x=cat, y=num, data=df)
            plt.title(f'{num} across {cat}')
            plt.xticks(rotation=30)
            plt.show()

# ==========================================================
# 4️⃣ Multivariate Analysis
# ==========================================================

# Pair Plot (only if dataset not too large)
if len(num_cols) <= 6:
    sns.pairplot(df[num_cols])
    plt.show()

# Parallel Coordinates (optional)
try:
    from pandas.plotting import parallel_coordinates
    sample = df.copy()
    if cat_cols:
        parallel_coordinates(sample, class_column=cat_cols[0], color=sns.color_palette("husl"))
        plt.title(f'Parallel Coordinates based on {cat_cols[0]}')
        plt.show()
except Exception as e:
    print("Parallel coordinates skipped:", e)

# ==========================================================
# 5️⃣ Outlier Detection
# ==========================================================

for col in num_cols:
    sns.boxplot(x=df[col], color='tomato')
    plt.title(f'Outlier Check for {col}')
    plt.show()

# ==========================================================
# 6️⃣ Relationship with Target Variable (if available)
# ==========================================================

target_col = 'target'  # replace with your actual target column name if available

if target_col in df.columns:
    # Numerical vs Target
    for num in num_cols:
        if num != target_col:
            sns.scatterplot(x=df[num], y=df[target_col])
            plt.title(f'{num} vs {target_col}')
            plt.show()

    # Categorical vs Target
    for cat in cat_cols:
        sns.boxplot(x=df[cat], y=df[target_col])
        plt.title(f'{target_col} across {cat}')
        plt.xticks(rotation=30)
        plt.show()

# ==========================================================
# 7️⃣ Interactive Visuals (Plotly)
# ==========================================================

# Example: 2D interactive scatter plot
if len(num_cols) >= 2:
    fig = px.scatter(df, x=num_cols[0], y=num_cols[1], color=cat_cols[0] if cat_cols else None,
                     title=f'Interactive {num_cols[0]} vs {num_cols[1]}')
    fig.show()


if cat_cols:
    fig = px.pie(df, names=cat_cols[0], title=f'Pie Chart of {cat_cols[0]}')
    fig.show()


plt.figure(figsize=(10, 5))
sns.heatmap(df.isnull(), cbar=False, cmap='viridis')
plt.title('Missing Values Heatmap')
plt.show()



print("\n✅ EDA Completed Successfully!")
print(f"Total Numerical Columns: {len(num_cols)} | Categorical Columns: {len(cat_cols)}")
print("Now interpret trends, correlations, and outliers based on the visuals above.")
