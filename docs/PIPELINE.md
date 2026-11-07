# Restoration pipeline

LUMINA AI runs three restorers. Each one returns the pixels it produced, the stages that ran, and measurements from those pixels.

## Classical CV

Implemented in `backend/app/services/enhance.py`.

1. Laplacian MAD noise estimate.
2. Bilateral denoise when sigma is at least 2. Strength follows the estimate. Clean frames skip it.
3. Gray-world white balance. Gains are clamped to `[0.75, 1.35]`. When enough pixels are above the noise floor, the means are weighted by luminance.
4. Multi-scale bright-channel illumination at scales 15, 80, and 250, capped by image size.
5. A gamma map, not one gamma for the whole frame. Where illumination is below 0.50, gamma is `log(0.52) / log(illumination)`, clipped to `[0.35, 0.92]`. Brighter illumination stays at 1, so a bright region beside a shadow is not pushed up with the shadow.
6. Restored luminance is `Y / illumination × illumination^gamma`.
7. A zero-mean log-domain multi-scale Retinex residual (Jobson) is added only as local detail in shadows. Subtracting the mean stops it from acting as a global brightness offset.
8. CLAHE on Y. Clip limit is 2.0 when the luminance standard deviation is at least 35, otherwise 2.8.
9. Luminance unsharp mask, amount 0.55, sigma 1.1.
10. Highlight rolloff blends the original luminance back in above 0.82.
11. Chroma is expanded by the luminance gain, capped at 1.25, and only where luminance increased.

`python -m evaluation.ablation` prints the measured luminance with each stage turned off. The pytest ablation checks that disabling Retinex reduces the shadow lift.

## Zero-DCE++

Implemented in `backend/app/services/zerodce.py`.

The network is the authors' `enhance_net_nopool`: depthwise-separable convolutions, 32 filters, a 3-channel curve, and eight quadratic iterations `x + r (x² − x)`. Curves are estimated at 1/12 resolution. The bundled file is Epoch99.

- SHA-256 `ca8855b90df9a80fa4195a831f33d3476b1964f787eb70602797c773067f3b84`
- Source: [Li-Chongyi/Zero-DCE_extension](https://github.com/Li-Chongyi/Zero-DCE_extension)
- The upstream repository has no LICENSE file. See `backend/models/README.md`.
- Inference is on CPU. A thread lock guards the cached module.
- The long side is limited by `MAX_INFERENCE_SIDE` (default 1280). Larger uploads are reduced for the forward pass and the result is resized back. The response says so.
- If the file is missing, the hash of the bundled name does not match, or PyTorch is absent, the method returns HTTP 501. It does not fall back to classical brightening.

## Hybrid

Implemented in `backend/app/services/hybrid.py`.

Both restorations are computed. A per-pixel network weight comes from darkness, local Laplacian noise, a global color-cast penalty, and a highlight gate above luminance 0.70. Classical weight is one minus that value. Highlights therefore keep the classical result, which has its own rolloff. The API returns the mean weights and the mean network weight inside dark and bright regions when those regions exist.

## Metrics

`backend/app/services/metrics.py`

| Score | Kind | When it is present |
| --- | --- | --- |
| Mean luminance, contrast, noise sigma | No reference | Always, from the result |
| Saturation and luminance percentiles | No reference | Always |
| PSNR, SSIM | Full reference | Only when a same-size reference upload is provided |
| LPIPS | Full reference | Only when a reference is provided and the `lpips` package can load its network. It is not installed by default. |
| NIQE | No reference | Not computed. The official parameter file is not bundled, and no substitute number is returned. |

An identical pair reports infinite PSNR explicitly (`psnr` null and `psnr_is_infinite` true), not a capped fake value.
