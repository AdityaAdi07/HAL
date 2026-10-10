import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.all_models import LoomModel, LoomBuildOrder, LoomUnit, ComponentUnit, ComponentEvent, ComponentType
import uuid

client = TestClient(app)

def create_fresh_order(db, lm, uid):
    response = client.post("/api/tracking/orders", json={
        "code": f"ORD-TEST-{uid}",
        "loom_model_id": lm.id,
        "quantity": 1
    })
    return response

def test_create_order_generates_correct_units():
    db = SessionLocal()
    lm = db.query(LoomModel).filter_by(code="LM-100").first()
    if not lm:
        pytest.skip("LM-100 not found")
        
    uid = str(uuid.uuid4())[:8]
    response = create_fresh_order(db, lm, uid)
    
    assert response.status_code == 200
    data = response.json()
    assert data["looms_created"] == 1
    assert data["components_created"] == 32 # 1 looms * 32 components per LM-100

def test_illegal_state_transition_returns_409():
    db = SessionLocal()
    lm = db.query(LoomModel).filter_by(code="LM-100").first()
    uid = str(uuid.uuid4())[:8]
    create_fresh_order(db, lm, uid)
    
    order = db.query(LoomBuildOrder).filter_by(code=f"ORD-TEST-{uid}").first()
    loom = db.query(LoomUnit).filter_by(order_id=order.id).first()
    comp = db.query(ComponentUnit).filter_by(loom_unit_id=loom.id).first()
    
    # comp is initially PLANNED.
    # Trying to jump to COMPLETE should fail (409)
    response = client.post("/api/tracking/events", json={
        "component_unit_id": comp.id,
        "event_type": "COMPLETE"
    })
    assert response.status_code == 409
    
def test_valid_state_transition_and_loom_progress():
    db = SessionLocal()
    lm = db.query(LoomModel).filter_by(code="LM-100").first()
    uid = str(uuid.uuid4())[:8]
    create_fresh_order(db, lm, uid)
    
    order = db.query(LoomBuildOrder).filter_by(code=f"ORD-TEST-{uid}").first()
    loom = db.query(LoomUnit).filter_by(order_id=order.id).first()
    comp = db.query(ComponentUnit).filter_by(loom_unit_id=loom.id).first()
    
    # PLANNED -> READY -> START -> COMPLETE
    client.post("/api/tracking/events", json={"component_unit_id": comp.id, "event_type": "READY"})
    client.post("/api/tracking/events", json={"component_unit_id": comp.id, "event_type": "START"})
    client.post("/api/tracking/events", json={"component_unit_id": comp.id, "event_type": "COMPLETE"})
    
    # Check loom progress
    response = client.get(f"/api/tracking/looms/{loom.serial}")
    assert response.status_code == 200
    data = response.json()
    assert data["progress_pct"] > 0.0
    
def test_rebuild_projection():
    db = SessionLocal()
    lm = db.query(LoomModel).filter_by(code="LM-100").first()
    uid = str(uuid.uuid4())[:8]
    create_fresh_order(db, lm, uid)
    
    order = db.query(LoomBuildOrder).filter_by(code=f"ORD-TEST-{uid}").first()
    loom = db.query(LoomUnit).filter_by(order_id=order.id).first()
    comp = db.query(ComponentUnit).filter_by(loom_unit_id=loom.id).first()
    
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    ev1 = ComponentEvent(component_unit_id=comp.id, event_type="READY", ts=now)
    ev2 = ComponentEvent(component_unit_id=comp.id, event_type="START", ts=now)
    db.add_all([ev1, ev2])
    db.commit()
    
    from app.tracking.state_machine import rebuild_projection
    
    # Rebuild it.
    comp2 = rebuild_projection(db, comp.id)
    assert comp2.status == "IN_PROGRESS"
