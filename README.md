# 환경 변화에 스스로 적응하는 엣지-클라우드 협력형 실시간 영상 분석 시스템

**Self-Adaptive Edge-Cloud Collaborative Video Analytics via Continual Learning**

AI P-실무프로젝트(캡스톤디자인) · 2026학년도 2학기 · 1분반 1조

> **현재 개발 상태: API 초기 구조(Contract-first Starter)**  
> 프레임 업로드와 학습 작업(`queued`) 생성·조회가 가능한 초기 버전입니다. 아직 실제 Teacher 추론, 비동기 학습 워커, 어댑터 생성·배포 및 작업 상태의 영구 저장은 구현되지 않았습니다.

## 1. 프로젝트 개요

엣지 기기에서 실행되는 경량 객체 탐지 모델(Student)은 야간·비·안개 등 환경이 달라지면 탐지 정확도(mAP)가 낮아질 수 있습니다. 그러나 배포 환경에서는 정답 라벨을 바로 얻기 어렵고, 엣지 기기에서 모델을 다시 학습하기에는 연산 자원이 제한적입니다.

이 프로젝트는 **엣지에서 성능 저하를 감지하고 필요한 프레임만 선택해 서버로 전송한 뒤, 서버에서 학습한 경량 어댑터를 다시 엣지에 적용하는 시스템**을 구현합니다.

### 핵심 연구 질문

- **RQ1 — 드리프트 감지:** 배포 시점에 정답 라벨 없이 추론 통계만으로 성능 저하를 감지할 수 있는가?
- **RQ2 — 프레임 선별:** 동일한 전송 예산에서 Random, Uncertainty, Diversity, Hybrid 중 어떤 전략이 더 빠르고 큰 성능 회복을 가져오는가?

## 2. 전체 시스템 흐름

```text
[엣지: Student + ONNX Runtime]
             ↓
[드리프트 감지 (RQ1)]
             ↓
[프레임 선별 (RQ2)]
             ↓ 선별된 프레임 업로드
[FastAPI 서버]
             ↓
[Teacher 의사 라벨 생성 및 필터링]
             ↓
[경량 어댑터 학습 및 환경별 저장]
             ↓ 어댑터 다운로드
[엣지: 어댑터 적용 / 필요 시 롤백]
```

엣지는 **추론·감지·선별**, 서버는 **의사 라벨 생성·학습·어댑터 관리**를 담당합니다.

## 3. 팀원별 역할

| 팀원 | 주요 담당 업무 | 관련 폴더 |
|---|---|---|
| 강서윤 | 드리프트 감지 신호 추출, 이진/회귀 감지 모델 학습 및 평가 | `drift/` |
| 김승룡 | 프레임 선별 전략 4종 구현 및 평가, 서버 어댑터 학습 파이프라인 | `selection/`, `training/` |
| 김동은 | SHIFT 전처리, Student·Teacher 학습, 베이스라인(TENT 등) 비교 평가 | `data/`, `training/` |
| 이은민 | ONNX 변환·경량화, FastAPI 엣지-서버 통신, 실시간 시연 데모 | `edge/`, `app/` |

## 4. 프로젝트 폴더 구성

```text
p-project-2026-2/
├── app/                 # FastAPI 서버 및 API 엔드포인트
├── data/                # SHIFT 전처리·데이터 분할 관련 코드
├── drift/               # RQ1: 드리프트 감지
├── selection/           # RQ2: 프레임 선별 전략
├── training/            # Teacher 의사 라벨·어댑터 학습
├── edge/                # ONNX 추론·서버 통신·어댑터 적용
├── tests/               # API 테스트
├── docs/
│   ├── API_SPEC.md      # API 요청·응답 명세
│   └── INTEGRATION.md   # 모듈 간 연결 규칙
├── examples/            # 샘플 요청 데이터
├── notion/              # Notion 프로젝트 링크
├── .github/             # 자동 테스트 및 PR 템플릿
├── pyproject.toml       # Python 프로젝트·의존성 설정
└── README.md
```

## 5. 로컬 실행 방법

Python 3.10 이상 환경에서 실행합니다.

### ① 저장소 복제

```bash
git clone https://github.com/ehddms0320/p-project-2026-2.git
cd p-project-2026-2
```

### ② 가상환경 생성 및 활성화

```bash
python -m venv .venv
```

- **Windows PowerShell:** `.venv\Scripts\Activate.ps1`
- **macOS/Linux:** `source .venv/bin/activate`

### ③ 의존성 설치

```bash
python -m pip install -e ".[dev]"
```

### ④ FastAPI 서버 실행

```bash
uvicorn app.main:app --reload
```

서버 실행 후 다음 주소에서 API를 확인할 수 있습니다.

- **Swagger UI:** http://127.0.0.1:8000/docs
- **서버 상태 확인:** http://127.0.0.1:8000/health

### ⑤ 테스트 실행

```bash
pytest -q
```

현재 기본 API 계약 테스트 5개가 작성되어 있습니다. GitHub Actions에서도 테스트를 실행하도록 설정되어 있습니다.

## 6. API 초기 명세

| 방식 | 경로 | 기능 | 구현 상태 |
|---|---|---|---|
| `GET` | `/health` | 서버 정상 동작 확인 | 구현 |
| `POST` | `/v1/adaptation-jobs` | 선별된 프레임 업로드 및 학습 작업 요청 | 업로드·대기 상태 생성까지 구현 |
| `GET` | `/v1/adaptation-jobs/{job_id}` | 작업 진행 상태 조회 | 메모리 기반 조회 구현 |
| `GET` | `/v1/adapters/{adapter_id}` | 어댑터 메타데이터 조회 | 기본 엔드포인트만 구현 |
| `GET` | `/v1/adapters/{adapter_id}/download` | 어댑터 파일 다운로드 | 기본 엔드포인트만 구현 |
| `POST` | `/v1/adapter-events` | 어댑터 적용·롤백·실패 이벤트 보고 | 요청 검증·응답 구현 |

요청 데이터 구조와 예시는 [API 명세서](docs/API_SPEC.md), 모듈 연결 규칙은 [통합 문서](docs/INTEGRATION.md)를 참고하세요. **현재 API가 실제 모델 학습까지 수행하는 것은 아닙니다.**

## 7. 데이터셋 및 성능 평가 계획

- **데이터셋:** SHIFT 합성 주행 데이터셋(6개 클래스)
- **학습:** Student/Teacher 이미지 단위 학습에 1Hz 샘플링
- **드리프트 감지 및 평가:** 10Hz 전체 프레임
- **데이터 분리:** 학습과 평가 시퀀스가 겹치지 않도록 구성하며, 안개 환경은 미학습 환경 평가용으로 분리
- **비교 대상:** A(적응 없음), B(주기적 적응), C(TENT 또는 BN Adapt), D(제안 방식)
- **프레임 선별 실험:** 전략 4종 × 전송 예산 3단계

| 평가 항목 | 목표 |
|---|---|
| 적응 필요 구간 Recall | 0.8 이상 |
| 정상 구간 오경보율 | 0.2 이하 |
| 미학습 환경(안개) Recall | 0.7 이상 |
| 프레임 선별 효과 | 예산 3단계 중 2단계 이상에서 Random 대비 우수 |
| 환경 변화 구간 평균 mAP | Baseline A 대비 5%p 이상 향상 |
| 어댑터 파일 크기 | 5MB 이하 |

위 수치는 **과제계획서의 목표값**이며 달성 결과가 아닙니다. 최종 성능은 동일 평가 스트림에서 실험해 검증합니다.

## 8. GitHub 협업 규칙

1. `main` 브랜치는 통합 기준으로 사용하고, 개발은 `feature/<모듈>-<작업>` 형태의 브랜치에서 진행합니다.
2. 작업이 끝나면 Pull Request(PR)를 생성하고 팀원 리뷰를 거쳐 병합합니다.
3. API 요청·응답을 바꾸면 `docs/API_SPEC.md`와 관련 테스트를 함께 수정합니다.
4. 실행에 필요한 라이브러리는 `pyproject.toml`에서 관리합니다.
5. **원본 데이터셋, 영상, 모델 가중치, 비밀키, 개인정보는 GitHub에 업로드하지 않습니다.**

## 9. 프로젝트 문서 및 협업 공간

- [Notion 프로젝트 홈](https://app.notion.com/p/40f8f4794bdb81129ce0e7eddf107f8e)
- [Notion 개발 태스크 보드](https://app.notion.com/p/ec825e31945b4a4ba3d1b5a4fcec1954)
- [Notion API 명세](https://app.notion.com/p/40f8f4794bdb816db495f9b9311a47ff)
- [GitHub API 명세](docs/API_SPEC.md)

---

본 저장소는 **2026학년도 2학기 AI P-실무프로젝트(캡스톤디자인)** 개발용 저장소입니다.
