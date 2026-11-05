# API contract v0.1 — Edge ↔ Cloud

**Status: PROPOSAL.** Endpoint skeleton is implemented; actual inference, teacher labeling, training queue and adapter build are not. Swagger: `/docs`.

## Endpoints

| Method | Path | Contract |
|---|---|---|
| GET | `/health` | Service health and `mode: contract_stub` |
| POST | `/v1/adaptation-jobs` | Upload selected frames + JSON manifest; returns 202 and job_id |
| GET | `/v1/adaptation-jobs/{job_id}` | Read queued job state; in-memory only |
| GET | `/v1/adapters/{adapter_id}` | Adapter metadata, 404 until registry exists |
| GET | `/v1/adapters/{adapter_id}/download` | Binary adapter, 404 until artifacts exist |
| POST | `/v1/adapter-events` | Activation/rollback/failed feedback (not persisted) |

## POST /v1/adaptation-jobs

Request `multipart/form-data`: a string part called `manifest` containing JSON and repeated image parts named `files`. Each filename must match a `manifest.frames[*].filename` exactly. JPG/PNG; checks MIME and signature. Default cap: 64 frames / request, 5MiB / frame. These caps are *not* the research 3-level transmission budgets.

```json
{
  "stream_id": "shift-val-001",
  "environment_hint": "rain",
  "selection_strategy": "hybrid",
  "budget_frames": 2,
  "trigger": "drift",
  "drift_score": 0.91,
  "student_version": "student-v1",
  "frames": [
    {"frame_id":"f100", "filename":"f100.jpg", "timestamp_ms":10000, "uncertainty":0.82},
    {"frame_id":"f101", "filename":"f101.jpg", "timestamp_ms":10100, "uncertainty":0.75}
  ]
}
```

Allowed strategies: `random|uncertainty|diversity|hybrid`; triggers: `drift|periodic|manual`. Optional hint and scores must not be treated as ground-truth labels.

Response 202:
```json
{"job_id":"<uuid>", "status":"queued", "status_url":"/v1/adaptation-jobs/<uuid>"}
```

Job status target (future worker): `queued → labeling → filtering → training → ready`; `failed` on error. **Currently always queued** unless a future worker changes state.

## Activation event
`POST /v1/adapter-events` JSON: `stream_id`, `adapter_id`, `action` one of `activated|rolled_back|failed`, optional `previous_adapter_id`, `reason`. Response 201 with `event_id` and timestamp; not persisted yet.

## Future adapter schema (not implemented)
```json
{
  "adapter_id":"rain-v3",
  "environment_id":"rain",
  "student_version":"student-v1",
  "format":"onnx-compatible",
  "size_bytes":3120000,
  "sha256":"<64-hex-digits>",
  "created_at":"2026-11-05T00:00:00+00:00",
  "status":"ready"
}
```

## Error response
HTTP 404 missing job/adapter; 413 oversized or empty image; 415 unsupported MIME/signature; 422 manifest validation or mismatched filenames. Current error envelope follows FastAPI HTTPException `detail`.

## Team decisions required
- [ ] SHIFT six-class mapping, pixel/normalized bbox coordinate convention
- [ ] RQ1 window length, consecutive N detections and cooldown
- [ ] RQ2 three upload budgets (independent of API limits)
- [ ] Teacher pseudo-label filtering threshold and data format
- [ ] Adapter weight-only hot swap feasibility for ONNX Runtime; fallback small whole model
- [ ] Persistent job store / queue, idempotency, retries, authorization, retention, version/hash checks

## Quick verification
`pip install -e ".[dev]"`; `pytest -q`; `uvicorn app.main:app --reload`. Inspect `/docs`.
