# Demo

## Local

Terminal 1, API:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Terminal 2, site:

```bash
cd frontend
npm run dev
```

Open http://127.0.0.1:5173

1. Drop a dark JPG, JPEG, PNG, or WEBP.
2. Confirm the mode cards. Classical CV is always available. Deep Learning and Hybrid AI are available when `backend/models/zerodce_pp_epoch99.pth` loads. The nav shows the API version.
3. Choose **Enhance selected mode** for one method, or **Compare available methods** for every method that loaded.
4. Use **Slider** or **Side by side**.
5. Turn on **Include intermediate images** before the run if you want the illumination map, Retinex, CLAHE, or the Zero-DCE++ curve map from that run.
6. Attach a same-size reference only when you want PSNR and SSIM. Without it, those rows stay empty on purpose.
7. **Download selected image** saves the JPEG returned by the API.

Health check: http://127.0.0.1:8000/api/health

Interactive API docs: http://127.0.0.1:8000/docs

## What to say in a demo

- Classical restoration is per-pixel Retinex plus CLAHE, not a brightness slider. The shadow/highlight test in `backend/tests/test_enhance.py` is the evidence.
- Deep learning is Zero-DCE++ Epoch99, cited, CPU, cached. The response includes the checkpoint name and SHA-256.
- Hybrid weights are measured per image. Read the classical and network means on the quality dashboard.
- NIQE is blank because its parameter file is not in the repo. Do not quote an NIQE number.

There is no public deployment yet. Vercel and Render files are prepared; see the README.
