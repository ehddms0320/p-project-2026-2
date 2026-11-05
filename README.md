# Self-Adaptive Edge–Cloud Collaborative Video Analytics

AI P-실무프로젝트 · 2026-2 · 1분반 1조

> **Status: contract-first starter.** The API accepts frames and creates a queued job; it does **not** train a Teacher, run a worker, produce an adapter, or persist job state yet.

## Research questions
- RQ1: Detect performance drift without ground-truth labels during deployment.
- RQ2: Under equal upload budgets, compare Random, Uncertainty, Diversity, Hybrid frame selection.

## Pipeline
Edge Student (ONNX Runtime) → Drift Detection → Frame Selection → FastAPI Upload → Teacher Pseudo Labels → Adapter Training → Versioned Adapter → Edge Apply / Rollback

## Run locally
```bash
python -m venv .venv
# Activate venv for your OS.
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
pytest -q
```

Swagger: http://127.0.0.1:8000/docs

## Modules / owners
| Folder | Owner | Responsibility |
|---|---|---|
| data/ | 김동은 | SHIFT → YOLO, train/val, Student/Teacher |
| drift/ | 강서윤 | Confidence distribution and temporal inconsistency, RQ1 |
| selection/ | 김승룡 | Four selection strategies, RQ2 |
| training/ | 김승룡 · 김동은 | Pseudo-labeling, filtering, adapter training |
| edge/ | 이은민 | ONNX Runtime, API client, apply/rollback |
| app/ | 이은민 | FastAPI upload, jobs, adapter endpoints |
| tests/ | everyone | Tests |
| docs/ | everyone | Contract and integration decisions |

## Evaluation contract
SHIFT: Student/Teacher image training at 1Hz; drift and evaluation at 10Hz. Keep sequences disjoint between train and val. Exclude fog from training. Compare Baselines A/B/C with D, selection strategies 4 × upload budgets 3. Targets: drift recall >= 0.8, false alarm <= 0.2, fog recall >= 0.7, adaptation mAP improvement >= 5 percentage points vs A, adapter <= 5 MB.

## Collaboration
Work on `feature/<module>-<task>`, open a PR to main, require another team member to review, keep API_SPEC.md and tests synchronized. **Never commit source datasets, video clips, tokens, weights, or private data.**

Notion project: https://app.notion.com/p/40f8f4794bdb81129ce0e7eddf107f8e
