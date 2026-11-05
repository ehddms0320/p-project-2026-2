import io
import json
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)
PNG = b"\x89PNG\r\n\x1a\n" + b"fake-for-contract-test"

def manifest():
    return {"stream_id":"shift-val-001", "selection_strategy":"uncertainty", "budget_frames":1, "student_version":"student-v1", "frames":[{"frame_id":"f0001", "filename":"f0001.png", "timestamp_ms":100}]}

def test_health():
    assert client.get("/health").json()["status"] == "ok"

def test_job_accepts_matching_files():
    res = client.post("/v1/adaptation-jobs", data={"manifest":json.dumps(manifest())}, files=[("files",("f0001.png", io.BytesIO(PNG), "image/png"))])
    assert res.status_code == 202, res.text
    detail = client.get(res.json()["status_url"])
    assert detail.status_code == 200
    assert detail.json()["status"] == "queued"

def test_rejects_mismatched_filename():
    res = client.post("/v1/adaptation-jobs", data={"manifest":json.dumps(manifest())}, files=[("files",("wrong.png", io.BytesIO(PNG), "image/png"))])
    assert res.status_code == 422

def test_rejects_budget_overrun():
    m=manifest();m["budget_frames"]=1;m["frames"].append({"frame_id":"f0002","filename":"f0002.png","timestamp_ms":200})
    res=client.post("/v1/adaptation-jobs",data={"manifest":json.dumps(m)},files=[("files",("f0001.png", io.BytesIO(PNG),"image/png")),("files",("f0002.png",io.BytesIO(PNG),"image/png"))])
    assert res.status_code == 422

def test_adapter_not_found():
    assert client.get("/v1/adapters/missing/download").status_code == 404
