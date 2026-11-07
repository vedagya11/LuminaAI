"""Measured image metrics.

Full-reference scores (PSNR, SSIM, LPIPS) are computed only when a reference
image is supplied. They are never filled in from the original low-light frame
and never replaced with a constant. NIQE is not bundled, so that field stays
null with an explicit reason. LPIPS is reported only when the optional
package and its network weights actually load.
"""

from __future__ import annotations

import math

import cv2
import numpy as np

from app.services.enhance import _luminance, estimate_noise_sigma


def _same_shape(reference: np.ndarray, candidate: np.ndarray) -> bool:
    return reference.shape == candidate.shape


def psnr(reference_bgr: np.ndarray, candidate_bgr: np.ndarray) -> tuple[float | None, bool, str]:
    if not _same_shape(reference_bgr, candidate_bgr):
        return None, False, "PSNR needs the reference and the result to have the same shape."
    difference = reference_bgr.astype(np.float64) - candidate_bgr.astype(np.float64)
    mse = float(np.mean(difference ** 2))
    if mse == 0.0:
        return None, True, "PSNR is infinite because the images are identical."
    score = 10.0 * math.log10((255.0 ** 2) / mse)
    return round(score, 4), False, ""


def ssim(reference_bgr: np.ndarray, candidate_bgr: np.ndarray) -> tuple[float | None, str]:
    """Mean SSIM on the OpenCV Y channel, 11x11 Gaussian window."""

    if not _same_shape(reference_bgr, candidate_bgr):
        return None, "SSIM needs the reference and the result to have the same shape."
    first = _luminance(reference_bgr).astype(np.float64)
    second = _luminance(candidate_bgr).astype(np.float64)
    kernel = cv2.getGaussianKernel(11, 1.5)
    window = kernel @ kernel.T
    mu1 = cv2.filter2D(first, -1, window, borderType=cv2.BORDER_REFLECT)
    mu2 = cv2.filter2D(second, -1, window, borderType=cv2.BORDER_REFLECT)
    mu1_sq = mu1 * mu1
    mu2_sq = mu2 * mu2
    mu12 = mu1 * mu2
    sigma1 = cv2.filter2D(first * first, -1, window, borderType=cv2.BORDER_REFLECT) - mu1_sq
    sigma2 = cv2.filter2D(second * second, -1, window, borderType=cv2.BORDER_REFLECT) - mu2_sq
    sigma12 = cv2.filter2D(first * second, -1, window, borderType=cv2.BORDER_REFLECT) - mu12
    c1 = (0.01 * 255.0) ** 2
    c2 = (0.03 * 255.0) ** 2
    numerator = (2.0 * mu12 + c1) * (2.0 * sigma12 + c2)
    denominator = (mu1_sq + mu2_sq + c1) * (sigma1 + sigma2 + c2)
    score = float(np.mean(numerator / denominator))
    return round(score, 4), ""


def try_lpips(reference_bgr: np.ndarray, candidate_bgr: np.ndarray) -> tuple[float | None, str]:
    if not _same_shape(reference_bgr, candidate_bgr):
        return None, "LPIPS needs the reference and the result to have the same shape."
    try:
        import lpips
        import torch
    except ImportError:
        return None, "LPIPS is not installed. The score is not estimated."
    try:
        model = _lpips_model(lpips, torch)
        reference = _lpips_tensor(reference_bgr, torch)
        candidate = _lpips_tensor(candidate_bgr, torch)
        with torch.inference_mode():
            distance = model(reference, candidate)
        return round(float(distance.item()), 4), ""
    except Exception as exc:
        return None, f"LPIPS could not be computed: {exc}"


_lpips = None


def _lpips_model(lpips_module, torch_module):
    global _lpips
    if _lpips is None:
        _lpips = lpips_module.LPIPS(net="alex", verbose=False)
        _lpips.eval()
    return _lpips


def _lpips_tensor(bgr: np.ndarray, torch_module):
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    tensor = torch_module.from_numpy(np.ascontiguousarray(rgb)).permute(2, 0, 1).unsqueeze(0)
    return tensor * 2.0 - 1.0


def no_reference(bgr: np.ndarray) -> dict:
    luma = _luminance(bgr).astype(np.float32)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    percentiles = np.percentile(luma, [5, 50, 95])
    return {
        "mean_luminance": round(float(luma.mean()), 2),
        "contrast_stddev": round(float(luma.std()), 2),
        "noise_sigma": round(estimate_noise_sigma(luma.astype(np.uint8)), 2),
        "saturation_mean": round(float(hsv[:, :, 1].mean() / 255.0), 4),
        "luminance_p5": round(float(percentiles[0]), 2),
        "luminance_p50": round(float(percentiles[1]), 2),
        "luminance_p95": round(float(percentiles[2]), 2),
        "niqe": None,
        "niqe_reason": (
            "NIQE is not computed. The official natural-scene parameter file is not bundled, "
            "and a substitute score is not reported in its place."
        ),
    }


def full_reference(reference_bgr: np.ndarray | None, candidate_bgr: np.ndarray) -> dict:
    if reference_bgr is None:
        return {
            "available": False,
            "reason": "No reference image was provided. PSNR, SSIM, and LPIPS are not estimated.",
            "psnr": None,
            "psnr_is_infinite": False,
            "ssim": None,
            "lpips": None,
            "lpips_reason": "No reference image was provided.",
        }
    psnr_score, infinite, psnr_reason = psnr(reference_bgr, candidate_bgr)
    ssim_score, ssim_reason = ssim(reference_bgr, candidate_bgr)
    lpips_score, lpips_reason = try_lpips(reference_bgr, candidate_bgr)
    reason = " ".join(part for part in (psnr_reason, ssim_reason) if part)
    available = psnr_score is not None or infinite or ssim_score is not None
    return {
        "available": available,
        "reason": reason,
        "psnr": psnr_score,
        "psnr_is_infinite": infinite,
        "ssim": ssim_score,
        "lpips": lpips_score,
        "lpips_reason": lpips_reason,
    }


def failure_labels(original_bgr: np.ndarray, enhanced_bgr: np.ndarray) -> list[str]:
    """Labels derived from measurements. Empty means no listed failure fired."""

    before = no_reference(original_bgr)
    after = no_reference(enhanced_bgr)
    labels: list[str] = []
    if after["luminance_p95"] >= 250:
        labels.append("highlight_clipping")
    if after["mean_luminance"] < before["mean_luminance"] + 5 and before["mean_luminance"] < 40:
        labels.append("under_enhanced")
    if after["noise_sigma"] > max(3.0, before["noise_sigma"] * 1.5):
        labels.append("noise_amplified")
    return labels
