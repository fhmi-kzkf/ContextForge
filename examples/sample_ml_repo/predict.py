import joblib
import numpy as np

# Load model once at module level
model = joblib.load("model/churn_model.pkl")

FEATURE_ORDER = ["tenure", "monthly_charges", "total_charges", "num_products", "has_internet", "has_phone"]

def predict(customer_data):
    # customer_data is a dict like:
    # {"tenure": 12, "monthly_charges": 65.5, "total_charges": 786.0,
    #  "num_products": 2, "has_internet": 1, "has_phone": 1}
    features = [customer_data[f] for f in FEATURE_ORDER]
    arr = np.array(features).reshape(1, -1)
    prediction = model.predict(arr)[0]
    probability = model.predict_proba(arr)[0]
    return {
        "churned": bool(prediction),
        "churn_probability": round(float(probability[1]), 4),
        "confidence": round(float(max(probability)), 4)
    }

def batch_predict(customers):
    # customers is a list of dicts
    return [predict(c) for c in customers]

def get_feature_importance():
    clf = model.named_steps["clf"]
    return dict(zip(FEATURE_ORDER, clf.feature_importances_.tolist()))
