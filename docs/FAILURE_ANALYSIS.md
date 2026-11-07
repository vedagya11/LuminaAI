# Failure analysis

These are the cases the implementation is expected to handle poorly. They are observations about the algorithms, not a scored benchmark.

## Classical CV

- A strong colored light can still look wrong after gray-world balancing, because the gains are global even when they are luminance-weighted.
- CLAHE can raise noise in a very dark, textured region after the illumination lift. The noise sigma in the response is allowed to increase, and the dashboard shows the before and after values.
- The gamma map is smooth because the illumination is a large Gaussian. A thin shadow next to a bright edge can be under-lifted.
- Frames that are already near mid gray keep gamma at 1. CLAHE can still change local contrast.

## Zero-DCE++

- The published checkpoint was trained as a low-light curve estimator. On an already bright photo it can still lift curves and clip highlights. Hybrid fusion reduces the network weight above luminance 0.70 for that reason.
- Noise in the input is not modeled inside Zero-DCE++. Amplification of that noise is why the fusion weight falls as the local Laplacian rises.
- CPU inference resizes the long side above `MAX_INFERENCE_SIDE` (default 1280). Fine detail on a large upload is reconstructed by the resize back, which the response flags with `resized_for_inference`.
- The upstream project does not publish a license file. Treat the checkpoint as a cited research artifact.

## Hybrid

- Fusion is a convex combination of the two results. It cannot invent texture that neither branch recovered.
- The color-cast penalty is one number for the whole frame, so a local colored region does not get its own balance.
- If Zero-DCE++ does not load, hybrid is unavailable. The API does not silently return the classical image under the hybrid name.

## How to see a failure on your data

`python -m evaluation.evaluate /path/to/pairs` prints filenames when `highlight_clipping`, `under_enhanced`, or `noise_amplified` fires, together with that pair's PSNR and SSIM. An empty dataset does not produce an example list.
