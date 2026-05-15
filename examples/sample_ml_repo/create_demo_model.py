"""
Run this script once to create a fake trained model for demo purposes.
This avoids needing the actual churn.csv dataset.
Usage: python create_demo_model.py
"""
import numpy as np
import joblib
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

np.random.seed(42)
n = 500

X = np.column_stack([
    np.random.randint(1, 72, n),          # tenure (months)
    np.random.uniform(20, 120, n),         # monthly_charges
    np.random.uniform(20, 8000, n),        # total_charges
    np.random.randint(1, 5, n),            # num_products
    np.random.randint(0, 2, n),            # has_internet
    np.random.randint(0, 2, n),            # has_phone
])

# Churn more likely when tenure < 12 and monthly_charges > 80
y = ((X[:, 0] < 12) & (X[:, 1] > 80)).astype(int)
y = np.where(np.random.random(n) < 0.1, 1 - y, y)  # add noise

pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", RandomForestClassifier(n_estimators=100, random_state=42))
])
pipeline.fit(X, y)

os.makedirs("model", exist_ok=True)
joblib.dump(pipeline, "model/churn_model.pkl")
print("Demo model created at model/churn_model.pkl")
print("Test prediction:", pipeline.predict([[12, 65.5, 786.0, 2, 1, 1]]))
