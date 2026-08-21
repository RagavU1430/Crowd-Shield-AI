# CROWD-SHIELD: Phase 1 API Implementation

**Document ID:** CS-DOC-P1-02
**Version:** 1.0.0

## Base URL
`http://127.0.0.1:8000`

## Authentication
None required for MVP. CORS configured for local development origins only.

## Error Format
All error responses follow a consistent structure:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message"
  }
}
```

## Endpoints

### GET /api/health
**Health check endpoint** for load balancers and deployment validation.

**Response:**
```json
{
  "status": "ok",
  "service": "crowd-shield-backend",
  "phase": "phase-1"
}
```

**Status:** implemented

---

### POST /api/videos/upload
**Phase 1 video upload endpoint.** Accepts MP4 / WebM / MOV files, validates, stores safely, extracts metadata, and creates an analysis job.

**Request:**
- Method: `POST`
- Body: `multipart/form-data`
- Fields:
  - `file` (file): The video file to upload
  - `analysis_mode` (hidden form field): `"STANDARD"` (default)

**Response (success):**
```json
{
  "video_id": "2c50dc6bf00d44d3b1f37829d674bf9a.mp4",
  "filename": "event_video.mp4",
  "duration": 6.0,
  "width": 640,
  "height": 480,
  "fps": 15.0,
  "frame_count": 90,
  "status": "VALID",
  "job_id": "job_8338464e"
}
```

**Response (error - unsupported format):**
```json
{
  "error": {
    "code": "UNSupported_FORMAT",
    "message": "Unsupported format: .txt. Allowed: {'.mp4', '.webm', '.mov'}"
  }
}
```

**Response (error - file too large):**
```json
{
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "File too large. Maximum size: 100MB"
  }
}
```

**Response (error - invalid video):**
```json
{
  "error": {
    "code": "INVALID_VIDEO",
    "message": "The uploaded file could not be read as a valid video."
  }
}
```

**Status:** implemented

---

### GET /api/analysis/{job_id}
**Analysis job status polling endpoint.** Clients poll this endpoint to check the progress and stage of video analysis.

**URL parameters:**
- `job_id` (string): The job ID returned from the upload endpoint

**Response:**
```json
{
  "job_id": "job_8338464e",
  "video_id": "2c50dc6bf00d44d3b1f37829d674bf9a.mp4",
  "status": "UPLOADED",
  "progress": 0,
  "stage": "Pending"
}
```

**Statuses progression:**
`UPLOADED` -> `VALIDATING_VIDEO` -> `READING_VIDEO` -> `PREPARING` -> `COMPLETED` / `FAILED`

**Status:** implemented

## Models

### VideoUploadResponse
| Field | Type | Description |
|---|---|---|
| video_id | str | Server-generated safe filename |
| filename | str | Original user-provided filename |
| duration | float | Video duration in seconds |
| width | int | Video width in pixels |
| height | int | Video height in pixels |
| fps | float | Video frame rate |
| frame_count | int | Total frame count |
| status | str | `"VALID"` or error indicator |

### VideoMetadata
| Field | Type | Description |
|---|---|---|
| video_id | str | Server-generated safe filename |
| original_filename | str | User-provided original filename |
| stored_filename | str | Safe UUID-based stored filename |
| file_size | int | File size in bytes |
| format | str | Video file extension |
| upload_time | str | ISO-format upload timestamp |
| duration | float | Video duration in seconds |
| width | int | Video width in pixels |
| height | int | Video height in pixels |
| fps | float | Video frame rate |
| frame_count | int | Total frame count |
| status | str | `"VALID"` or `"INVALID"` |

### AnalysisStatus (enum)
| Value | Description |
|---|---|
| UPLOADED | Video uploaded, awaiting validation |
| VALIDATING_VIDEO | Video format and readability validation |
| READING_VIDEO | Video metadata extraction |
| PREPARING | Job preparing for analysis |
| COMPLETED | Analysis complete |
| FAILED | Analysis failed |

### AnalysisJob
| Field | Type | Description |
|---|---|---|
| job_id | str | Unique job identifier |
| video_id | str | Associated video identifier |
| status | AnalysisStatus | Current job status |
| progress | int | Progress percentage (0-100) |
| stage | str | Current processing stage |

### APIError
| Field | Type | Description |
|---|---|---|
| error.code | str | Machine-readable error code |
| error.message | str | Human-readable error message |

## CORS Configuration
**Development:**
- `allow_origins`: `http://127.0.0.1:5173` (React Vite dev server), `http://127.0.0.1:8000` (Backend)
- `allow_methods`: `GET`, `POST`
- `allow_headers`: `Content-Type`, `Authorization`

**Production:** (not configured for MVP; explicit origins only in development)

## Versioning
API is currently at phase-1 version. Future phases will add `/api/v2/` endpoints as the AI pipeline is integrated. Existing `/api/v1/` endpoints preserve the full AI pipeline for backward compatibility.

## API Compatibility
- Phase 1 endpoints (`/api/`) are new and do not break existing `/api/v1/` endpoints
- Frontend types aligned with backend Pydantic models
- No duplicate response formats; existing models reused where possible