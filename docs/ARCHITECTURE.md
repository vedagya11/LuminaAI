# Architecture

```
browser (React, Vite)
    |  VITE_API_BASE_URL
    |  GET  /api/health
    |  GET  /api/info
    |  POST /api/upload
    |  POST /api/enhance
    v
FastAPI
    ├─ config.Settings          environment only
    ├─ images.py                size, type, Pillow decode, unique temp file
    ├─ methods.py               classical available; deep learning and hybrid refused
    └─ enhance.py               OpenCV / NumPy classical pipeline
```

The frontend never chooses a result locally. Mode buttons that the info endpoint marks `available: false` are disabled, and the matching API call returns 501 if it is forged.

Images are not stored after the response. Temp files use `tempfile.mkstemp` with a UUID prefix and are removed in a `finally` block. User filenames are not used as paths.

## Configuration

| Variable | Where | Purpose |
| --- | --- | --- |
| `PORT` | Backend process | Bind port. Render injects this. Local default 8000. |
| `ALLOWED_ORIGINS` | Backend | Comma-separated CORS origins. |
| `MAX_UPLOAD_BYTES` | Backend | Raw upload ceiling. Default 10485760. |
| `MAX_IMAGE_PIXELS` | Backend | Pillow decompression-bomb ceiling. Default 24000000. |
| `TEMP_DIR` | Backend | Optional temp directory. |
| `JPEG_QUALITY` | Backend | Enhanced JPEG quality, 70–95. Default 92. |
| `VITE_API_BASE_URL` | Frontend build | API origin, no `/api` suffix. Inlined when Vite builds. |

There is no API key in this phase because the pipeline is local classical vision. Do not add a secret to the repository to stand in for one.

## Deployment shape

- Frontend: Vercel project, root directory `frontend`. `vercel.json` rewrites unknown paths to `index.html`. Set `VITE_API_BASE_URL` before the production build.
- Backend: Render web service from `render.yaml`, root directory `backend`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- After the API has a public origin, set `ALLOWED_ORIGINS` to the Vercel origin and redeploy the API. Then set `VITE_API_BASE_URL` to the API origin and redeploy the frontend.

Those hosted URLs are not created by this repository until someone with Vercel and Render access deploys it.
