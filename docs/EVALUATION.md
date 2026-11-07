# Evaluation methodology

Dataset scores are produced only by running the evaluator on files you already have. The repository does not download LOL, LOL-v2, or MIT-Adobe FiveK, and it does not contain a results table.

## Paired sets

From `backend/`, with the virtualenv active:

```bash
python -m evaluation.evaluate /absolute/path/to/dataset
```

The script looks for matching filenames in:

- `eval15/low` and `eval15/high` (LOL test split)
- `our485/low` and `our485/high` (LOL training split)
- `Test/Low` and `Test/Normal`, or `Low` and `Normal` (LOL-v2 style)
- `low` and `high` (a generic export, including FiveK pairs you export yourself)

FiveK is a retouching set, not a low-light pair set. Use it only after you have made your own low/high folders. The script resizes a reference that does not match the input and then computes PSNR and SSIM against that reference. LPIPS and NIQE are not part of this script: LPIPS is optional in the API, and NIQE parameters are not bundled.

For each available method it prints:

- mean finite PSNR and the count of identical (infinite) pairs
- mean SSIM
- mean processing time
- peak memory reported by `tracemalloc`
- up to eight frames whose measured labels fired

Labels, from `failure_labels`:

- `highlight_clipping` when the result's 95th luminance percentile is at least 250
- `under_enhanced` when a dark input (mean luminance under 40) gains fewer than 5 levels
- `noise_amplified` when output noise sigma exceeds both 3 and 1.5 times the input

If the folder is missing or has no pairs, the script exits with status 2 and prints the expected layout. It does not write placeholder scores.

`--limit N` evaluates the first N pairs. That is a subset, and the printout says how many images were used.

## Ablation

```bash
python -m evaluation.ablation
```

This uses one synthetic dark frame and turns classical stages off one at a time. The numbers are measurements of that frame. They are not LOL scores. The same Retinex ablation is asserted in `backend/tests/test_enhance.py`.

## What is not claimed

No leaderboard number in this repository was copied from a paper. Run the script on your machine and quote the printout, including the split and the image count.
