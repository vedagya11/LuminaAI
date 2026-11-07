"""Paired-dataset evaluation for LOL, LOL-v2, or a FiveK export.

This script does not download data and does not write scores unless the
folders below actually contain matching pairs.

Accepted layouts, relative to the dataset root:

- eval15/low and eval15/high
- our485/low and our485/high
- Low and Normal
- low and high
- Test/Low and Test/Normal

Usage, from the backend directory:

    python -m evaluation.evaluate /path/to/LOLdataset
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time
import tracemalloc

import cv2

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.enhance import enhance_classical
from app.services.hybrid import enhance_hybrid
from app.services.metrics import failure_labels, psnr, ssim
from app.services.zerodce import ModelUnavailable, enhance_zerodce, get_model_status

PAIR_CANDIDATES = (
    ("eval15/low", "eval15/high"),
    ("our485/low", "our485/high"),
    ("Test/Low", "Test/Normal"),
    ("Low", "Normal"),
    ("low", "high"),
)
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


def find_pairs(root: Path) -> tuple[Path, Path, list[tuple[Path, Path]]]:
    for low_name, high_name in PAIR_CANDIDATES:
        low_dir = root / low_name
        high_dir = root / high_name
        if not low_dir.is_dir() or not high_dir.is_dir():
            continue
        pairs = []
        for low_path in sorted(low_dir.iterdir()):
            if low_path.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            high_path = high_dir / low_path.name
            if high_path.is_file():
                pairs.append((low_path, high_path))
        if pairs:
            return low_dir, high_dir, pairs
    return root, root, []


def read_bgr(path: Path):
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Could not read {path}")
    return image


def run_method(name: str, image):
    if name == "classical":
        return enhance_classical(image)[0]
    if name == "deep_learning":
        return enhance_zerodce(image)[0]
    if name == "hybrid":
        return enhance_hybrid(image)[0]
    raise ValueError(name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate LUMINA restorers on paired images.")
    parser.add_argument("dataset", type=Path, help="Root folder of a local paired dataset.")
    parser.add_argument("--limit", type=int, default=0, help="Optional cap on the number of pairs.")
    args = parser.parse_args()
    root = args.dataset.expanduser()
    if not root.is_dir():
        print(f"Dataset folder does not exist: {root}")
        print("Place LOL, LOL-v2, or exported FiveK pairs locally. This script will not download them.")
        return 2
    _low, _high, pairs = find_pairs(root)
    if not pairs:
        print(f"No matching low/high pairs were found under {root}.")
        print("Expected one of: " + ", ".join(f"{a} + {b}" for a, b in PAIR_CANDIDATES))
        return 2
    if args.limit > 0:
        pairs = pairs[: args.limit]

    methods = ["classical"]
    if get_model_status().available:
        methods.extend(["deep_learning", "hybrid"])
    else:
        print(f"Learned methods skipped: {get_model_status().reason}")

    print(f"Pairs: {len(pairs)}")
    for method in methods:
        scores = []
        failures = []
        tracemalloc.start()
        started = time.perf_counter()
        for low_path, high_path in pairs:
            low = read_bgr(low_path)
            high = read_bgr(high_path)
            if low.shape != high.shape:
                high = cv2.resize(high, (low.shape[1], low.shape[0]), interpolation=cv2.INTER_CUBIC)
            try:
                restored = run_method(method, low)
            except ModelUnavailable as exc:
                print(f"{method} stopped: {exc}")
                break
            psnr_score, infinite, _reason = psnr(high, restored)
            structural, _ssim_reason = ssim(high, restored)
            scores.append((psnr_score, infinite, structural))
            labels = failure_labels(low, restored)
            if labels:
                failures.append((low_path.name, labels, psnr_score, structural))
        elapsed = time.perf_counter() - started
        _current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        finite = [item[0] for item in scores if item[0] is not None]
        structural_scores = [item[2] for item in scores if item[2] is not None]
        print(f"\n{method}")
        print(f"  images: {len(scores)}")
        if finite:
            print(f"  mean PSNR: {sum(finite) / len(finite):.4f} dB over {len(finite)} finite scores")
        infinite_count = sum(1 for item in scores if item[1])
        if infinite_count:
            print(f"  infinite PSNR (identical to reference): {infinite_count}")
        if structural_scores:
            print(f"  mean SSIM: {sum(structural_scores) / len(structural_scores):.4f}")
        if scores:
            print(f"  mean time: {elapsed / len(scores) * 1000:.2f} ms")
        print(f"  peak traced memory: {peak / (1024 * 1024):.2f} MiB")
        if failures:
            print("  failure labels:")
            for name, labels, psnr_score, structural in failures[:8]:
                print(f"    {name}: {', '.join(labels)} psnr={psnr_score} ssim={structural}")
        else:
            print("  failure labels: none on this sample")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
