import pytest
from app.workforce.shift_util import calculate_duration_h, check_worker_rules

def test_shift_util_duration():
    # Regular shift
    assert calculate_duration_h("06:00:00", "14:00:00") == 8.0
    # Cross-midnight shift
    assert calculate_duration_h("22:00:00", "06:00:00") == 8.0

def test_shift_util_rules():
    # 1 shift per day rule
    with pytest.raises(ValueError, match="already assigned"):
        check_worker_rules([{"start_time": "06:00:00", "end_time": "14:00:00", "planned_hours": 8.0}],
                           {"start_time": "14:00:00", "end_time": "22:00:00", "planned_hours": 8.0})
                           
    # max hours per day rule (simulate bypassing the 1-shift rule to check max hours independently, or just use one long shift)
    with pytest.raises(ValueError, match="Exceeds maximum 12.0 hours per day"):
        check_worker_rules([], {"start_time": "06:00:00", "end_time": "20:00:00", "planned_hours": 14.0})

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.all_models import RosterAssignment, Worker, Department, ShiftTemplate

client = TestClient(app)

def test_roster_endpoint():
    db = SessionLocal()
    # Find a worker and a dept and a shift
    worker = db.query(Worker).first()
    dept = db.query(Department).first()
    shift = db.query(ShiftTemplate).first()
    
    if worker and dept and shift:
        # Create a loan assignment (worker in a different dept)
        loan_dept = db.query(Department).filter(Department.id != worker.home_dept_id).first()
        
        assign = RosterAssignment(
            worker_id=worker.id,
            date="2026-10-10",
            shift_template_id=shift.id,
            dept_id=loan_dept.id if loan_dept else dept.id,
            kind="LOAN" if loan_dept else "REGULAR",
            planned_hours=8.0
        )
        db.add(assign)
        db.commit()
        
        # Test roster for the loan_dept
        response = client.get(f"/api/workforce/roster?date=2026-10-10&dept_id={loan_dept.id if loan_dept else dept.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["present"] >= 1
        
        if loan_dept:
            assert data["summary"]["loan_in"] >= 1
            
            # Test roster for home_dept to see loan_out
            response2 = client.get(f"/api/workforce/roster?date=2026-10-10&dept_id={worker.home_dept_id}")
            assert response2.status_code == 200
            data2 = response2.json()
            assert data2["summary"]["loan_out"] >= 1
            
        # Clean up
        db.delete(assign)
        db.commit()

def test_skill_coverage_endpoint():
    db = SessionLocal()
    dept = db.query(Department).first()
    if dept:
        response = client.get(f"/api/workforce/skills/coverage?date=2026-10-10&dept_id={dept.id}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
