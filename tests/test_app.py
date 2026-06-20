import os
import tempfile
from io import BytesIO
import pytest

from app import app
import storage

@pytest.fixture
def client():
    # Setup temporary database context to isolate testing changes
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_file = os.path.join(tmpdir, "test_db.json")
        orig_db = storage.DB_FILE
        orig_dir = storage.DATA_DIR
        storage.DB_FILE = test_db_file
        storage.DATA_DIR = tmpdir

        # Put Flask app in testing mode
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

        # Restore database configuration
        storage.DB_FILE = orig_db
        storage.DATA_DIR = orig_dir


def test_pages_load(client):
    # Scan/Home page loads successfully
    res = client.get("/")
    assert res.status_code == 200
    assert b"Every receipt tells a" in res.data

    # Dashboard page loads successfully
    res = client.get("/dashboard")
    assert res.status_code == 200
    assert b"Overview" in res.data

    # Challenges page loads successfully
    res = client.get("/challenges")
    assert res.status_code == 200
    assert b"Badges" in res.data

    # Weekly Report page loads successfully
    res = client.get("/report/weekly")
    assert res.status_code == 200
    assert b"Weekly Progress Report" in res.data


def test_api_dashboard(client):
    res = client.get("/api/dashboard")
    assert res.status_code == 200
    data = res.get_json()
    assert "scans" in data
    assert "total_co2e_kg" in data
    assert "current_streak" in data


def test_api_challenges_today(client):
    res = client.get("/api/challenges/today")
    assert res.status_code == 200
    data = res.get_json()
    assert "id" in data
    assert "title" in data
    assert "completed" in data


def test_api_scan_validation(client):
    # Uploading empty / missing parameters triggers bad request (400)
    res = client.post("/api/scan", data={})
    assert res.status_code == 400
    data = res.get_json()
    assert "error" in data


def test_api_scan_flow(client):
    # Uploading a mock JPEG file triggers the scan flow
    # Since the API key is placeholder, it falls back to the mock scanner
    data = {
        "receipt": (BytesIO(b"fake jpeg content"), "receipt.jpg")
    }
    res = client.post("/api/scan", data=data, content_type="multipart/form-data")
    assert res.status_code == 200

    payload = res.get_json()
    assert "scan" in payload
    assert "tip" in payload
    assert "streak" in payload
    assert "challenge" in payload

    # Verify the scan was saved in storage
    scan = payload["scan"]
    assert scan["id"] == 1
    assert len(scan["items"]) == 5
    assert scan["total_co2e_kg"] > 0
