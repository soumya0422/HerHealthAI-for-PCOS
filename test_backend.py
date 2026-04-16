import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model_loaded" in data

def test_predict_validation_error():
    # Attempt to send an impossible age to trigger Pydantic bounds evaluation
    response = client.post(
        "/predict",
        json={"age": 500.0, "weight": 60.0} # Age > 80 should fail
    )
    assert response.status_code == 422
    data = response.json()
    assert "Input should be less than or equal to 80" in str(data) or "Validation Error" in data.get("message", "")

def test_predict_success():
    # Attempt a successful prediction with valid bounds
    response = client.post(
        "/predict",
        json={
            "age": 25.0, 
            "weight": 60.0, 
            "height": 160.0, 
            "pulse": 72.0,
            "cycle_regular": 1,
            "exercise": 1
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "risk_percentage" in data
    assert "risk_level" in data
    assert "confidence" in data

def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "model_name" in data
    assert "accuracy" in data
