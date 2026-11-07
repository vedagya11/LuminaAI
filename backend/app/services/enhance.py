"""Classical low-light restoration.

This is a pixel pipeline, not a brightness slider and not a neural network.
Illumination is estimated per pixel and lifted separately from reflectance,
which is the Retinex model used by classical low-light work (Jobson MSR,
bright-channel illumination). Contrast is then local (CLAHE), and color is
corrected with a clamped gray-world assumption (Buchsbaum).

Zero-DCE and any hybrid learned stage are intentionally absent.
"""

from __future__ import annotations

import math

import cv2
import numpy as np


def _luminance(bgr: np.ndarray) -> np.ndarray:
    ycrcb = cv2.cvtColor(bgr, cv2.COLOR_BGR2YCrCb)
    return ycrcb[:, :, 0]


def estimate_noise_sigma(y_u8: np.ndarray) -> float:
    """Robust noise estimate from the median absolute deviation of a Laplacian."""

    laplacian = cv2.Laplacian(y_u8, cv2.CV_64F, ksize=3)
    median = float(np.median(laplacian))
    mad = float(np.median(np.abs(laplacian - median)))
    return mad / 0.6745 if mad else 0.0


def measure_luminance(y_u8: np.ndarray) -> dict[str, float]:
    values = y_u8.astype(np.float32)
    return {
        "mean_luminance": round(float(values.mean()), 2),
        "contrast_stddev": round(float(values.std()), 2),
        "noise_sigma": round(estimate_noise_sigma(y_u8), 2),
    }


def _denoise(bgr: np.ndarray, sigma: float) -> tuple[np.ndarray, bool]:
    """Bilateral filter. Strength follows the measured noise; clean images are left alone."""

    if sigma < 2.0:
        return bgr, False
    sigma_color = float(np.clip(sigma * 1.6, 10.0, 45.0))
    filtered = cv2.bilateralFilter(bgr, d=5, sigmaColor=sigma_color, sigmaSpace=5)
    return filtered, True


def _gray_world(bgr: np.ndarray) -> tuple[np.ndarray, np.ndarray, bool]:
    """Scale BGR channels toward a common mean. Gains are clamped so a strong cast cannot explode."""

    pixels = bgr.astype(np.float32)
    means = pixels.reshape(-1, 3).mean(axis=0)
    gray = float(means.mean())
    gains = gray / np.clip(means, 1.0, None)
    gains = np.clip(gains, 0.75, 1.35).astype(np.float32)
    if float(np.max(np.abs(gains - 1.0))) < 0.03:
        return bgr, np.ones(3, dtype=np.float32), False
    corrected = np.clip(pixels * gains.reshape(1, 1, 3), 0, 255)
    return corrected.astype(np.uint8), gains, True


def _illumination(bgr: np.ndarray) -> np.ndarray:
    """Multi-scale bright-channel illumination in the range (0, 1]."""

    bright = bgr.max(axis=2).astype(np.float32) / 255.0
    height, width = bright.shape
    sigma_cap = max(3.0, min(height, width) / 4.0)
    scales = (15.0, 80.0, 250.0)
    weights = (0.5, 0.3, 0.2)
    illumination = np.zeros_like(bright, dtype=np.float32)
    for weight, scale in zip(weights, scales):
        sigma = float(max(2.0, min(scale, sigma_cap)))
        illumination += weight * cv2.GaussianBlur(bright, (0, 0), sigmaX=sigma, sigmaY=sigma)
    return np.clip(illumination, 1e-3, 1.0)


def _adaptive_gamma(illumination: np.ndarray) -> float:
    """Choose gamma so a dark mean illumination moves toward mid gray.

    Already-bright images keep gamma = 1 so highlights are not pushed further.
    """

    mean_illumination = float(np.mean(illumination))
    target = 0.52
    if mean_illumination >= target - 0.02:
        return 1.0
    gamma = math.log(target) / math.log(max(mean_illumination, 1e-3))
    return float(np.clip(gamma, 0.35, 0.92))


def _apply_retinex(y_u8: np.ndarray, illumination: np.ndarray, gamma: float) -> np.ndarray:
    luminance = y_u8.astype(np.float32) / 255.0
    adjusted = np.power(illumination, gamma)
    restored = luminance / illumination * adjusted
    return np.clip(restored * 255.0, 0, 255).astype(np.uint8)


def _clahe(y_u8: np.ndarray) -> np.ndarray:
    height, width = y_u8.shape
    tiles_x = max(1, min(8, width // 8))
    tiles_y = max(1, min(8, height // 8))
    clip = 2.0 if float(y_u8.std()) >= 35.0 else 2.8
    clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(tiles_x, tiles_y))
    return clahe.apply(y_u8)


def _unsharp(y_u8: np.ndarray) -> np.ndarray:
    values = y_u8.astype(np.float32)
    blurred = cv2.GaussianBlur(values, (0, 0), 1.1)
    sharpened = values + 0.55 * (values - blurred)
    return np.clip(sharpened, 0, 255).astype(np.uint8)


def _protect_highlights(enhanced_y: np.ndarray, original_y: np.ndarray) -> np.ndarray:
    """Blend original luminance back in only where the source was already near white."""

    original = original_y.astype(np.float32) / 255.0
    weight = np.clip((original - 0.82) / 0.18, 0.0, 1.0).astype(np.float32)
    mixed = enhanced_y.astype(np.float32) * (1.0 - weight) + original_y.astype(np.float32) * weight
    return np.clip(mixed, 0, 255).astype(np.uint8)


def _restore_chroma(ycrcb: np.ndarray, base_y: np.ndarray, final_y: np.ndarray) -> np.ndarray:
    """Expand chroma only where luminance was lifted, capped at 25 percent."""

    base = base_y.astype(np.float32)
    final = final_y.astype(np.float32)
    scale = np.ones_like(base, dtype=np.float32)
    np.divide(final, np.maximum(base, 1.0), out=scale, where=base > 1.0)
    scale = np.clip(scale, 1.0, 1.25)
    restored = ycrcb.copy()
    for index in (1, 2):
        channel = ycrcb[:, :, index].astype(np.float32)
        restored[:, :, index] = np.clip(128.0 + (channel - 128.0) * scale, 0, 255).astype(np.uint8)
    restored[:, :, 0] = final_y
    return restored


def enhance_classical(bgr: np.ndarray) -> tuple[np.ndarray, dict]:
    """Run the classical pipeline and return the BGR result plus measured metadata."""

    if bgr.ndim != 3 or bgr.shape[2] != 3:
        raise ValueError("Expected a 3-channel BGR image.")
    if bgr.shape[0] < 8 or bgr.shape[1] < 8:
        raise ValueError("Image is too small. The minimum size is 8 by 8 pixels.")

    original_y = _luminance(bgr)
    input_stats = measure_luminance(original_y)
    sigma = estimate_noise_sigma(original_y)
    stages: list[str] = []

    current, denoised = _denoise(bgr, sigma)
    if denoised:
        stages.append("bilateral_denoise")

    current, _gains, balanced = _gray_world(current)
    if balanced:
        stages.append("gray_world")

    illumination = _illumination(current)
    gamma = _adaptive_gamma(illumination)
    ycrcb = cv2.cvtColor(current, cv2.COLOR_BGR2YCrCb)
    base_y = ycrcb[:, :, 0].copy()
    luminance = base_y
    if gamma < 0.999:
        luminance = _apply_retinex(base_y, illumination, gamma)
        stages.append("multiscale_retinex")

    luminance = _clahe(luminance)
    stages.append("clahe")
    luminance = _unsharp(luminance)
    stages.append("luminance_unsharp")
    luminance = _protect_highlights(luminance, original_y)
    stages.append("highlight_rolloff")

    original_chroma = ycrcb[:, :, 1].copy()
    ycrcb = _restore_chroma(ycrcb, base_y, luminance)
    if not np.array_equal(ycrcb[:, :, 1], original_chroma):
        stages.append("chroma_restore")

    enhanced = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
    output_y = _luminance(enhanced)
    return enhanced, {
        "gamma": round(gamma, 4),
        "stages": stages,
        "input": input_stats,
        "output": measure_luminance(output_y),
    }


def encode_jpeg(bgr: np.ndarray, quality: int) -> bytes:
    ok, encoded = cv2.imencode(
        ".jpg",
        bgr,
        [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)],
    )
    if not ok:
        raise RuntimeError("Could not encode the enhanced image.")
    return encoded.tobytes()
