import pytest
from app.capacity.engine import classify_load, monte_carlo_workload, build_snapshot
from app.root_cause.engine import analyze_root_cause
from fastapi.testclient import TestClient
from app.main import app

def test_load_classification_boundaries():
    assert classify_load(100.0, 69.9, 75.0) == "UNDERLOAD"
    assert classify_load(100.0, 70.0, 75.0) == "HEALTHY"
    assert classify_load(100.0, 95.0, 90.0) == "HEALTHY"
    assert classify_load(100.0, 95.1, 95.1) == "OVERLOAD"
    assert classify_load(100.0, 90.0, 96.0) == "OVERLOAD_RISK"
    assert classify_load(0.0, 0.0, 0.0) == "UNAVAILABLE"

def test_monte_carlo_aggregation():
    # If we have 2 identical units, P90 of sum should be less than sum of P90s
    units = [
        {"p50": 10.0, "p90": 15.0},
        {"p50": 10.0, "p90": 15.0}
    ]
    
    expected, p75, p90_agg = monte_carlo_workload(units)
    # Sum of P90s is 30.0
    # Aggregated P90 should be strictly less than 30.0 because of pooling variance
    assert p90_agg < 30.0
    assert p90_agg > 20.0 # Must be greater than sum of means

def test_root_cause_e1():
    # Example E1 (SENS underload cause)
    result = analyze_root_cause(
        "DEPT-SENS", 
        "UNDERLOAD", 
        {"upstream_starvation": True}
    )
    assert result is not None
    assert result["cause"] == "UPSTREAM_STARVATION"

client = TestClient(app)

def test_snapshot_api():
    response = client.get("/api/capacity/departments/DEPT-SENS/snapshot")
    assert response.status_code == 200
    data = response.json()
    assert "usable_h" in data
    assert "classification" in data
    assert data["classification"] in ["UNDERLOAD", "HEALTHY", "OVERLOAD", "OVERLOAD_RISK"]
