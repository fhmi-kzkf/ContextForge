import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report
import joblib
import os

# Load data
df = pd.read_csv("data/churn.csv")

# Features and target
FEATURES = ["tenure", "monthly_charges", "total_charges", "num_products", "has_internet", "has_phone"]
TARGET = "churned"

X = df[FEATURES]
y = df[TARGET]

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Build pipeline
pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", RandomForestClassifier(n_estimators=100, random_state=42))
])

# Train
pipeline.fit(X_train, y_train)

# Evaluate
preds = pipeline.predict(X_test)
print(classification_report(y_test, preds))

# Save
os.makedirs("model", exist_ok=True)
joblib.dump(pipeline, "model/churn_model.pkl")
print("Model saved to model/churn_model.pkl")
