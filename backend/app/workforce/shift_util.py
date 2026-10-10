import datetime

MAX_H_PER_DAY = 12.0

def parse_time(time_str: str) -> datetime.time:
    """Parses 'HH:MM:SS' into datetime.time"""
    parts = time_str.split(":")
    return datetime.time(hour=int(parts[0]), minute=int(parts[1]), second=int(parts[2]) if len(parts) > 2 else 0)

def calculate_duration_h(start_time: str, end_time: str) -> float:
    """Calculates duration in hours between two times, handling cross-midnight"""
    start = parse_time(start_time)
    end = parse_time(end_time)
    
    start_td = datetime.timedelta(hours=start.hour, minutes=start.minute, seconds=start.second)
    end_td = datetime.timedelta(hours=end.hour, minutes=end.minute, seconds=end.second)
    
    if end_td < start_td:
        # Crosses midnight
        end_td += datetime.timedelta(days=1)
        
    duration = (end_td - start_td).total_seconds() / 3600.0
    return duration

def check_worker_rules(existing_shifts: list[dict], new_shift: dict) -> bool:
    """
    existing_shifts: list of dicts {"start_time": str, "end_time": str, "planned_hours": float}
    new_shift: dict {"start_time": str, "end_time": str, "planned_hours": float}
    """
    # Rule: 1 shift template per day (assuming existing_shifts are on the same day)
    # Wait, the spec says "1-shift/day rule". A worker shouldn't have >1 shift template on the exact same date
    if len(existing_shifts) >= 1:
        raise ValueError("Worker already assigned to a shift on this date.")
        
    # Rule: max_h/day
    total_h = sum([s["planned_hours"] for s in existing_shifts]) + new_shift["planned_hours"]
    if total_h > MAX_H_PER_DAY:
        raise ValueError(f"Exceeds maximum {MAX_H_PER_DAY} hours per day.")
        
    return True
