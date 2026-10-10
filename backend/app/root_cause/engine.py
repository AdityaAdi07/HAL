def analyze_root_cause(dept_id: str, snapshot_class: str, context: dict):
    """
    context holds info like:
    {
       "demand_low": bool,
       "material_blocking": bool,
       "worker_absence": bool,
       "upstream_starvation": bool,
       "evidence": str
    }
    """
    if snapshot_class == "UNDERLOAD":
        if context.get("demand_low"):
            cause = "LOW_DEMAND"
        elif context.get("material_blocking"):
            cause = "MATERIAL_SHORTAGE"
        elif context.get("worker_absence"):
            cause = "WORKER_ABSENCE"
        elif context.get("upstream_starvation"):
            cause = "UPSTREAM_STARVATION"
        else:
            cause = "UNKNOWN_UNDERLOAD"
            
        return {
            "problem": f"{dept_id} is underloaded",
            "cause": cause,
            "evidence": context.get("evidence", ""),
            "confidence": "HIGH" if cause != "UNKNOWN_UNDERLOAD" else "LOW",
            "action": "Rebalance workers or expedite upstream" if cause == "UPSTREAM_STARVATION" else "Investigate",
            "impact": "Restore throughput"
        }
    return None
