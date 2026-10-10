import pytest
from app.scheduling.optimizer import optimize_schedule, check_feasibility
from app.what_if.engine import WhatIfEngine

def test_optimizer_and_checker():
    # 3 tasks, 1 workstation, 2 workers
    # Total duration = 30 + 40 + 20 = 90
    tasks = [
        {"id": "T1", "duration": 30, "eligible_ws": ["WS1"], "eligible_workers": ["W1", "W2"]},
        {"id": "T2", "duration": 40, "eligible_ws": ["WS1"], "eligible_workers": ["W1"]},
        {"id": "T3", "duration": 20, "eligible_ws": ["WS1"], "eligible_workers": ["W2"]},
    ]
    
    result = optimize_schedule(tasks, ["WS1"], ["W1", "W2"], horizon=200)
    
    assert result["status"] in ["OPTIMAL", "FEASIBLE"]
    assert len(result["assignments"]) == 3
    
    # Run through independent checker
    is_feasible, reason = check_feasibility(result["assignments"])
    assert is_feasible == True
    
def test_checker_detects_overlap():
    bad_assignments = [
        {"task_id": "T1", "start": 0, "end": 50, "workstation": "WS1", "worker": "W1"},
        {"task_id": "T2", "start": 30, "end": 70, "workstation": "WS1", "worker": "W2"} # overlaps on WS1
    ]
    is_feasible, reason = check_feasibility(bad_assignments)
    assert is_feasible == False
    assert "Overlap on workstation WS1" in reason
    
def test_what_if_scenarios():
    engine = WhatIfEngine()
    
    current = {
        "capacity_h": 100.0,
        "workload_expected": 110.0,
        "load_expected": 110.0 # OVERLOAD
    }
    
    # E2 - Overtime mitigation
    res = engine.evaluate_scenario("OVERTIME", current, {"hours": 2, "workers": 5}) # adds 10h
    
    assert res["after"]["capacity_h"] == 110.0
    assert res["after"]["load_expected"] == 100.0
    assert res["delta"]["load_expected"] == -10.0
