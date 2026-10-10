from sqlalchemy.orm import Session
from app.models.all_models import ComponentUnit, ComponentEvent

# Legal transitions per event
TRANSITIONS = {
    "RELEASE": ["PLANNED"],
    "READY": ["PLANNED", "RELEASED", "BLOCKED"], # Actually, it can become ready from planned when prereqs finish
    "QUEUE": ["READY", "PAUSED"],
    "START": ["READY", "QUEUE"],
    "PROGRESS": ["IN_PROGRESS", "QC_IN_PROGRESS"],
    "PAUSE": ["IN_PROGRESS"],
    "RESUME": ["PAUSED"],
    "BLOCK": ["PLANNED", "READY", "QUEUE", "IN_PROGRESS", "PAUSED"],
    "UNBLOCK": ["BLOCKED"],
    "QC_START": ["IN_PROGRESS"],
    "QC_PASS": ["QC_IN_PROGRESS"],
    "QC_FAIL": ["QC_IN_PROGRESS"],
    "REWORK_START": ["QC_FAILED"],
    "REJECT": ["QC_FAILED", "IN_PROGRESS"],
    "COMPLETE": ["IN_PROGRESS", "QC_PASSED"],
    "REOPEN": ["COMPLETED"],
    "REASSIGN": ["IN_PROGRESS", "PAUSED", "QUEUE"]
}

TARGET_STATES = {
    "RELEASE": "RELEASED",
    "READY": "READY",
    "QUEUE": "QUEUED",
    "START": "IN_PROGRESS",
    "PROGRESS": None, # keeps current state
    "PAUSE": "PAUSED",
    "RESUME": "IN_PROGRESS",
    "BLOCK": "BLOCKED",
    "UNBLOCK": "READY", # simplify for now
    "QC_START": "QC_IN_PROGRESS",
    "QC_PASS": "QC_PASSED",
    "QC_FAIL": "QC_FAILED",
    "REWORK_START": "IN_PROGRESS",
    "REJECT": "REJECTED",
    "COMPLETE": "COMPLETED",
    "REOPEN": "IN_PROGRESS",
    "REASSIGN": None # keeps current state
}

def apply_event(db: Session, event: ComponentEvent, simulate=False):
    unit = db.query(ComponentUnit).filter(ComponentUnit.id == event.component_unit_id).first()
    if not unit:
        raise ValueError(f"ComponentUnit {event.component_unit_id} not found")
        
    current_state = unit.status
    allowed_from = TRANSITIONS.get(event.event_type)
    
    if allowed_from is None:
        raise ValueError(f"Unknown event type {event.event_type}")
        
    if current_state not in allowed_from:
        raise ValueError(f"Illegal transition: {event.event_type} from {current_state}")
        
    target_state = TARGET_STATES[event.event_type]
    if target_state:
        unit.status = target_state
        
    # Update projection fields
    if event.progress_pct is not None:
        unit.progress_pct = event.progress_pct
    if event.workstation_id:
        unit.workstation_id = event.workstation_id
    if event.worker_id:
        # Simplification: overwrite crew with the single worker for now, or append
        unit.worker_ids = [event.worker_id]
        
    if event.event_type == "START" and not unit.actual_start:
        unit.actual_start = event.ts
    if event.event_type == "COMPLETE":
        unit.progress_pct = 1.0
        unit.actual_end = event.ts
    if event.event_type == "BLOCK":
        unit.block_reason = event.reason_code
    if event.event_type == "UNBLOCK":
        unit.block_reason = None
        
    if not simulate:
        db.add(event)
        db.commit()

def rebuild_projection(db: Session, unit_id: str):
    unit = db.query(ComponentUnit).filter(ComponentUnit.id == unit_id).first()
    events = db.query(ComponentEvent).filter(ComponentEvent.component_unit_id == unit_id).order_by(ComponentEvent.ts).all()
    
    # Reset projection
    unit.status = "PLANNED"
    unit.progress_pct = 0.0
    unit.workstation_id = None
    unit.worker_ids = None
    unit.actual_start = None
    unit.actual_end = None
    unit.block_reason = None
    
    for event in events:
        apply_event(db, event, simulate=True)
        
    db.commit()
    return unit
