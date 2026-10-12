"""Integration tests crossing the HTTP boundary for core application workflows."""
from fastapi.testclient import TestClient


def test_health_check_endpoint(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_diagram_create_and_read_workflow(client: TestClient, analyst_token: str):
    headers = {"Authorization": f"Bearer {analyst_token}"}
    create_payload = {
        "name": "Integration Test Treemap",
        "diagram_type": "treemap",
        "theme": "editorial_light",
        "content": {
            "title": "Clean Energy Integration",
            "eyebrow": "DATA VISUALIZATION",
            "data": {
                "items": [
                    {"label": "Solar", "value": 60},
                    {"label": "Wind", "value": 40},
                ]
            },
        },
    }

    # 1. Create diagram crossing HTTP boundary
    create_res = client.post("/api/diagrams", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    created_data = create_res.json()
    diagram_id = created_data["id"]
    assert created_data["name"] == "Integration Test Treemap"

    # 2. Read back diagram
    get_res = client.get(f"/api/diagrams/{diagram_id}", headers=headers)
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["id"] == diagram_id
    assert get_data["content"]["title"] == "Clean Energy Integration"

    # 3. List diagrams
    list_res = client.get("/api/diagrams", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(d["id"] == diagram_id for d in list_data["items"])


def test_diagram_update_and_delete_workflow(client: TestClient, analyst_token: str, admin_token: str):
    analyst_headers = {"Authorization": f"Bearer {analyst_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    create_payload = {
        "name": "Temporary Diagram",
        "diagram_type": "slopegraph",
        "content": {"title": "Slope", "data": {}},
    }
    create_res = client.post("/api/diagrams", json=create_payload, headers=analyst_headers)
    diagram_id = create_res.json()["id"]

    # Update diagram
    update_res = client.put(
        f"/api/diagrams/{diagram_id}",
        json={"name": "Renamed Diagram"},
        headers=analyst_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Renamed Diagram"

    # Delete diagram with admin token
    del_res = client.delete(f"/api/diagrams/{diagram_id}", headers=admin_headers)
    assert del_res.status_code == 204

    # Verify not found
    get_res = client.get(f"/api/diagrams/{diagram_id}", headers=analyst_headers)
    assert get_res.status_code == 404


def test_live_render_endpoint(client: TestClient, viewer_token: str):
    headers = {"Authorization": f"Bearer {viewer_token}"}
    render_payload = {
        "diagram_type": "rag_pipeline",
        "theme": "editorial_dark",
        "content": {
            "title": "Live RAG Flow",
            "data": {},
        },
    }
    res = client.post("/api/diagrams/render", json=render_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "<svg" in data["svg"]
    assert "<!DOCTYPE html>" in data["html"]
    assert data["diagram_type"] == "rag_pipeline"


def test_live_validate_endpoint(client: TestClient, viewer_token: str):
    headers = {"Authorization": f"Bearer {viewer_token}"}
    validate_payload = {
        "diagram_type": "architecture_azure",
        "content": {
            "title": "Validation Test",
            "data": {
                "subscription": "Sub",
                "resource_group": "RG",
                "vnet": "VNet",
                "subnets": [
                    {
                        "name": "snet-1",
                        "nodes": [{"id": "bad-paas", "label": "Azure SQL", "type": "paas_service"}],
                    }
                ],
            },
        },
    }
    res = client.post("/api/diagrams/validate", json=validate_payload, headers=headers)
    assert res.status_code == 200
    report = res.json()
    assert not report["valid"]
    assert not report["containment_compliant"]


def test_evaluation_run_endpoint(client: TestClient, analyst_token: str):
    headers = {"Authorization": f"Bearer {analyst_token}"}
    res = client.post("/api/evaluation/run", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_cases"] == 20
    assert data["accuracy_rate"] >= 0.90


def test_audit_logs_endpoint(client: TestClient, analyst_token: str):
    headers = {"Authorization": f"Bearer {analyst_token}"}
    res = client.get("/api/audit", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
