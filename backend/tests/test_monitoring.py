import pytest
import numpy as np
import pandas as pd
from app.ml.monitoring.metrics import calculate_psi, monitor_model_performance
from app.ml.retraining.manager import ModelManager

def test_psi_calculation():
    np.random.seed(42)
    expected = np.random.normal(0, 1, 1000)
    actual_similar = np.random.normal(0, 1, 1000)
    actual_drifted = np.random.normal(2, 1, 1000)
    
    psi_similar = calculate_psi(expected, actual_similar)
    psi_drifted = calculate_psi(expected, actual_drifted)
    
    assert psi_similar < 0.1 # Should be very low
    assert psi_drifted > 0.2 # Should be high (drift detected)
    
def test_monitoring_recommends_retrain():
    train_df = pd.DataFrame({"feat1": np.random.normal(0, 1, 1000)})
    live_df = pd.DataFrame({"feat1": np.random.normal(3, 1, 1000)}) # High drift
    
    # Dummy predictions
    y_true = np.array([1, 2, 3])
    y_pred_p75 = np.array([2, 3, 4]) # 100% coverage
    y_pred_p90 = np.array([3, 4, 5])
    
    res = monitor_model_performance(y_true, y_pred_p75, y_pred_p90, train_df, live_df)
    
    assert res["drift_detected"] == True
    assert res["recommend_retrain"] == True
    
def test_retraining_manager():
    manager = ModelManager()
    
    # Challenger beats overall but regresses on overload
    challenger_metrics = {"mae": 5.0}
    champion_metrics = {"mae": 10.0}
    overload_metrics = {"challenger_mae": 12.0, "champion_mae": 8.0}
    
    decision = manager.evaluate_challenger(challenger_metrics, champion_metrics, overload_metrics)
    assert decision == "REJECT_DUE_TO_OVERLOAD_REGRESSION"
    
    # Challenger beats overall and improves on overload
    overload_metrics_2 = {"challenger_mae": 6.0, "champion_mae": 8.0}
    decision2 = manager.evaluate_challenger(challenger_metrics, champion_metrics, overload_metrics_2)
    assert decision2 == "PROMOTE"
    
    manager.promote_challenger("v2.0")
    assert manager.models["CHAMPION"] == "v2.0"
    assert manager.models["PREVIOUS"] == "v1.0"
    
    # Rollback
    did_rollback = manager.rollback()
    assert did_rollback == True
    assert manager.models["CHAMPION"] == "v1.0"
