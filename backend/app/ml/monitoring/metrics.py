import numpy as np
import pandas as pd

def calculate_psi(expected, actual, buckets=10):
    """
    Calculate Population Stability Index (PSI) to detect data drift.
    """
    def scale_range (input, min, max):
        input += -(np.min(input))
        input /= np.max(input) / (max - min)
        input += min
        return input

    breakpoints = np.arange(0, buckets + 1) / (buckets) * 100
    breakpoints = scale_range(breakpoints, np.min(expected), np.max(expected))
    
    expected_percents = np.histogram(expected, breakpoints)[0] / len(expected)
    actual_percents = np.histogram(actual, breakpoints)[0] / len(actual)
    
    # Avoid div by 0
    expected_percents = np.where(expected_percents == 0, 0.0001, expected_percents)
    actual_percents = np.where(actual_percents == 0, 0.0001, actual_percents)
    
    psi_value = np.sum((actual_percents - expected_percents) * np.log(actual_percents / expected_percents))
    return float(psi_value)

def monitor_model_performance(y_true, y_pred_p75, y_pred_p90, train_features=None, live_features=None):
    """
    Evaluates monitoring metrics per Phase 9.
    Checks P75, P90 coverage, and PSI drift on features if provided.
    """
    coverage_p75 = np.mean(y_true <= y_pred_p75)
    coverage_p90 = np.mean(y_true <= y_pred_p90)
    
    drift_detected = False
    psi_scores = {}
    
    if train_features is not None and live_features is not None:
        for col in train_features.columns:
            if col in live_features:
                psi = calculate_psi(train_features[col].values, live_features[col].values)
                psi_scores[col] = psi
                if psi > 0.2: # Standard threshold for significant drift
                    drift_detected = True
                    
    recommend_retrain = False
    # If coverage drops significantly below target or significant drift is detected
    if coverage_p75 < 0.65 or coverage_p90 < 0.80 or drift_detected:
        recommend_retrain = True
        
    return {
        "coverage_p75": float(coverage_p75),
        "coverage_p90": float(coverage_p90),
        "drift_detected": drift_detected,
        "psi_scores": psi_scores,
        "recommend_retrain": recommend_retrain
    }
