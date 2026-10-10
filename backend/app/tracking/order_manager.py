import uuid
from sqlalchemy.orm import Session
from app.models.all_models import LoomBuildOrder, LoomUnit, ComponentUnit, LoomModelComponent, ComponentType

def create_order(db: Session, order_data: dict) -> LoomBuildOrder:
    order = LoomBuildOrder(
        code=order_data["code"],
        loom_model_id=order_data["loom_model_id"],
        quantity=order_data["quantity"],
        priority=order_data.get("priority", "NORMAL"),
        customer_ref=order_data.get("customer_ref")
    )
    db.add(order)
    db.flush()
    
    components = db.query(LoomModelComponent).filter(
        LoomModelComponent.loom_model_id == order.loom_model_id
    ).all()
    
    comp_types = {c.id: c for c in db.query(ComponentType).all()}
    
    # Create LoomUnits and ComponentUnits
    for i in range(order.quantity):
        serial = f"{order.code}-{(i+1):03d}"
        l_unit = LoomUnit(serial=serial, order_id=order.id)
        db.add(l_unit)
        db.flush()
        
        for mc in components:
            ct = comp_types[mc.component_type_id]
            for j in range(mc.qty_per_loom):
                c_unit = ComponentUnit(
                    loom_unit_id=l_unit.id,
                    component_type_id=ct.id,
                    ordinal=j+1,
                    dept_id=ct.dept_id,
                    expected_h=ct.std_hours * mc.complexity_multiplier
                )
                db.add(c_unit)
    
    db.commit()
    return order
