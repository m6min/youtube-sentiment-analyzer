from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"live": True}

def test_invalid_url_handling():
    response = client.post("/analyze", json={"video_url": "im_not_an_url"})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
