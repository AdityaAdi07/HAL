import uuid
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, JSON, text
from sqlalchemy.orm import relationship
from app.db.base import Base

def generate_uuid():
    return str(uuid.uuid4())

class Department(Base):
    __tablename__ = "department"
    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, unique=True, index=True, nullable=False)
    dept_no = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    layout_json = Column(JSON, nullable=True)
    lead_worker_id = Column(String, ForeignKey("worker.id"), nullable=True)
    accent_icon = Column(String, nullable=True)

class WorkstationType(Base):
    __tablename__ = "workstation_type"
    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, unique=True, index=True, nullable=False)
    dept_id = Column(String, ForeignKey("department.id"), nullable=False)
    name = Column(String, nullable=False)

class Workstation(Base):
    __tablename__ = "workstation"
    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, unique=True, index=True, nullable=False)
    dept_id = Column(String, ForeignKey("department.id"), nullable=False)
    type_id = Column(String, ForeignKey("workstation_type.id"), nullable=False)
    name = Column(String, nullable=True)
    status = Column(String, nullable=False, default="AVAILABLE")
    speed_factor_hint = Column(Float, nullable=True)
    commissioned_on = Column(DateTime(timezone=True), nullable=True)

class Skill(Base):
    __tablename__ = "skill"
    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)

class ComponentType(Base):
    __tablename__ = "component_type"
    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, unique=True, index=True, nullable=False)
    dept_id = Column(String, ForeignKey("department.id"), nullable=False)
    name = Column(String, nullable=False)
    std_hours = Column(Float, nullable=False)
    std_setup_hours = Column(Float, nullable=False, default=0.0)
    crew_size = Column(Integer, nullable=False, default=1)
    required_skill_id = Column(String, ForeignKey("skill.id"), nullable=False)
    min_skill_level = Column(Integer, nullable=False, default=1)
    first_pass_yield = Column(Float, nullable=False, default=0.99)
    visual_key = Column(String, nullable=True)
    sequence_hint = Column(Integer, nullable=True)

class ComponentTypeWorkstationType(Base):
    __tablename__ = "component_type_workstation_type"
    component_type_id = Column(String, ForeignKey("component_type.id"), primary_key=True)
    workstation_type_id = Column(String, ForeignKey("workstation_type.id"), primary_key=True)
    preference_rank = Column(Integer, nullable=False, default=1)

class ComponentPrerequisite(Base):
    __tablename__ = "component_prerequisite"
    component_type_id = Column(String, ForeignKey("component_type.id"), primary_key=True)
    prerequisite_type_id = Column(String, ForeignKey("component_type.id"), primary_key=True)
    transfer_time_h = Column(Float, nullable=False, default=0.0)

class LoomModel(Base):
    __tablename__ = "loom_model"
    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    complexity_multiplier = Column(Float, nullable=False, default=1.0)
    active = Column(Boolean, nullable=False, default=True)

class LoomModelComponent(Base):
    __tablename__ = "loom_model_component"
    loom_model_id = Column(String, ForeignKey("loom_model.id"), primary_key=True)
    component_type_id = Column(String, ForeignKey("component_type.id"), primary_key=True)
    qty_per_loom = Column(Integer, nullable=False, default=1)
    complexity_multiplier = Column(Float, nullable=False, default=1.0)

class Worker(Base):
    __tablename__ = "worker"
    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    home_dept_id = Column(String, ForeignKey("department.id"), nullable=False)
    employment = Column(String, nullable=False, default="FULL")
    active = Column(Boolean, nullable=False, default=True)

class WorkerSkill(Base):
    __tablename__ = "worker_skill"
    worker_id = Column(String, ForeignKey("worker.id"), primary_key=True)
    skill_id = Column(String, ForeignKey("skill.id"), primary_key=True)
    level = Column(Integer, nullable=False, default=1)

class ShiftTemplate(Base):
    __tablename__ = "shift_template"
    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    break_h = Column(Float, nullable=False, default=0.0)
    productive_h = Column(Float, nullable=False)

class Material(Base):
    __tablename__ = "material"
    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    unit = Column(String, nullable=False, default="pcs")
    lead_time_days = Column(Integer, nullable=False, default=1)
    safety_stock = Column(Integer, nullable=False, default=0)

class BomLine(Base):
    __tablename__ = "bom_line"
    component_type_id = Column(String, ForeignKey("component_type.id"), primary_key=True)
    material_id = Column(String, ForeignKey("material.id"), primary_key=True)
    qty_per_unit = Column(Float, nullable=False)
    scrap_factor = Column(Float, nullable=False, default=0.0)

class CalendarDay(Base):
    __tablename__ = "calendar_day"
    date = Column(String, primary_key=True) # YYYY-MM-DD
    is_working = Column(Boolean, nullable=False, default=True)
    kind = Column(String, nullable=False, default="NORMAL") # HOLIDAY, SHUTDOWN, NORMAL
    note = Column(String, nullable=True)

class ConfigThreshold(Base):
    __tablename__ = "config_threshold"
    id = Column(String, primary_key=True, default=generate_uuid)
    scope_type = Column(String, nullable=False) # GLOBAL, DEPT, WORKSTATION
    scope_id = Column(String, nullable=True)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)

class LoomBuildOrder(Base):
    __tablename__ = "loom_build_order"
    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, unique=True, index=True, nullable=False)
    loom_model_id = Column(String, ForeignKey("loom_model.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    priority = Column(String, nullable=False, default="NORMAL") # NORMAL, HIGH, URGENT, CRITICAL
    release_at = Column(DateTime(timezone=True), nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, nullable=False, default="PLANNED")
    customer_ref = Column(String, nullable=True)

class LoomUnit(Base):
    __tablename__ = "loom_unit"
    id = Column(String, primary_key=True, default=generate_uuid)
    serial = Column(String, unique=True, index=True, nullable=False)
    order_id = Column(String, ForeignKey("loom_build_order.id"), nullable=False)
    status = Column(String, nullable=False, default="PLANNED")
    stage = Column(String, nullable=True)
    progress_pct = Column(Float, nullable=False, default=0.0)
    released_at = Column(DateTime(timezone=True), nullable=True)
    planned_complete_at = Column(DateTime(timezone=True), nullable=True)
    actual_complete_at = Column(DateTime(timezone=True), nullable=True)
    operating_device_id = Column(String, nullable=True)

class ComponentUnit(Base):
    __tablename__ = "component_unit"
    id = Column(String, primary_key=True, default=generate_uuid)
    loom_unit_id = Column(String, ForeignKey("loom_unit.id"), nullable=False)
    component_type_id = Column(String, ForeignKey("component_type.id"), nullable=False)
    ordinal = Column(Integer, nullable=False, default=1)
    dept_id = Column(String, ForeignKey("department.id"), nullable=False)
    status = Column(String, nullable=False, default="PLANNED")
    block_reason = Column(String, nullable=True)
    progress_pct = Column(Float, nullable=False, default=0.0)
    progress_source = Column(String, nullable=True)
    workstation_id = Column(String, ForeignKey("workstation.id"), nullable=True)
    worker_ids = Column(JSON, nullable=True) # crew
    planned_start = Column(DateTime(timezone=True), nullable=True)
    planned_end = Column(DateTime(timezone=True), nullable=True)
    actual_start = Column(DateTime(timezone=True), nullable=True)
    actual_end = Column(DateTime(timezone=True), nullable=True)
    expected_h = Column(Float, nullable=True)
    p75_h = Column(Float, nullable=True)
    p90_h = Column(Float, nullable=True)
    worked_h = Column(Float, nullable=False, default=0.0)
    rework_count = Column(Integer, nullable=False, default=0)
    replaces_id = Column(String, nullable=True)
    queue_entered_at = Column(DateTime(timezone=True), nullable=True)
    ready_at = Column(DateTime(timezone=True), nullable=True)

class ComponentEvent(Base):
    __tablename__ = "component_event"
    id = Column(String, primary_key=True, default=generate_uuid)
    ts = Column(DateTime(timezone=True), nullable=False)
    component_unit_id = Column(String, ForeignKey("component_unit.id"), nullable=False)
    event_type = Column(String, nullable=False)
    workstation_id = Column(String, ForeignKey("workstation.id"), nullable=True)
    worker_id = Column(String, ForeignKey("worker.id"), nullable=True)
    progress_pct = Column(Float, nullable=True)
    qty_good = Column(Integer, nullable=True)
    qty_rejected = Column(Integer, nullable=True)
    reason_code = Column(String, nullable=True)
    payload_json = Column(JSON, nullable=True)
    data_source = Column(String, nullable=False, default="LIVE")

class RosterAssignment(Base):
    __tablename__ = "roster_assignment"
    id = Column(String, primary_key=True, default=generate_uuid)
    worker_id = Column(String, ForeignKey("worker.id"), nullable=False)
    date = Column(String, nullable=False) # YYYY-MM-DD
    shift_template_id = Column(String, ForeignKey("shift_template.id"), nullable=False)
    dept_id = Column(String, ForeignKey("department.id"), nullable=False) # might differ from home_dept -> loan
    kind = Column(String, nullable=False, default="REGULAR") # REGULAR, OVERTIME, LOAN
    planned_hours = Column(Float, nullable=False)

class WorkerAvailability(Base):
    __tablename__ = "worker_availability"
    id = Column(String, primary_key=True, default=generate_uuid)
    worker_id = Column(String, ForeignKey("worker.id"), nullable=False)
    date = Column(String, nullable=False) # YYYY-MM-DD
    status = Column(String, nullable=False) # PRESENT, ABSENT, LEAVE, LATE, SICK
    reported_at = Column(DateTime(timezone=True), nullable=True)

class AttendanceLog(Base):
    __tablename__ = "attendance_log"
    id = Column(String, primary_key=True, default=generate_uuid)
    worker_id = Column(String, ForeignKey("worker.id"), nullable=False)
    check_in = Column(DateTime(timezone=True), nullable=False)
    check_out = Column(DateTime(timezone=True), nullable=True)
    workstation_id = Column(String, ForeignKey("workstation.id"), nullable=True)
