class WhatIfEngine:
    def __init__(self):
        pass
        
    def evaluate_scenario(self, scenario_type: str, current_metrics: dict, params: dict):
        """
        scenario_type: WORKER_ABSENCE, ADD_SHIFT, LOAN_WORKER, etc.
        Returns BEFORE, AFTER, DELTA metrics.
        """
        before = current_metrics.copy()
        after = current_metrics.copy()
        
        # Very simplified mock impact logic for Phase 8 exit criteria
        if scenario_type == "WORKER_ABSENCE":
            after["load_expected"] = before["load_expected"] * 1.5
            after["capacity_h"] = before["capacity_h"] * 0.6
            
        elif scenario_type == "LOAN_WORKER":
            # Loaning workers into this dept
            after["capacity_h"] = before["capacity_h"] + (8.0 * params.get("workers", 1))
            after["load_expected"] = before["workload_expected"] / after["capacity_h"] * 100
            
        elif scenario_type == "OVERTIME":
            after["capacity_h"] = before["capacity_h"] + (params.get("hours", 2) * params.get("workers", 1))
            after["load_expected"] = before["workload_expected"] / after["capacity_h"] * 100
            
        delta = {
            "load_expected": after["load_expected"] - before["load_expected"],
            "capacity_h": after["capacity_h"] - before["capacity_h"]
        }
        
        return {
            "before": before,
            "after": after,
            "delta": delta,
            "recommended_action": "Proceed with loan" if after["load_expected"] < 95.0 else "Insufficient impact"
        }
