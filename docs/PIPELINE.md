# Classical restoration pipeline

LUMINA AI phase 1 enhances a photograph with OpenCV and NumPy. It does not load a neural network. Zero-DCE is a later phase and is refused by the API with HTTP 501.

The implementation lives in `backend/app/services/enhance.py`. Every statistic returned by `POST /api/enhance` is measured on the image that was just processed.

## Stages

1. **Noise estimate.** Median absolute deviation of a 3×3 Laplacian on the Y channel, scaled by 0.6745. This is a robust sigma estimate, not a constant.

2. **Bilateral denoise.** Applied only when that sigma is at least 2. `sigmaColor` is `clip(sigma × 1.6, 10, 45)` and `sigmaSpace` is 5. Clean frames skip this stage, and the response will not list `bilateral_denoise`.

3. **Gray-world color constancy.** Per-channel gains pull B, G, and R toward their joint mean. Gains outside `[0.75, 1.35]` are clamped. Gains within 3 percent of 1 are ignored so a neutral image is not recolored.

4. **Multi-scale illumination.** The bright channel (max of B, G, R) is blurred at scales 15, 80, and 250 and mixed with weights 0.5, 0.3, and 0.2. Each scale is capped at a quarter of the shorter image side so small uploads stay stable.

5. **Adaptive gamma on illumination only.** Let `m` be the mean illumination. If `m` is already at least 0.50, gamma is 1 and this stage is skipped. Otherwise gamma is `log(0.52) / log(m)`, clipped to `[0.35, 0.92]`. Restored luminance is `Y / illumination × illumination^gamma`. Shadows move more than highlights. A single added brightness offset cannot do that.

6. **CLAHE** on the Y channel. Clip limit is 2.0 when the luminance standard deviation is at least 35, otherwise 2.8. Tile grid is at most 8×8 and shrinks with the image.

7. **Luminance unsharp mask.** `Y + 0.55 × (Y − Gaussian(Y, σ=1.1))`. Chroma is not sharpened.

8. **Highlight rolloff.** Original pixels at or above luminance 0.82 are blended back toward the source, fully at white. This keeps lamps and windows from clipping.

9. **Chroma restore.** Cr and Cb are expanded by the luminance gain, capped at 1.25, and only where luminance increased. The stage is omitted when the chroma planes do not change.

## What this is not

- It is not `convertScaleAbs`, a global gamma on the whole BGR image, or a histogram stretch presented as a model.
- It is not Zero-DCE, Retinexformer, or any checkpoint. PyTorch is not installed in this phase, so a missing weight file cannot be confused with a working model.
- Processing time is `time.perf_counter()` around `enhance_classical` only. It is not a stored benchmark.
