import yaml
import os
import json
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.models.all_models import (
    Department, ComponentType, Skill, WorkstationType,
    Workstation, ComponentTypeWorkstationType, ComponentPrerequisite,
    LoomModel, LoomModelComponent, Worker, WorkerSkill, ShiftTemplate
)
from app.db.base import Base

def check_dag_acyclic(session: Session):
    # Check for cycles in component prerequisites
    prereqs = session.query(ComponentPrerequisite).all()
    graph = {}
    for p in prereqs:
        if p.component_type_id not in graph:
            graph[p.component_type_id] = []
        graph[p.component_type_id].append(p.prerequisite_type_id)

    def visit(node, visited, recursion_stack):
        visited.add(node)
        recursion_stack.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if visit(neighbor, visited, recursion_stack):
                    return True
            elif neighbor in recursion_stack:
                return True
        recursion_stack.remove(node)
        return False

    visited = set()
    recursion_stack = set()
    for node in graph:
        if node not in visited:
            if visit(node, visited, recursion_stack):
                raise ValueError("DAG contains a cycle!")
    print("DAG acyclic check passed.")

def seed():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    
    # Optional: Clear tables if we want idempotent seed, though we're using SQLite for now 
    # For a robust seed, we'd delete in reverse order of dependencies.
    # Instead we'll just check if already seeded.
    if session.query(Department).first():
        print("Database already seeded.")
        return

    configs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "configs")
    
    with open(os.path.join(configs_dir, "catalog.yaml"), "r") as f:
        catalog = yaml.safe_load(f)
        
    with open(os.path.join(configs_dir, "factory.yaml"), "r") as f:
        factory = yaml.safe_load(f)

    # 1. Shifts
    for s in factory.get("shifts", []):
        session.add(ShiftTemplate(code=s["code"], name=s["name"], start_time=s["start_time"], end_time=s["end_time"], break_h=s["break_h"], productive_h=8.0 - s["break_h"]))
    
    # 2. Skills
    skills_map = {}
    for sk in factory.get("skills", []):
        obj = Skill(code=sk["code"], name=sk["name"])
        session.add(obj)
        session.flush()
        skills_map[obj.code] = obj.id

    # 3. Departments
    depts_map = {}
    for d in catalog.get("departments", []):
        obj = Department(code=d["code"], name=d["name"], dept_no=d["dept_no"], layout_json=json.loads(d["layout_json"]) if isinstance(d["layout_json"], str) else d["layout_json"], accent_icon=d.get("accent_icon"))
        session.add(obj)
        session.flush()
        depts_map[obj.code] = obj.id

    # 4. Workstation Types
    wt_map = {}
    for wt in factory.get("workstation_types", []):
        obj = WorkstationType(code=wt["code"], name=wt["name"], dept_id=depts_map[wt["dept_code"]])
        session.add(obj)
        session.flush()
        wt_map[obj.code] = obj.id

    # 5. Workstations
    for w in factory.get("workstations", []):
        wt_obj = session.query(WorkstationType).filter_by(code=w["type_code"]).first()
        session.add(Workstation(code=w["code"], type_id=wt_obj.id, dept_id=wt_obj.dept_id, name=w["code"]))
    session.commit()


    # 6. Component Types & Prerequisites
    comp_map = {}
    prereqs_pending = []
    wst_links = []
    
    for d in catalog.get("departments", []):
        for c in d.get("components", []):
            obj = ComponentType(
                code=c["code"],
                name=c["name"],
                dept_id=depts_map[d["code"]],
                std_hours=c["std_hours"],
                crew_size=c.get("crew_size", 1),
                required_skill_id=skills_map[c["skill"]],
                min_skill_level=c["min_skill_level"],
                visual_key=c.get("visual_key")
            )
            session.add(obj)
            session.flush()
            comp_map[obj.code] = obj.id
            
            for p in c.get("prereqs", []):
                prereqs_pending.append((obj.code, p))
            for wt in c.get("workstation_types", []):
                wst_links.append((obj.code, wt))
                
    for c_code, wt_code in wst_links:
        session.add(ComponentTypeWorkstationType(component_type_id=comp_map[c_code], workstation_type_id=wt_map[wt_code]))
    
    session.commit()
    
    for child, parent in prereqs_pending:
        session.add(ComponentPrerequisite(component_type_id=comp_map[child], prerequisite_type_id=comp_map[parent]))

    # 7. Loom Models
    for lm in catalog.get("loom_models", []):
        obj = LoomModel(code=lm["code"], name=lm["name"], complexity_multiplier=lm["complexity_multiplier"], active=lm["active"])
        session.add(obj)
        session.flush()
        
        # Link components for LM-100 base
        if obj.code == "LM-100":
            for d in catalog.get("departments", []):
                for c in d.get("components", []):
                    session.add(LoomModelComponent(
                        loom_model_id=obj.id,
                        component_type_id=comp_map[c["code"]],
                        qty_per_loom=c.get("qty_per_loom", 1)
                    ))
                    
    # 8. Workers
    for w in factory.get("workers", []):
        obj = Worker(code=w["code"], name=w["name"], home_dept_id=depts_map[w["home_dept"]])
        session.add(obj)
        session.flush()
        
        for sk in w.get("skills", []):
            session.add(WorkerSkill(worker_id=obj.id, skill_id=skills_map[sk["code"]], level=sk["level"]))
            
    session.commit()

    # 9. Verify DAG
    check_dag_acyclic(session)
    print("Seeding completed successfully.")

if __name__ == "__main__":
    seed()
