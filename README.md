# LUMINA AI

LUMINA AI restores underexposed photographs in the browser. You upload a dark, noisy image and download a result with lifted shadows, corrected color, local contrast, and a record of what was measured.

The studio can run three restorers:

- **Classical CV** — multi-scale Retinex, a per-pixel gamma, CLAHE, edge-preserving denoise, adaptive gray-world balance, and highlight protection.
- **Deep learning** — Zero-DCE++ with the authors' Epoch99 checkpoint, on CPU.
- **Hybrid AI** — a spatial mix of those two results. The fusion weights are returned with the image.

If the checkpoint or PyTorch is missing, Deep Learning and Hybrid AI stay disabled. Classical CV still runs. Scores that need a reference image are left empty instead of being guessed.

## Problem statement

Robust low-light image restoration: take an underexposed, noisy photograph and return a more natural image with better brightness, color, and contrast while keeping detail and limiting blown highlights.

## Features

- Drag-and-drop upload for JPG, JPEG, PNG, and WEBP, checked by content rather than the extension alone.
- Preview, single-method enhancement, and a comparison of every method that actually loaded.
- Before/after slider and a side-by-side view.
- Optional intermediate images: illumination, Retinex, CLAHE, and the Zero-DCE++ curve map.
- Download of the JPEG the API returned.
- Quality dashboard: luminance, contrast, noise, saturation, percentiles, timing, file size, and fusion weights.
- Optional PSNR and SSIM when you attach a same-size reference. NIQE is not computed.

## Architecture

```text
React studio  -- VITE_API_BASE_URL -->  FastAPI
                                         |- validation and temp files
                                         |- classical pipeline
                                         |- Zero-DCE++ (cached, CPU)
                                         |- spatial hybrid fusion
                                         '- measured metrics
```

Diagrams and module notes: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Technology stack

| Layer | Choice |
| --- | --- |
| Frontend | React 18, Vite, Tailwind CSS, JavaScript |
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Vision | OpenCV, NumPy, Pillow |
| Learned model | PyTorch, Zero-DCE++ Epoch99 |
| Tests | pytest |
| Frontend host | Vercel configuration included. Not deployed from this workspace. |
| API host | Render configuration included. Not deployed from this workspace. |

## Algorithms

Classical stages, Zero-DCE++ iteration count, and the fusion formula are written in [docs/PIPELINE.md](docs/PIPELINE.md). The short version: shadows are lifted by dividing luminance by a multi-scale illumination map and raising that illumination to a local gamma. A bright region keeps gamma 1. Zero-DCE++ applies eight quadratic curves from a pretrained network. Hybrid weights move toward the network in dark, clean pixels and toward the classical result where the frame is noisy or already bright.

## Installation

Python 3.11 or newer, and Node.js 20 or newer.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

```bash
cd frontend
npm install
```

`frontend/.env.development` sets `VITE_API_BASE_URL` for an API on port 8000. The source under `frontend/src` does not hardcode that host.

PyTorch is a large install. The Zero-DCE++ file in `backend/models/` is about 52 KB.

## Local execution

API:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Site:

```bash
cd frontend
npm run dev
```

Open http://127.0.0.1:5173. Step-by-step demo notes are in [docs/DEMO.md](docs/DEMO.md).

Production API command, including Render:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Frontend production build:

```bash
cd frontend
VITE_API_BASE_URL=https://your-api.example.com npm run build
```

Vite inlines `VITE_API_BASE_URL` at build time. Set it in Vercel before building, and rebuild if the API origin changes.

## Environment variables

| Variable | Where | Role |
| --- | --- | --- |
| `PORT` | API process | Bind port. Render sets this. |
| `ALLOWED_ORIGINS` | API | Comma-separated browser origins for CORS. |
| `MAX_UPLOAD_BYTES` | API | Upload limit. Default 10 MiB. |
| `MAX_IMAGE_PIXELS` | API | Decompression-bomb guard. |
| `TEMP_DIR` | API | Optional temp directory. |
| `JPEG_QUALITY` | API | Enhanced JPEG quality. |
| `ZERODCE_WEIGHTS` | API | Optional checkpoint path. |
| `ZERODCE_SCALE` | API | Default 12. |
| `MAX_INFERENCE_SIDE` | API | Default 1280. |
| `VITE_API_BASE_URL` | Frontend build | API origin, no `/api` suffix. |

No API secret is required. Do not commit a filled `.env`.

## API documentation

| Method | Path | Behavior |
| --- | --- | --- |
| `GET` | `/api/health` | Status, name, version |
| `GET` | `/api/info` | Formats, limits, method availability |
| `POST` | `/api/upload` | Validate an image and return dimensions |
| `POST` | `/api/enhance` | Run one method |
| `POST` | `/api/compare` | Run every available method |

Details and status codes: [docs/API.md](docs/API.md). Live schemas: `http://127.0.0.1:8000/docs` while the API is running.

## Model details

Zero-DCE++ Epoch99, from Chongyi Li, Chunle Guo, and Chen Change Loy, "Learning to Enhance Low-Light Image via Zero-Reference Deep Curve Estimation," IEEE TPAMI 2022.

The checkpoint URL, SHA-256, and the missing upstream license are recorded in [backend/models/README.md](backend/models/README.md). The loader rejects the bundled filename if the hash changes. A missing file makes the learned modes return HTTP 501.

## Dataset evaluation

LOL, LOL-v2, and a FiveK export you prepare yourself can be scored with:

```bash
cd backend
source .venv/bin/activate
python -m evaluation.evaluate /path/to/dataset
python -m evaluation.ablation
```

The evaluator does not download data. If the folder has no pairs it exits without writing scores. Method: [docs/EVALUATION.md](docs/EVALUATION.md). This README does not list PSNR or SSIM figures because none have been produced against those datasets in this workspace.

## Results

Pytest covers health, uploads, corrupt and oversized files, temp cleanup, the classical shadow/highlight behavior, Retinex ablation, fusion weights, Zero-DCE++ when the checkpoint loads, and a 501 response when the checkpoint path is missing. Full-reference metrics stay null without a reference.

There is no checked-in dataset table. Run the evaluator and use its printout.

## Limitations

- NIQE is not reported. LPIPS runs only if you install the optional package and it can fetch its network.
- Zero-DCE++ can amplify noise and lift bright areas. Hybrid fusion is the control for that, not a guarantee.
- The upstream checkpoint has no license file.
- Large images are reduced before the network forward pass.
- The app is not deployed. Render's smaller instances may fail while installing PyTorch.

Failure notes: [docs/FAILURE_ANALYSIS.md](docs/FAILURE_ANALYSIS.md).

## Testing

```bash
cd backend
source .venv/bin/activate
pytest
```

```bash
cd frontend
npm run build
```

## Deployment instructions

These steps prepare a public deploy. They do not mean a public URL exists.

### Render

1. Push the repository, including `backend/models/zerodce_pp_epoch99.pth`.
2. Create a web service from `render.yaml`. Root directory is `backend`. Health check is `/api/health`. Start command is `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
3. Set `ALLOWED_ORIGINS` to the exact Vercel origin.
4. Use an instance with enough memory to install PyTorch.
5. Open `https://<service>/api/health` and `https://<service>/api/info` before pointing the site at it. `deep_learning` should be `available: true` when the checkpoint shipped.

### Vercel

1. Import the same repository and set the root directory to `frontend`.
2. Set `VITE_API_BASE_URL` to the Render origin, without `/api`.
3. Deploy. `frontend/vercel.json` sends unknown paths to `index.html`.

After both are live, enhance one dark image on the public site and confirm the dashboard numbers change with the photo. A browser network error is usually a missing rebuild of `VITE_API_BASE_URL` or an `ALLOWED_ORIGINS` value that does not match the site.
