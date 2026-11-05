"""Contract-first API starter. No Teacher, adapter worker, or persistent DB yet."""
from __future__ import annotations
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ValidationError, model_validator

BASE = Path(os.getenv("ARTIFACT_DIR", "artifacts")).resolve()
MAX_FRAME_BYTES = int(os.getenv("MAX_FRAME_BYTES", 5 * 1024 * 1024))
MAX_FRAMES = int(os.getenv("MAX_FRAMES", 64))
JOBS: dict[str, dict] = {}  # demo memory only
ADAPTERS: dict[str, dict] = {}  # empty until training pipeline is integrated
app = FastAPI(title="Edge-Cloud Adaptation API", version="0.1.0", description="Contract stub; no real model training")

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

class FrameMeta(BaseModel):
    frame_id: str = Field(min_length=1, max_length=128)
    filename: str = Field(min_length=1, max_length=255)
    timestamp_ms: int = Field(ge=0)
    uncertainty: float | None = Field(default=None, ge=0, le=1)

class UploadManifest(BaseModel):
    stream_id: str = Field(min_length=1, max_length=128)
    environment_hint: str | None = Field(default=None, max_length=64)
    selection_strategy: Literal["random", "uncertainty", "diversity", "hybrid"]
    budget_frames: int = Field(ge=1, le=64)
    trigger: Literal["drift", "periodic", "manual"] = "drift"
    drift_score: float | None = Field(default=None, ge=0, le=1)
    student_version: str = Field(min_length=1, max_length=128)
    frames: list[FrameMeta] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def validate_frames(self):
        ids = [f.frame_id for f in self.frames]
        names = [f.filename for f in self.frames]
        if len(ids) != len(set(ids)) or len(names) != len(set(names)):
            raise ValueError("frame_id and filename must be unique")
        if len(self.frames) > self.budget_frames:
            raise ValueError("frames exceed declared budget_frames")
        return self

class ActivationReport(BaseModel):
    stream_id: str = Field(min_length=1)
    adapter_id: str = Field(min_length=1)
    action: Literal["activated", "rolled_back", "failed"]
    previous_adapter_id: str | None = None
    reason: str | None = None

@app.get("/health")
def health():
    return {"status": "ok", "mode": "contract_stub", "timestamp": now()}

@app.post("/v1/adaptation-jobs", status_code=202)
async def create_job(manifest: str = Form(...), files: list[UploadFile] = File(...)):
    try:
        payload = UploadManifest.model_validate_json(manifest)
    except ValidationError as exc:
        raise HTTPException(422, detail=json.loads(exc.json())) from exc
    if len(files) != len(payload.frames) or len(files) > MAX_FRAMES:
        raise HTTPException(422, detail="files count must match manifest.frames and server limit")
    expected = {f.filename for f in payload.frames}
    actual = [f.filename for f in files]
    if len(actual) != len(set(actual)) or set(actual) != expected:
        raise HTTPException(422, detail="file names must exactly match manifest filenames")
    job_id = str(uuid.uuid4())
    folder = BASE / "uploads" / job_id
    folder.mkdir(parents=True, exist_ok=False)
    try:
        for item in files:
            if not item.filename or Path(item.filename).name != item.filename or not re.fullmatch(r"[A-Za-z0-9_.-]+\.(jpg|jpeg|png)", item.filename, re.I):
                raise HTTPException(422, detail="invalid image filename")
            if item.content_type not in {"image/jpeg", "image/png"}:
                raise HTTPException(415, detail="only image/jpeg or image/png allowed")
            body = await item.read(MAX_FRAME_BYTES + 1)
            if len(body) > MAX_FRAME_BYTES or not body:
                raise HTTPException(413, detail="invalid frame size")
            magic_ok = (item.content_type == "image/jpeg" and body.startswith(b"\xff\xd8\xff")) or (item.content_type == "image/png" and body.startswith(b"\x89PNG\r\n\x1a\n"))
            if not magic_ok:
                raise HTTPException(415, detail="image signature does not match content type")
            (folder / item.filename).write_bytes(body)
    except Exception:
        import shutil
        shutil.rmtree(folder, ignore_errors=True)
        raise
    job = {"job_id": job_id, "status": "queued", "created_at": now(), "updated_at": now(), "manifest": payload.model_dump(), "adapter_id": None, "error": None, "note": "Contract stub: no worker; queued jobs do not train automatically."}
    JOBS[job_id] = job
    return {"job_id": job_id, "status": job["status"], "status_url": f"/v1/adaptation-jobs/{job_id}"}

@app.get("/v1/adaptation-jobs/{job_id}")
def get_job(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(404, detail="job not found")
    return JOBS[job_id]

@app.get("/v1/adapters/{adapter_id}")
def adapter_metadata(adapter_id: str):
    if adapter_id not in ADAPTERS:
        raise HTTPException(404, detail="adapter not found")
    return {k: v for k, v in ADAPTERS[adapter_id].items() if k != "file_path"}

@app.get("/v1/adapters/{adapter_id}/download")
def download_adapter(adapter_id: str):
    adapter = ADAPTERS.get(adapter_id)
    if not adapter:
        raise HTTPException(404, detail="adapter not found")
    path = Path(adapter["file_path"])
    if not path.is_file():
        raise HTTPException(404, detail="artifact missing")
    return FileResponse(path, filename=f"{adapter_id}.bin", media_type="application/octet-stream")

@app.post("/v1/adapter-events", status_code=201)
def adapter_event(body: ActivationReport):
    if body.action == "activated" and body.adapter_id not in ADAPTERS:
        raise HTTPException(404, detail="unknown adapter")
    return {"event_id": str(uuid.uuid4()), "timestamp": now(), **body.model_dump()}
