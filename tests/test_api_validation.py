import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def test_review_endpoint_rejects_invalid_json_with_400():
    response = client.post(
        "/api/review",
        content="{invalid json",
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 400
    assert "error" in response.json()


def test_openapi_defines_explicit_response_models():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()

    health_response = schema["paths"]["/api/health"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    review_response = schema["paths"]["/api/review"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]

    assert health_response["$ref"] == "#/components/schemas/HealthResponse"
    assert review_response["$ref"] == "#/components/schemas/ReviewResponse"
