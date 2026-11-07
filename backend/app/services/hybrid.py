"""Adaptive fusion of the classical pipeline and Zero-DCE++.

Weights are spatial. Dark, clean pixels trust the curve network more.
Noisy pixels and pixels that were already bright trust the classical
pipeline, which has an explicit denoise stage and highlight rolloff.
A strong global color cast shifts weight toward classical white balance.
The blend is not a constant average.
"""

from __future__ import annotations

import cv2
import numpy as np

from app.services.enhance import _luminance, enhance_classical, measure_luminance
from app.services.zerodce import enhance_zerodce


def _fusion_weights(original_bgr: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    luma = _luminance(original_bgr).astype(np.float32) / 255.0
    laplacian = np.abs(cv2.Laplacian(luma, cv2.CV_32F, ksize=3))
    noise = cv2.GaussianBlur(laplacian, (0, 0), 1.2)
    noise_scale = float(np.percentile(noise, 95))
    if noise_scale > 1e-8:
        noise_norm = np.clip(noise / noise_scale, 0.0, 1.0)
    else:
        noise_norm = np.zeros_like(noise)
    darkness = np.clip((0.50 - luma) / 0.50, 0.0, 1.0)
    means = original_bgr.reshape(-1, 3).astype(np.float32).mean(axis=0)
    color_cast = float(np.std(means) / (float(means.mean()) + 1e-6))
    cast_penalty = float(np.clip(color_cast * 1.5, 0.0, 0.45))
    deep = darkness * (1.0 - 0.70 * noise_norm) * (1.0 - cast_penalty)
    highlight = np.clip((luma - 0.70) / 0.30, 0.0, 1.0)
    deep = np.clip(deep, 0.05, 0.90).astype(np.float32) * (1.0 - highlight)
    deep = deep.astype(np.float32)
    classical = (1.0 - deep).astype(np.float32)

    def _region(mask: np.ndarray, values: np.ndarray) -> float | None:
        if int(mask.sum()) < 16:
            return None
        return round(float(values[mask].mean()), 4)

    summary = {
        "classical_mean": round(float(classical.mean()), 4),
        "deep_learning_mean": round(float(deep.mean()), 4),
        "deep_learning_dark_mean": _region(luma < 0.20, deep),
        "deep_learning_bright_mean": _region(luma > 0.75, deep),
        "color_cast": round(color_cast, 4),
        "noise_sigma": round(float(np.std(laplacian) * 255.0), 4),
    }
    return classical, deep, summary


def enhance_hybrid(bgr: np.ndarray, *, include_intermediates: bool = False) -> tuple[np.ndarray, dict]:
    classical, classical_meta = enhance_classical(bgr, include_intermediates=include_intermediates)
    learned, learned_meta = enhance_zerodce(bgr, include_intermediates=include_intermediates)
    if learned.shape != classical.shape:
        learned = cv2.resize(learned, (classical.shape[1], classical.shape[0]), interpolation=cv2.INTER_CUBIC)
    classical_weight, deep_weight, summary = _fusion_weights(bgr)
    fused = (
        classical.astype(np.float32) * classical_weight[..., None]
        + learned.astype(np.float32) * deep_weight[..., None]
    )
    fused_u8 = np.clip(fused, 0, 255).astype(np.uint8)
    intermediates = None
    if include_intermediates:
        weight_u8 = np.clip(deep_weight * 255.0, 0, 255).astype(np.uint8)
        intermediates = {
            "classical": classical,
            "deep_learning": learned,
            "deep_learning_weight": cv2.applyColorMap(weight_u8, cv2.COLORMAP_VIRIDIS),
        }
        for name, image in (classical_meta.get("intermediates") or {}).items():
            intermediates[f"classical_{name}"] = image
        for name, image in (learned_meta.get("intermediates") or {}).items():
            intermediates[f"deep_learning_{name}"] = image
    return fused_u8, {
        "gamma": classical_meta.get("gamma"),
        "stages": ["classical_branch", "zerodce_pp_branch", "adaptive_fusion"],
        "input": measure_luminance(_luminance(bgr)),
        "output": measure_luminance(_luminance(fused_u8)),
        "fusion_weights": summary,
        "model": learned_meta.get("model"),
        "intermediates": intermediates,
    }
