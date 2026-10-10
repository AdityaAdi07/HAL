from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.all_models import Department, ComponentType, Workstation, Worker, WorkerSkill, ComponentTypeWorkstationType, WorkstationType

router = APIRouter()

@router.get("/departments")
def get_departments(db: Session = Depends(get_db)):
    depts = db.query(Department).all()
    return [{"id": d.id, "code": d.code, "name": d.name, "dept_no": d.dept_no} for d in depts]

@router.get("/component-types")
def get_component_types(db: Session = Depends(get_db)):
    comps = db.query(ComponentType).all()
    return [{"id": c.id, "code": c.code, "name": c.name, "dept_id": c.dept_id} for c in comps]

@router.get("/component-types/{comp_code}/eligibility")
def get_eligibility(comp_code: str, db: Session = Depends(get_db)):
    comp = db.query(ComponentType).filter(ComponentType.code == comp_code).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Component not found")
        
    # Get eligible workstation types
    ws_types = db.query(WorkstationType).join(ComponentTypeWorkstationType).filter(
        ComponentTypeWorkstationType.component_type_id == comp.id
    ).all()
    ws_type_ids = [w.id for w in ws_types]
    
    # Get eligible workstations
    workstations = db.query(Workstation).filter(Workstation.type_id.in_(ws_type_ids)).all()
    
    # Get eligible workers (who have the required skill at >= min_skill_level)
    workers = db.query(Worker).join(WorkerSkill).filter(
        WorkerSkill.skill_id == comp.required_skill_id,
        WorkerSkill.level >= comp.min_skill_level,
        Worker.active == True
    ).all()
    
    return {
        "component": comp.code,
        "eligible_workstation_types": [wt.code for wt in ws_types],
        "eligible_workstations": [w.code for w in workstations],
        "qualified_workers": [w.code for w in workers]
    }
