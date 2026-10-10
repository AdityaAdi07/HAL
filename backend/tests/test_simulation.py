import pytest
from app.simulation.engine import SimEngine
from app.simulation.generator import generate_synthetic_data, validate_synthetic_data
from app.db.session import SessionLocal
from app.models.all_models import ComponentEvent, ComponentUnit

def test_engine_determinism():
    units = [{"id": "u1", "expected_h": 2.0}, {"id": "u2", "expected_h": 4.0}]
    
    eng1 = SimEngine(seed=123)
    events1 = eng1.run(units, duration_limit=100)
    
    eng2 = SimEngine(seed=123)
    events2 = eng2.run(units, duration_limit=100)
    
    assert len(events1) == len(events2)
    for e1, e2 in zip(events1, events2):
        assert e1["component_unit_id"] == e2["component_unit_id"]
        assert e1["event_type"] == e2["event_type"]
        assert e1["ts"] == e2["ts"]
        
def test_validation_script():
    db = SessionLocal()
    from app.models.all_models import LoomModel
    from app.tracking.order_manager import create_order
    lm = db.query(LoomModel).first()
    if lm and db.query(ComponentUnit).count() == 0:
        create_order(db, {"code": "ORD-SYNTH-TEST", "loom_model_id": lm.id, "quantity": 1})
    
    # Clear old events to ensure we are testing the generation
    db.query(ComponentEvent).filter(ComponentEvent.data_source == "SYNTHETIC").delete()
    db.commit()
    
    generated = generate_synthetic_data(months=1, seed=42)
    
    is_valid = validate_synthetic_data()
    if generated and generated > 0:
        assert is_valid is True
    else:
        # If no units exist, generation skips
        pass
