from ortools.sat.python import cp_model

def optimize_schedule(tasks, workstations, workers, horizon=7*24*60):
    """
    tasks: list of dicts: id, duration (minutes), eligible_ws, eligible_workers
    workstations: list of ids
    workers: list of ids
    horizon: scheduling horizon in minutes
    """
    model = cp_model.CpModel()
    
    # Variables
    # task_vars[t_id] = { start, end, interval, ws_vars, worker_vars }
    task_vars = {}
    ws_intervals = {ws: [] for ws in workstations}
    worker_intervals = {w: [] for w in workers}
    
    for t in tasks:
        t_id = t["id"]
        dur = int(t["duration"])
        
        start = model.NewIntVar(0, horizon, f'start_{t_id}')
        end = model.NewIntVar(0, horizon, f'end_{t_id}')
        interval = model.NewIntervalVar(start, dur, end, f'interval_{t_id}')
        
        ws_vars = {}
        for ws in t["eligible_ws"]:
            # Optional interval for each possible workstation
            ws_pres = model.NewBoolVar(f'ws_pres_{t_id}_{ws}')
            ws_start = model.NewIntVar(0, horizon, f'ws_start_{t_id}_{ws}')
            ws_end = model.NewIntVar(0, horizon, f'ws_end_{t_id}_{ws}')
            ws_int = model.NewOptionalIntervalVar(ws_start, dur, ws_end, ws_pres, f'ws_int_{t_id}_{ws}')
            
            ws_vars[ws] = ws_pres
            ws_intervals[ws].append(ws_int)
            
            # Sync optional interval with main interval if selected
            model.Add(start == ws_start).OnlyEnforceIf(ws_pres)
            model.Add(end == ws_end).OnlyEnforceIf(ws_pres)
            
        # Must pick exactly one workstation
        model.AddExactlyOne(ws_vars.values())
        
        w_vars = {}
        for w in t["eligible_workers"]:
            w_pres = model.NewBoolVar(f'w_pres_{t_id}_{w}')
            w_start = model.NewIntVar(0, horizon, f'w_start_{t_id}_{w}')
            w_end = model.NewIntVar(0, horizon, f'w_end_{t_id}_{w}')
            w_int = model.NewOptionalIntervalVar(w_start, dur, w_end, w_pres, f'w_int_{t_id}_{w}')
            
            w_vars[w] = w_pres
            worker_intervals[w].append(w_int)
            
            model.Add(start == w_start).OnlyEnforceIf(w_pres)
            model.Add(end == w_end).OnlyEnforceIf(w_pres)
            
        # Must pick exactly one worker (assuming crew_size = 1 for simplicity in this stub)
        model.AddExactlyOne(w_vars.values())
        
        task_vars[t_id] = {
            'start': start,
            'end': end,
            'interval': interval,
            'ws_vars': ws_vars,
            'w_vars': w_vars
        }
        
    # No overlap constraints
    for ws in workstations:
        if ws_intervals[ws]:
            model.AddNoOverlap(ws_intervals[ws])
            
    for w in workers:
        if worker_intervals[w]:
            model.AddNoOverlap(worker_intervals[w])
            
    # Objective: minimize makespan
    makespan = model.NewIntVar(0, horizon, 'makespan')
    model.AddMaxEquality(makespan, [tv['end'] for tv in task_vars.values()])
    model.Minimize(makespan)
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5.0
    status = solver.Solve(model)
    
    result = {
        "status": solver.StatusName(status),
        "assignments": []
    }
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for t in tasks:
            t_id = t["id"]
            assigned_ws = None
            assigned_w = None
            
            for ws, var in task_vars[t_id]['ws_vars'].items():
                if solver.Value(var):
                    assigned_ws = ws
                    break
                    
            for w, var in task_vars[t_id]['w_vars'].items():
                if solver.Value(var):
                    assigned_w = w
                    break
                    
            result["assignments"].append({
                "task_id": t_id,
                "start": solver.Value(task_vars[t_id]['start']),
                "end": solver.Value(task_vars[t_id]['end']),
                "workstation": assigned_ws,
                "worker": assigned_w
            })
            
    return result

def check_feasibility(assignments):
    """Independent Feasibility Checker"""
    ws_timeline = {}
    w_timeline = {}
    
    for a in assignments:
        ws = a["workstation"]
        w = a["worker"]
        s = a["start"]
        e = a["end"]
        
        if ws not in ws_timeline:
            ws_timeline[ws] = []
        for prev_s, prev_e in ws_timeline[ws]:
            if not (e <= prev_s or s >= prev_e):
                return False, f"Overlap on workstation {ws}"
        ws_timeline[ws].append((s, e))
        
        if w not in w_timeline:
            w_timeline[w] = []
        for prev_s, prev_e in w_timeline[w]:
            if not (e <= prev_s or s >= prev_e):
                return False, f"Overlap on worker {w}"
        w_timeline[w].append((s, e))
        
    return True, "Feasible"
