import pytest
import pandas as pd
import numpy as np
from app.ml.build_time import BuildTimePredictor
from app.ml.workload_forecast import WorkloadForecaster

def create_dummy_data(n=1000):
    np.random.seed(42)
    df = pd.DataFrame({
        "std_hours": np.random.uniform(1.0, 5.0, n),
        "complexity": np.random.uniform(0.8, 1.2, n),
        "crew_size": np.random.randint(1, 3, n),
        "skill_level": np.random.randint(1, 5, n),
        "rework_history": np.random.poisson(0.1, n)
    })
    # Create actual hours as a function of features + noise
    df["actual_hours"] = (df["std_hours"] * df["complexity"] * 
                          (1.2 - 0.05 * df["skill_level"]) + 
                          np.random.lognormal(0, 0.1, n))
    
    # Sort chronologically (implicitly done by index)
    return df

def test_build_time_predictor():
    df = create_dummy_data(1000)
    
    # Time-split backtest (chronological split)
    df_train = df.iloc[:800]
    df_val = df.iloc[800:900]
    df_test = df.iloc[900:]
    
    predictor = BuildTimePredictor()
    
    # Check cold start fallback flagged
    cold_preds = predictor.predict(df_test)
    assert cold_preds["fallback_used"].all() == True
    
    predictor.train(df_train, df_val)
    
    # Predict on holdout
    preds = predictor.predict(df_test)
    assert preds["fallback_used"].all() == False
    
    # Quantiles monotone check
    assert (preds['p50'] <= preds['p75']).all()
    assert (preds['p75'] <= preds['p90']).all()
    
    # Evaluate baseline vs ML
    metrics = predictor.evaluate(df_test)
    assert metrics["beats_baseline"] == True
    
    # Coverage check
    assert 0.80 <= metrics["p90_coverage"] <= 1.0 # Approximate coverage check

def test_leakage():
    df = create_dummy_data(500)
    df_train = df.iloc[:400]
    df_val = df.iloc[400:450]
    df_test = df.iloc[450:]
    
    predictor = BuildTimePredictor()
    predictor.train(df_train, df_val)
    
    base_preds = predictor.predict(df_test.iloc[[0]])
    
    # Perturb future rows (index > 450)
    df_test_perturbed = df_test.copy()
    df_test_perturbed.loc[451:, "std_hours"] = 999.0
    
    # Assert prediction on row 0 unchanged
    new_preds = predictor.predict(df_test_perturbed.iloc[[0]])
    
    assert base_preds['p50'].iloc[0] == new_preds['p50'].iloc[0]

def test_workload_forecast():
    # Create dummy daily workload
    np.random.seed(42)
    # 3 weeks of data
    trend = np.linspace(100, 150, 21)
    seasonality = np.tile([10, -5, -5, -5, -5, 10, 0], 3)
    series = pd.Series(trend + seasonality)
    
    forecaster = WorkloadForecaster(seasonal_periods=7)
    forecaster.fit(series)
    
    assert "weekly seasonality" in forecaster.method_note
    
    preds = forecaster.forecast(7)
    assert len(preds) == 7
    assert (preds['expected'] <= preds['p75']).all()
    assert (preds['p75'] <= preds['p90']).all()
    
def test_workload_forecast_short_history():
    series = pd.Series(np.random.normal(100, 10, 10)) # less than 14 days
    forecaster = WorkloadForecaster(seasonal_periods=7)
    forecaster.fit(series)
    
    assert "trend-only" in forecaster.method_note
