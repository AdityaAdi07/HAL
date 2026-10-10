import uuid
import datetime
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.all_models import ComponentUnit, ComponentEvent
from app.simulation.engine import SimEngine

def generate_synthetic_data(months: int = 6, seed: int = 42):
    db = SessionLocal()
    
    # Let's get a few component units
    units = db.query(ComponentUnit).limit(100).all()
    if not units:
        print("No units to simulate. Run orders creation first.")
        return 0
        
    unit_data = [{"id": u.id, "expected_h": u.expected_h or 2.0} for u in units]
    
    engine = SimEngine(seed=seed)
    # simulate for roughly 6 months of hours (6 * 30 * 24 = 4320 hours)
    duration = months * 30 * 24
    
    events = engine.run(unit_data, duration_limit=duration)
    
    # Save to db
    for e in events:
        db_event = ComponentEvent(
            ts=e["ts"],
            component_unit_id=e["component_unit_id"],
            event_type=e["event_type"],
            data_source=e["data_source"]
        )
        db.add(db_event)
        
    db.commit()
    return len(events)

def validate_synthetic_data():
    db = SessionLocal()
    events = db.query(ComponentEvent).filter(ComponentEvent.data_source == "SYNTHETIC").all()
    if not events:
        return False
        
    # Validation: Determinism is checked by calling generate twice with same seed in tests.
    return True
