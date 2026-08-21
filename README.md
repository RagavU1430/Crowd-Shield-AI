# CROWD-SHIELD

## Context-Aware Predictive Crowd Safety & Intervention System

**Tagline:** Sense → Predict → Simulate → Recommend → Protect

---

## Project Purpose

CROWD-SHIELD is a privacy-aware, human-in-the-loop crowd safety decision-support system.

The system analyzes a recorded crowd/event video, extracts anonymous crowd information, understands crowd movement and venue context, estimates evolving crowd-crush risk, identifies critical zones, simulates possible interventions, checks their feasibility, and recommends the safest feasible intervention to an authorized human operator.

**Core Pipeline:**
```
UPLOAD VIDEO
↓
SENSE
↓
UNDERSTAND
↓
PREDICT
↓
SIMULATE
↓
RECOMMEND
↓
HUMAN APPROVAL
↓
MONITOR
↓
ADAPT
```

---

## Architecture

```
crowd-shield/
│
├── frontend/              React + Vite command-center interface
│   └── src/components/    Upload, Dashboard, VideoViewer, common, layout
│
├── backend/               FastAPI service with AI pipeline
│   ├── app/
│   │   ├── api/           Phase 1 + v1 endpoints
│   │   ├── core/          Config, CORS, middleware
│   │   ├── models/        Pydantic schemas
│   │   ├── services/      Video, perception, analytics, simulation
│   │   └── main.py        Application entry point
│   └── tests/             Backend unit tests
│
├── ai/                    AI modules (deferred to Phase 2)
│   ├── detection/
│   ├── crowd_state/
│   ├── risk/
│   ├── trajectory/
│   └── simulation/
│
├── data/                  Uploads, processed, scenarios, fixtures
│   └── uploads/           User-uploaded test videos
│
├── configs/               Venue configuration JSON
│   └── venue_config.json  Benchmark demo venue
│
├── docs/                  Phase 0 + Phase 1 documentation
│   ├── phase-0/           Locked baseline documents
│   └── phase-1/           Phase 1 implementation docs
│
└── README.md              This file
```

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| **Backend API** | FastAPI (Python 3.11) | ASGI, automatic OpenAPI, async I/O |
| **Video Processing** | OpenCV (cv2) | Metadata extraction, readability validation |
| **Frontend Framework** | React 19 + Vite | Dark command-center theme, Canvas/SVG overlays |
| **Styling** | CSS custom properties | Navy/charcoal base, cyan/green/orange/red accents |
| **Testing** | pytest + TestClient | 11/11 backend tests passing |
| **Configuration** | Python dotenv | Environment variables for URLs, limits |
| **AI (Phase 2+)** | YOLOv8, Optical Flow | Deferred; clean module boundaries created |

---

## Project Structure

```
crowd-shield/
├── frontend/              React + Vite app
├── backend/               FastAPI service
│   ├── app/
│   ├── tests/
│   └── requirements.txt
├── ai/                    AI modules (Phase 2+)
├── data/                  Data directories
│   ├── uploads/
│   ├── processed/
│   ├── scenarios/
│   └── fixtures/
├── configs/               Venue configs
│   └── venue_config.json
├── docs/                  Documentation
│   ├── phase-0/           Locked Phase 0
│   └── phase-1/           Phase 1 docs
└── README.md
```

---

## Phase 0 Status

**STATUS:** LOCKED & FROZEN

All Phase 0 documents (12 files in `docs/phase-0/`) are the source of truth and must not be redesigned. Key Phase 0 baselines:

- **PROJECT_SCOPE.md:** 13 core pillars, 8 out-of-scope items locked
- **MVP_REQUIREMENTS.md:** 6 functional + 7 non-functional requirements locked
- **ARCHITECTURE.md:** FastAPI + React + YOLO architecture documented
- **DATA_FLOW.md:** 9-step end-to-end data lifecycle documented
- **API_PLAN.md:** FastAPI endpoint specs with Pydantic models
- **AI_PIPELINE.md:** 4-layer AI pipeline architecture
- **VENUE_MODEL.md:** Directed capacitated network flow graph
- **INTERVENTION_ENGINE.md:** Counterfactual intervention simulation
- **2_DAY_P.md:** 48-hour implementation roadmap
- **RISK_REGISTER.md:** 6 technical risks + ethical compliance
- **TEST_PLAN.md:** 4 benchmark scenarios + live demo script
- **VIDEO_FIRST_UPDATE.md:** Uploaded video as primary MVP input

---

## Phase 1 Status

**STATUS:** COMPLETE

Phase 1 delivers the foundation for all later AI and crowd-analysis phases. Key accomplishments:

- **Frontend:** React + Vite dashboard with upload, status polling, and command-center shell
- **Backend:** FastAPI with `/api/health`, `/api/videos/upload`, `/api/analysis/{job_id}` endpoints
- **Video Upload:** MP4/WebM/MOV validation, extension/MIME/size checks, OpenCV metadata extraction
- **Video Storage:** Safe UUID filenames in `data/uploads/`, metadata persisted in memory
- **Job Management:** Analysis job lifecycle with 6 statuses: UPLOADED, VALIDATING_VIDEO, READING_VIDEO, PREPARING, COMPLETED, FAILED
- **API Schemas:** Pydantic models: VideoUploadResponse, VideoMetadata, AnalysisJob, AnalysisStatus, APIError
- **Error Handling:** Clean error codes and messages, no stack traces exposed to frontend
- **CORS:** Explicit local development origins, no wildcard configuration
- **Configuration:** Environment variables via `.env` (MAX_VIDEO_SIZE, UPLOAD_DIRECTORY, URLs)
- **Tests:** 11/11 backend tests passing, E2E upload flow verified

---

## Installation

### Prerequisites

- Python 3.11+
- Node.js 18+ (for React Vite frontend)
- 100MB free disk space (uploads directory)

### Backend Setup

```bash
# 1. Clone/cd to project directory
cd C:\Users\Ragav U\OneDrive\Desktop\Ragav Folder\Projects\Dev Fusion\backend

# 2. Install dependencies
pip install -r requirements.txt  # or use existing env

# 3. Ensure test videos are present
# (CS_BENCH_6119FE_benchmark_crowd.mp4, vertical_slice_test.mp4 in backend/uploads/)

# 4. Start the backend server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Setup

```bash
# 1. cd to frontend directory
cd C:\Users\Ragav U\OneDrive\Desktop\Ragav Folder\Projects\Dev Fusion\frontend

# 2. Install dependencies
npm install

# 3. Start the Vite development server
npm run dev
```

The Vite dev server runs at `http://127.0.0.1:5173`.

### Environment Configuration

Create a `.env` file in the backend directory:

```
FRONTEND_URL=http://127.0.0.1:5173
BACKEND_URL=http://127.0.0.1:8000
MAX_VIDEO_SIZE_MB=100
UPLOAD_DIRECTORY=./uploads
ALLOWED_VIDEO_FORMATS=mp4,webm,mov
```

---

## Upload Workflow

### Phase 1 Upload Flow

1. **Open CROWD-SHIELD** at `http://127.0.0.1:8000`
2. **Select "Upload Crowd Video"** - UploadPage renders with VideoUploader component
3. **Select a valid video** (MP4, WebM, or MOV) - File validation checks extension and MIME type
4. **Upload the video** - Frontend sends `multipart/form-data` to `POST /api/videos/upload`
5. **Backend receives file** - Validates extension, MIME type, file readability
6. **File is safely stored** - Saved with UUID-based filename (e.g., `e150dfa7cd7b48f7b15bfa94777b8928.mp4`)
7. **Metadata extracted** - OpenCV extracts: duration, width, height, fps, frame_count
8. **Analysis job created** - Job ID returned, stored in memory job_store
9. **Frontend receives job ID** - UI transitions to status polling mode
10. **Frontend polls status** - `GET /api/analysis/{job_id}` every 1.5s
11. **Status reaches COMPLETED** - Dashboard shell becomes available
12. **User sees command center** - Dashboard with video viewer, risk placeholders, statistics

### Supported Formats
- MP4
- WebM
- MOV (where supported)

### Error States
- "Please select a video file." - No file selected
- "Unsupported video format. Please upload MP4, WebM, or MOV." - Invalid extension
- "The uploaded video could not be processed." - Invalid/corrupt video
- "File too large. Maximum size: 100MB." - Size limit exceeded
- "Unable to connect to the analysis server." - CORS/network error

---

## Current Limitations

### Phase 1 Deferred Features (Phase 2+)

- ❌ YOLO person detection and inference
- ❌ Optical flow computation
- ❌ Density calculation per zone
- ❌ Crowd-state engine (zone occupancy, flow convergence)
- ❌ Contextual risk engine (0-100 risk scoring)
- ❌ Risk trajectory forecasting
- ❌ Intervention simulator (what-if analysis)
- ❌ Feasibility engine (constraint checking)
- ❌ Reinforcement learning
- ❌ Live CCTV / RTSP integration
- ❌ Facial recognition / identity tracking
- ❌ Drone / satellite video feeds
- ❌ IoT sensor integration

### Known Issues

- Background video processing task uses FastAPI `BackgroundTasks`; status polling may show `UPLOADED`/`Pending` in test client; in production uvicorn, status progresses through all stages
- In-memory job store (`phase1_job_store`) not persistent across server restarts; replace with database for production
- No database persistence; all metadata stored in memory
- React frontend Vite dev server and FastAPI backend must both be running
- CORS configured for local development only; production requires explicit origin configuration

### Scope Out-of-Bounds (Per Phase 0)

- Aerial drone video ingestion
- Satellite imagery
- Telecom cellular density data
- Live emergency services CAD data
- Direct hardware / IoT gate actuator automation
- Facial recognition / identity profiling
- Reinforcement learning from scratch
- Distributed microservices / Kubernetes deployment

---

## Next Phase

**Phase 2 — Video Intelligence**

Connect the video foundation built in Phase 1 to the AI pipeline:

```
VIDEO (uploaded)
        ↓
YOLO inference          ← NEW in Phase 2
        ↓
Anonymous person detection
        ↓
Crowd state engine      ← NEW in Phase 2
        ↓
Density estimation
        ↓
Risk engine             ← NEW in Phase 2
        ↓
Risk forecasting
        ↓
Intervention simulator  ← NEW in Phase 2
        ↓
Feasibility check
        ↓
Recommendation → Human HITL
```

**Exact Phase 2 starting point:** Integrate `app.services.perception.yolo_detector.AnonymousPersonDetector` with the video metadata extraction already implemented in Phase 1. Replace the minimal metadata service with full YOLO-based person detection. Extend the analysis job status stages to include: DETECTION, CROWD ANALYSIS, RISK ANALYSIS, SIMULATION.

---

## License

Hackathon prototype. All Phase 0 documents locked & frozen. No external dependencies required for local runtime.