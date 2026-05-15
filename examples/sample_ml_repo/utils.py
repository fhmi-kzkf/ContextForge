import json
import os
from datetime import datetime

def save_prediction_log(input_data, result, log_dir="logs"):
    os.makedirs(log_dir, exist_ok=True)
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "input": input_data,
        "result": result
    }
    log_path = os.path.join(log_dir, "predictions.jsonl")
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")

def load_config(config_path="config.json"):
    if not os.path.exists(config_path):
        return {}
    with open(config_path) as f:
        return json.load(f)
