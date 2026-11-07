# LUMINA AI

LUMINA AI is a low-light image restoration web app for a computer vision hackathon (problem P1). A person uploads a dark, noisy photograph and downloads a version with lifted shadows, corrected color, local contrast, and retained detail.

This repository is the phase-1 foundation. Restoration is a real classical computer-vision pipeline in FastAPI. The React app calls that API. Zero-DCE is not integrated, PyTorch is not installed, and the Deep Learning and Hybrid modes cannot be selected.

## Problem statement

Robust low-light image restoration and enhancement: take underexposed, noisy images and return a natural result with better brightness, color, contrast, and preserved detail.

## Technology stack

| Layer | Choice |
| --- | --- |
| Frontend | React 18, Vite, Tailwind CSS, JavaScript |
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Vision | OpenCV, NumPy, Pillow |
| Tests | pytest, FastAPI TestClient, httpx |
| Frontend host | Vercel (config included; not deployed from this session) |
| API host | Render ( `render.yaml` included; not deployed from this session) |
| Source | Git repository, ready to push to GitHub |

PyTorch and Zero-DCE are the planned phase-2 stack. They are omitted on purpose so the app cannot pretend a model ran.

## Architecture

```
frontend/   React studio. API origin is VITE_API_BASE_URL.
backend/    FastAPI. Classical pipeline in app/services/enhance.py.
docs/       Pipeline, API, and deployment notes.
```

`GET /api/info` tells the UI which methods work. Only `classical` is `available: true`. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/API.md](docs/API.md), and [docs/PIPELINE.md](docs/PIPELINE.md).

The classical pipeline, in order:

1. Laplacian MAD noise estimate and a bilateral filter when the frame is noisy.
2. Clamped gray-world white balance.
3. Multi-scale bright-channel illumination with adaptive gamma (Retinex). Gamma is 1 when the frame is already bright.
4. CLAHE and a luminance unsharp mask.
5. Highlight rolloff and limited chroma restoration.

Shadows are lifted more than highlights. That is the check used in `backend/tests/test_enhance.py` against a global brightness add.

## Installation

Requirements: Python 3.11 or newer, Node.js 20 or newer.

```bash
git clone <your-github-url> LUMINA-AI
cd LUMINA-AI
```

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

`.env` is optional for local defaults. Edit `ALLOWED_ORIGINS` if the browser origin is not `http://localhost:5173` or `http://127.0.0.1:5173`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.development
```

`frontend/.env.development` already sets `VITE_API_BASE_URL` for a backend on port 8000. Change that file if the API origin differs. Do not hardcode the origin in `src/`.

## Backend startup

From `backend/`, with the virtualenv active:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Production, including Render, must use the platform port:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

- API: `http://127.0.0.1:8000`
- Health: `http://127.0.0.1:8000/api/health`
- OpenAPI: `http://127.0.0.1:8000/docs`

## Frontend startup

From `frontend/`:

```bash
npm run dev
```

Vite serves the studio at `http://127.0.0.1:5173`.

Production build:

```bash
VITE_API_BASE_URL=https://your-api.example.com npm run build
npm run preview
```

Vite inlines `VITE_API_BASE_URL` at build time. Set it in Vercel before building, then redeploy if the API URL changes.

## Environment variables

Backend (`backend/.env.example`):

| Variable | Default | Role |
| --- | --- | --- |
| `PORT` | `8000` | Process port. Render sets this. |
| `ALLOWED_ORIGINS` | local Vite origins | CORS allow-list, comma-separated |
| `MAX_UPLOAD_BYTES` | `10485760` | Upload limit |
| `MAX_IMAGE_PIXELS` | `24000000` | Decompression-bomb guard |
| `TEMP_DIR` | system temp `/lumina-ai` | Unique temp uploads |
| `JPEG_QUALITY` | `92` | Enhanced JPEG quality |

Frontend:

| Variable | Role |
| --- | --- |
| `VITE_API_BASE_URL` | API origin only, for example `http://127.0.0.1:8000`. No `/api` suffix and no trailing path. |

No secrets are required and none are committed.

## API documentation

| Method | Path | Behavior |
| --- | --- | --- |
| `GET` | `/api/health` | Status, service name, version |
| `GET` | `/api/info` | Formats, size limits, methods and availability |
| `POST` | `/api/upload` | Validate image bytes, return id, format, dimensions, size |
| `POST` | `/api/enhance` | Run a method and return JPEG bytes (base64), timing, and measured stats |

Details, status codes, and example bodies: [docs/API.md](docs/API.md).

`deep_learning` and `hybrid` return **501** with an explicit “not integrated” message. They do not return a brightened copy of the input.

## Testing

From `backend/` with the virtualenv active:

```bash
pytest
```

The suite covers health, info, PNG/JPEG/WEBP upload, text disguised as JPEG, corrupt JPEG, extension mismatch, empty file, oversized file, tiny image, temp-file deletion, classical enhancement (decoded output, dimensions, measured luminance, positive processing time), 501 for unfinished methods, and 422 for a missing file.

Frontend production bundle:

```bash
cd frontend
npm run build
```

GitHub Actions (`.github/workflows/test.yml`) runs pytest on Python 3.12 and `npm run build`.

## Deployment

These steps prepare a public deployment. They do not, by themselves, mean a public URL exists.

### Backend on Render

1. Push this repository to GitHub.
2. Create a Render web service from the repo. `render.yaml` sets root directory `backend`, the install command, the health check `/api/health`, and the start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
3. Set `ALLOWED_ORIGINS` to the exact Vercel origin (scheme + host, no path), comma-separated if you also want local Vite.
4. Deploy and open `https://<service>/api/health` before pointing the frontend at it.

`backend/runtime.txt` asks for Python 3.12.7.

### Frontend on Vercel

1. Import the same GitHub repository.
2. Set the project root directory to `frontend`. Framework preset: Vite.
3. Set `VITE_API_BASE_URL` to the Render origin, without `/api`.
4. Deploy. `frontend/vercel.json` sends non-file routes to `index.html`.

### After both are live

Call `GET /api/health` and `GET /api/info` on the public API. Upload a dark JPEG through the public site, confirm the before/after image and the statistics, and download the JPEG. If the browser reports a network error, the usual cause is a missing `VITE_API_BASE_URL` rebuild or an `ALLOWED_ORIGINS` value that does not match the Vercel origin.

## Local demo flow

1. Start the API on port 8000.
2. Start Vite.
3. Drop a JPG, JPEG, PNG, or WEBP.
4. Leave Classical CV selected. The other two cards stay disabled.
5. Choose **Enhance image**. The comparison slider and statistics come from the JSON response.
6. Choose **Download enhanced image**.

## Project layout

```
LUMINA-AI/
  frontend/          React studio
  backend/           FastAPI app and pytest suite
  docs/              Architecture, API, pipeline
  render.yaml        Render service definition
  README.md
```
