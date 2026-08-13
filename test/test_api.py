from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# --- 1. Health Probe Tests ---

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_liveness_probe():
    response = client.get("/health/liveness")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"

@patch("main.db")
def test_readiness_probe_success(mock_db):
    mock_db.collection.return_value.document.return_value.get.return_value = True
    response = client.get("/health/readiness")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


# --- 2. Firestore User CRUD Tests ---

@patch("main.db")
def test_create_user(mock_db):
    payload = {"name": "Alice Doe", "email": "alice@example.com", "role": "admin"}
    response = client.post("/api/users/user_123", json=payload)
    assert response.status_code == 200
    assert response.json()["user_id"] == "user_123"
    assert response.json()["data"]["name"] == "Alice Doe"

@patch("main.db")
def test_get_user_success(mock_db):
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {"name": "Alice Doe", "email": "alice@example.com", "role": "admin"}
    mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

    response = client.get("/api/users/user_123")
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Alice Doe"

@patch("main.db")
def test_get_user_not_found(mock_db):
    mock_doc = MagicMock()
    mock_doc.exists = False
    mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

    response = client.get("/api/users/nonexistent_user")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

@patch("main.db")
def test_update_user_success(mock_db):
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

    payload = {"name": "Alice Updated", "email": "alice@example.com", "role": "admin"}
    response = client.put("/api/users/user_123", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

@patch("main.db")
def test_delete_user_success(mock_db):
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

    response = client.delete("/api/users/user_123")
    assert response.status_code == 200
    assert response.json()["status"] == "success"


# --- 3. Telemetry Ingestion Tests ---

def test_ingest_telemetry_single():
    payload = {
        "device_id": "sensor_01",
        "event_type": "temperature_reading",
        "timestamp": "2026-08-13T12:00:00Z",
        "metadata": {"value": 24.5}
    }
    response = client.post("/telemetry", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["received"]["device_id"] == "sensor_01"

def test_ingest_telemetry_batch():
    payload = {
        "events": [
            {
                "device_id": "sensor_01",
                "event_type": "temperature",
                "timestamp": "2026-08-13T12:00:00Z"
            },
            {
                "device_id": "sensor_02",
                "event_type": "humidity",
                "timestamp": "2026-08-13T12:00:01Z"
            }
        ]
    }
    response = client.post("/telemetry/batch", json=payload)
    assert response.status_code == 200
    assert response.json()["processed_count"] == 2


# --- 4. Analytics Engine Tests (BigQuery) ---

@patch("bigquery_service.get_device_breakdown")
def test_get_analytics_success(mock_bq):
    mock_bq.return_value = [
        {"device_type": "Oculus Quest 3", "total_events": 1500},
        {"device_type": "Mobile WebXR", "total_events": 800}
    ]
    response = client.get("/analytics/device-breakdown")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 2

@patch("bigquery_service.get_device_breakdown")
def test_get_analytics_failure(mock_bq):
    mock_bq.return_value = None
    response = client.get("/analytics/device-breakdown")
    assert response.status_code == 500
    assert response.json()["detail"] == "BigQuery connection or query execution failed"


# --- 5. System Alerts Tests ---

@patch("main.db")
def test_receive_system_alert(mock_db):
    payload = {
        "severity": "CRITICAL",
        "message": "High error rate detected in telemetry worker",
        "details": {"error_code": 500}
    }
    response = client.post("/api/system/alerts", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"