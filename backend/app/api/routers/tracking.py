from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Any
from app.db.session import get_db
from app.models.all_models import LoomBuildOrder, LoomUnit, ComponentUnit, ComponentEvent, Department, ComponentType
from app.tracking.order_manager import create_order
from app.tracking.state_machine import apply_event
import datetime
import uuid

router = APIRouter()

class OrderCreate(BaseModel):
    code: str
    loom_model_id: str
    quantity: int
    priority: str = "NORMAL"

class EventCreate(BaseModel):
    component_unit_id: str
    event_type: str
    workstation_id: Optional[str] = None
    worker_id: Optional[str] = None
    progress_pct: Optional[float] = None
    reason_code: Optional[str] = None
    payload_json: Optional[dict] = None

@router.post("/orders")
def post_order(order: OrderCreate, db: Session = Depends(get_db)):
    try:
        new_order = create_order(db, order.model_dump())
        
        # Count created units
        looms = db.query(LoomUnit).filter(LoomUnit.order_id == new_order.id).count()
        comps = db.query(ComponentUnit).join(LoomUnit).filter(LoomUnit.order_id == new_order.id).count()
        
        return {"message": "Order created", "looms_created": looms, "components_created": comps}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/events")
def post_event(event: EventCreate, db: Session = Depends(get_db)):
    db_event = ComponentEvent(
        ts=datetime.datetime.now(datetime.timezone.utc),
        component_unit_id=event.component_unit_id,
        event_type=event.event_type,
        workstation_id=event.workstation_id,
        worker_id=event.worker_id,
        progress_pct=event.progress_pct,
        reason_code=event.reason_code,
        payload_json=event.payload_json,
        data_source="MANUAL"
    )
    
    try:
        apply_event(db, db_event)
        return {"message": "Event applied"}
    except ValueError as ve:
        raise HTTPException(status_code=409, detail=str(ve))

@router.get("/looms/{serial}")
def get_loom(serial: str, db: Session = Depends(get_db)):
    loom = db.query(LoomUnit).filter(LoomUnit.serial == serial).first()
    if not loom:
        raise HTTPException(status_code=404, detail="Loom not found")
        
    components = db.query(ComponentUnit).filter(ComponentUnit.loom_unit_id == loom.id).all()
    
    # Calculate progress
    total_expected_h = sum([c.expected_h for c in components if c.expected_h])
    completed_h = sum([c.expected_h for c in components if c.expected_h and c.progress_pct == 1.0])
    
    loom_progress = (completed_h / total_expected_h) if total_expected_h > 0 else 0.0
    loom.progress_pct = loom_progress
    db.commit()
    
    # Find blocking component
    blocked = [c for c in components if c.status == "BLOCKED"]
    
    return {
        "serial": loom.serial,
        "progress_pct": loom_progress,
        "stage": loom.stage,
        "blocking_components": [{"id": c.id, "reason": c.block_reason} for c in blocked],
        "components_count": len(components)
    }
