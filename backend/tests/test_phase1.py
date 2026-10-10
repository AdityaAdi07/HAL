from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_departments():
    response = client.get("/api/departments")
    assert response.status_code == 200
    depts = response.json()
    assert len(depts) == 5
    assert any(d["code"] == "DEPT-MECH" for d in depts)

def test_get_component_types():
    response = client.get("/api/component-types")
    assert response.status_code == 200
    comps = response.json()
    assert len(comps) > 10

def test_get_eligibility():
    response = client.get("/api/component-types/ASY-TEST/eligibility")
    assert response.status_code == 200
    data = response.json()
    assert data["component"] == "ASY-TEST"
    assert "TEST_RIG" in data["eligible_workstation_types"]
    assert len(data["qualified_workers"]) >= 1
