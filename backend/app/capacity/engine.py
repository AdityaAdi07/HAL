import math
import numpy as np
from pydantic import BaseModel
from typing import List, Optional

class CapacitySnapshot(BaseModel):
    dept_id: str
    usable_h: float
    usable_h_p10: float
    workload_expected: float
    workload_p75: float
    workload_p90: float
    load_expected: float
    load_p75: float
    load_p90: float
    stress_load: float
    classification: str

def classify_load(usable_h: float, load_expected: float, load_risk: float) -> str:
    if usable_h == 0:
        return "UNAVAILABLE"
    
    # Boundary logic: 69.9 -> UNDERLOAD, 70 -> HEALTHY, 95 -> HEALTHY, 95.1 -> OVERLOAD
    if load_expected > 95.0:
        return "OVERLOAD"
    elif load_expected <= 95.0 and load_risk > 95.0:
        return "OVERLOAD_RISK"
    elif load_expected < 70.0:
        return "UNDERLOAD"
    else:
        return "HEALTHY"

def calculate_capacity(
    available_ws_h: float, 
    labour_h: float, 
    efficiency: float = 0.85, 
    material_factor: float = 1.0,
    pessimistic_factor: float = 0.8
):
    binding_h = min(available_ws_h, labour_h)
    usable_h = binding_h * efficiency * material_factor
    usable_h_p10 = usable_h * pessimistic_factor
    return usable_h, usable_h_p10

def monte_carlo_workload(units: List[dict], num_draws: int = 2000, seed: int = 42):
    """
    units: list of dicts with 'p50', 'p75', 'p90' expected hours.
    Returns (expected, p75, p90) aggregated workload.
    """
    if not units:
        return 0.0, 0.0, 0.0
        
    np.random.seed(seed)
    # Simulate lognormal for each unit. For simplicity, just use normal approx or triangle if stats missing
    # Since we need P90(agg) < sum(P90)
    
    total_draws = np.zeros(num_draws)
    
    for u in units:
        # Simplistic mapping: treating P50 as mean, and deriving std from P90
        # P90 = mean + 1.28 * std  => std = (P90 - P50) / 1.28
        p50 = u.get("p50", 1.0)
        p90 = u.get("p90", p50 * 1.2)
        
        std = (p90 - p50) / 1.28
        if std <= 0: std = 0.1
        
        draws = np.random.normal(p50, std, num_draws)
        draws = np.clip(draws, a_min=0, a_max=None)
        total_draws += draws
        
    expected = float(np.mean(total_draws))
    p75 = float(np.percentile(total_draws, 75))
    p90 = float(np.percentile(total_draws, 90))
    
    return expected, p75, p90

def build_snapshot(dept_id: str, available_ws_h: float, labour_h: float, units: List[dict]):
    usable_h, usable_h_p10 = calculate_capacity(available_ws_h, labour_h)
    
    workload_exp, workload_p75, workload_p90 = monte_carlo_workload(units)
    
    load_exp = (workload_exp / usable_h * 100) if usable_h > 0 else 0
    load_p75 = (workload_p75 / usable_h * 100) if usable_h > 0 else 0
    load_p90 = (workload_p90 / usable_h * 100) if usable_h > 0 else 0
    stress_load = (workload_p90 / usable_h_p10 * 100) if usable_h_p10 > 0 else 0
    
    classification = classify_load(usable_h, load_exp, load_p75) # using p75 as risk quantile
    
    return CapacitySnapshot(
        dept_id=dept_id,
        usable_h=usable_h,
        usable_h_p10=usable_h_p10,
        workload_expected=workload_exp,
        workload_p75=workload_p75,
        workload_p90=workload_p90,
        load_expected=load_exp,
        load_p75=load_p75,
        load_p90=load_p90,
        stress_load=stress_load,
        classification=classification
    )
