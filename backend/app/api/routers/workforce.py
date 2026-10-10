from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.db.session import get_db
from app.models.all_models import Worker, RosterAssignment, WorkerAvailability, Department, ShiftTemplate, Skill, WorkerSkill

router = APIRouter()

@router.get("/roster")
def get_roster(date: str, dept_id: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Returns roster for a specific date, handling present/absent/loan logic.
    """
    # Base query for assignments on this date
    query = db.query(RosterAssignment).filter(RosterAssignment.date == date)
    
    if dept_id:
        # We want to see workers assigned to this dept (which includes loans IN)
        # and we also want to see home_dept workers who are assigned OUT (loans out)
        # But for "roster", usually it means who is working HERE today.
        query = query.filter(RosterAssignment.dept_id == dept_id)
        
    assignments = query.all()
    
    result = []
    present_count = 0
    absent_count = 0
    loan_in_count = 0
    loan_out_count = 0

    # Also grab availability status for the date
    for a in assignments:
        worker = db.query(Worker).filter(Worker.id == a.worker_id).first()
        avail = db.query(WorkerAvailability).filter(
            WorkerAvailability.worker_id == a.worker_id,
            WorkerAvailability.date == date
        ).first()
        
        status = avail.status if avail else "PRESENT" # Default assumption if rostered
        
        if status in ["ABSENT", "LEAVE", "SICK"]:
            absent_count += 1
        else:
            present_count += 1
            
        is_loan_in = (worker.home_dept_id != a.dept_id)
        if is_loan_in:
            loan_in_count += 1
            
        result.append({
            "worker_id": worker.id,
            "worker_name": worker.name,
            "worker_code": worker.code,
            "shift_id": a.shift_template_id,
            "dept_id": a.dept_id, # Working dept
            "home_dept_id": worker.home_dept_id,
            "kind": a.kind,
            "status": status,
            "planned_hours": a.planned_hours
        })
        
    # Find loans OUT (workers from this dept working elsewhere)
    if dept_id:
        loans_out = db.query(RosterAssignment).join(Worker).filter(
            RosterAssignment.date == date,
            Worker.home_dept_id == dept_id,
            RosterAssignment.dept_id != dept_id
        ).all()
        loan_out_count = len(loans_out)
        
    return {
        "date": date,
        "dept_id": dept_id,
        "summary": {
            "present": present_count,
            "absent": absent_count,
            "loan_in": loan_in_count,
            "loan_out": loan_out_count
        },
        "assignments": result
    }

@router.get("/skills/coverage")
def get_skill_coverage(date: str, dept_id: str, db: Session = Depends(get_db)):
    """
    Returns skill coverage for a dept on a specific date (based on PRESENT workers).
    """
    assignments = db.query(RosterAssignment).filter(
        RosterAssignment.date == date,
        RosterAssignment.dept_id == dept_id
    ).all()
    
    coverage = {}
    for a in assignments:
        avail = db.query(WorkerAvailability).filter(
            WorkerAvailability.worker_id == a.worker_id,
            WorkerAvailability.date == date
        ).first()
        status = avail.status if avail else "PRESENT"
        if status not in ["ABSENT", "LEAVE", "SICK"]:
            worker_skills = db.query(WorkerSkill).filter(WorkerSkill.worker_id == a.worker_id).all()
            for ws in worker_skills:
                skill = db.query(Skill).filter(Skill.id == ws.skill_id).first()
                if skill.code not in coverage:
                    coverage[skill.code] = 0
                coverage[skill.code] += 1
                
    return coverage
