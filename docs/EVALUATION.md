# Evaluation — P1, robust low-light image restoration

LUMINA AI restores an underexposed photograph and reports measurements taken from the pixels it just produced. This file is the evaluation note for that system. It does not contain a leaderboard copied from a paper, and it does not invent PSNR, SSIM, LPIPS, or NIQE for a dataset that was not run here.

## Submission

| Item | Location |
| --- | --- |
| Repository | https://github.com/vedagya11/LuminaAI |
| Studio | https://lumina-ai-amber-psi.vercel.app |
| API | https://lumina-ai-api-il8i.onrender.com |
| This note | `docs/EVALUATION.md` |

The studio calls `GET /api/health` and `GET /api/info` on load. A method card can be selected only when `/api/info` marks that method `available: true`. Classical CV always runs. Deep Learning and Hybrid AI run only when the Zero-DCE++ Epoch99 checkpoint loads.

## Methods

1. **Classical CV** (`backend/app/services/enhance.py`). Laplacian noise estimate, bilateral denoise only when that estimate is high enough, luminance-weighted gray-world balance, multi-scale bright-channel illumination, a per-pixel gamma that lifts shadows and leaves already-bright pixels at gamma 1, log-domain detail in the shadows, CLAHE, a light unsharp mask, highlight rolloff, and a capped chroma restore.
2. **Deep Learning** (`backend/app/services/zerodce.py`). Zero-DCE++ (Li, Guo, Loy), the authors' Epoch99 weights, eight quadratic curve iterations, CPU inference. The long side is reduced only above 1280 pixels, then scaled back, and the response says so. A missing weight file returns HTTP 501. It does not fall back to classical brightening.
3. **Hybrid AI** (`backend/app/services/hybrid.py`). A per-pixel mix of the two results. The network weight rises in dark, clean regions and falls where local noise is high, where the frame has a strong color cast, and where luminance is already above 0.70. The response includes the measured mean weights. They are not fixed at one half.

## Metrics that are always measured

These come from the input and the output, with no reference image. The studio shows them in the Evaluation section.

| Metric | Meaning |
| --- | --- |
| Mean luminance | Average of the Y channel, 0–255 |
| Contrast | Standard deviation of Y |
| Noise estimate | Sigma from the median absolute deviation of a Laplacian on Y |
| Saturation | Mean HSV saturation, scaled to 0–1 |
| Luminance percentiles | 5th, 50th, and 95th percentile of Y |
| Processing time | Wall time of that method, in milliseconds |
| Dimensions and JPEG size | Size of the image that was returned |

Fusion responses also include `classical_mean`, `deep_learning_mean`, the means inside dark and bright regions, and the color-cast term.

## Metrics that need a reference

PSNR and SSIM are computed only when the request includes a reference of the same width and height. PSNR is `10 log10(255² / MSE)` on the BGR image. If the two images are identical, MSE is 0, `psnr` is null, and `psnr_is_infinite` is true. The score is not replaced with a large constant. SSIM is the mean structural similarity on Y, with an 11×11 Gaussian window.

In the studio, attach the normal exposure with **Optional reference for PSNR and SSIM**, then run Enhance or Compare. Without that file the full-reference block stays empty and the API says the scores were not estimated.

LPIPS is computed only if the optional `lpips` package is installed. It is not a project dependency, so the field is null and the reason says it was not estimated. NIQE is always null. The natural-scene parameter file is not bundled, and no substitute number is reported under that name.

## Paired datasets

LOL, LOL-v2, and MIT-Adobe FiveK are not downloaded by this repository, and this file does not list scores for them. To score a local copy:

```bash
cd backend
source .venv/bin/activate
python -m evaluation.evaluate /absolute/path/to/dataset
```

The script looks for matching filenames in `eval15/low` + `eval15/high`, `our485/low` + `our485/high`, `Test/Low` + `Test/Normal`, `Low` + `Normal`, or `low` + `high`. FiveK is a retouching set. Use it only after exporting your own low/high folders. A reference with a different size is resized to the input, then PSNR and SSIM are computed against that resized reference.

For each method that actually loads, the script prints the image count, mean finite PSNR, the count of identical pairs, mean SSIM, mean time, peak memory from `tracemalloc`, and up to eight frames that tripped a failure label. If the folder has no pairs, it exits with status 2 and prints the expected layout. It does not write placeholder scores. `--limit N` scores only the first N pairs and the printout says so.

Quote a number from that printout only together with the split name and the image count.

## Checks already in the test suite

`backend/tests` checks behavior, not a public benchmark:

- On a frame that is dark on one side and bright on the other, the dark side is lifted by more than the bright side. Disabling Retinex lifts the shadow less.
- Identical images report infinite PSNR rather than a capped number. A shape mismatch leaves PSNR and SSIM empty.
- Hybrid weights change across a dark region and a bright region. They are not a flat average.
- If the checkpoint path is missing, Deep Learning and Hybrid AI return HTTP 501.

## Failure labels

The API and the dataset script mark a result when a measurement crosses a threshold:

- `highlight_clipping` when the 95th luminance percentile is at least 250
- `under_enhanced` when a dark input (mean luminance under 40) gains fewer than 5 levels
- `noise_amplified` when output noise sigma is above 3 and also above 1.5 times the input sigma

Known weak cases are written in [FAILURE_ANALYSIS.md](FAILURE_ANALYSIS.md): colored lights after a global white balance, noise raised by CLAHE, thin shadows next to a bright edge, and Zero-DCE++ lifting a photo that was already bright. Hybrid lowers the network weight on those highlights. It cannot recover texture that neither branch produced.

## Ablation

```bash
python -m evaluation.ablation
```

This turns classical stages off one at a time on one synthetic dark frame and prints the measured luminance. Those numbers describe that frame. They are not LOL scores. The Retinex case is the same comparison the shadow test asserts.

## What this report does not claim

No PSNR, SSIM, LPIPS, or NIQE in a paper is repeated here as our result. A score exists only after the studio or `evaluation.evaluate` measured it on the images in front of it.
