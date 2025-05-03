# agents/flaky_detector.py
import joblib
import numpy as np

class FlakyDetectorAgent:
    def __init__(self, model_path="flake_model.txt"):
        self.model = joblib.load(model_path)

    def score(self, features: dict) -> float:
        vals = np.array([features[k] for k in sorted(features)])
        return float(self.model.predict_proba(vals.reshape(1, -1))[0][1])
