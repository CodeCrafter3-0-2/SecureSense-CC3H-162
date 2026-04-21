import numpy as np

# Simple statistical anomaly detector (fast + no retraining needed)
def anomaly_score(features: dict):
    values = np.array(list(features.values()))

    # Normalize
    mean = np.mean(values)
    std = np.std(values) + 1e-6

    z_scores = np.abs((values - mean) / std)

    # Score = average deviation
    score = float(np.mean(z_scores))

    return score


def is_anomaly(features: dict, threshold=0.8):
    score = anomaly_score(features)
    return score > threshold, score