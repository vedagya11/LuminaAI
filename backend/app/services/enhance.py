"""Classical low-light restoration.

Illumination is estimated per pixel and lifted with a local gamma, which is the
Retinex separation used by classical low-light work (Jobson multi-scale Retinex,
bright-channel illumination). A log-domain multi-scale residual restores local
detail without acting as a global brightness offset. Contrast is then local
(CLAHE), color uses a luminance-weighted gray-world balance, and pixels that
were already near white are blended back toward the original.
"""

from __future__ import annotations

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


def _replace_luma(bgr: np.ndarray, luma: np.ndarray) -> np.ndarray:
    ycrcb = cv2.cvtColor(bgr, cv2.COLOR_BGR2YCrCb)
    ycrcb[:, :, 0] = luma
    return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)


def _denoise(bgr: np.ndarray, sigma: float) -> tuple[np.ndarray, bool]:
    """Bilateral filter. Strength follows the measured noise; clean images are left alone."""

    if sigma < 2.0:
        return bgr, False
    sigma_color = float(np.clip(sigma * 1.6, 10.0, 45.0))
    filtered = cv2.bilateralFilter(bgr, d=5, sigmaColor=sigma_color, sigmaSpace=5)
    return filtered, True


def _gray_world(bgr: np.ndarray) -> tuple[np.ndarray, bool]:
    """Gray-world gains, weighted toward brighter pixels when the frame is not mostly black."""

    pixels = bgr.astype(np.float32)
    luma = _luminance(bgr).astype(np.float32)
    weight = np.clip((luma - 12.0) / 48.0, 0.0, 1.0)
    if float(weight.mean()) < 0.08:
        means = pixels.reshape(-1, 3).mean(axis=0)
    else:
        means = (pixels * weight[..., None]).sum(axis=(0, 1)) / float(weight.sum())
    gray = float(means.mean())
    gains = gray / np.clip(means, 1.0, None)
    gains = np.clip(gains, 0.75, 1.35).astype(np.float32)
    if float(np.max(np.abs(gains - 1.0))) < 0.03:
        return bgr, False
    corrected = np.clip(pixels * gains.reshape(1, 1, 3), 0, 255)
    return corrected.astype(np.uint8), True


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


def _gamma_map(illumination: np.ndarray) -> np.ndarray:
    """Per-pixel gamma. Dark illumination is lifted; bright illumination stays at 1.

    A single gamma computed from the frame mean cannot lift a shadow that sits
    next to a large bright region. The exponent is chosen so local illumination
    moves toward mid gray, then clipped to [0.35, 0.92].
    """

    target = 0.52
    gamma = np.ones_like(illumination, dtype=np.float32)
    dark = illumination < (target - 0.02)
    if not np.any(dark):
        return gamma
    safe = np.clip(illumination, 1e-3, 0.999)
    raw = np.log(target) / np.log(safe)
    gamma[dark] = np.clip(raw[dark], 0.35, 0.92)
    return gamma


def _apply_retinex(y_u8: np.ndarray, illumination: np.ndarray, gamma_map: np.ndarray) -> np.ndarray:
    luminance = y_u8.astype(np.float32) / 255.0
    adjusted = np.power(illumination, gamma_map)
    restored = luminance / np.maximum(illumination, 1e-3) * adjusted
    return np.clip(restored * 255.0, 0, 255).astype(np.uint8)


def _msr_detail(y_u8: np.ndarray) -> np.ndarray:
    """Zero-mean log-domain multi-scale Retinex residual (Jobson)."""

    luminance = np.clip(y_u8.astype(np.float32) / 255.0, 1e-3, 1.0)
    log_luminance = np.log(luminance)
    height, width = luminance.shape
    sigma_cap = max(3.0, min(height, width) / 4.0)
    residual = np.zeros_like(luminance)
    for weight, scale in zip((0.5, 0.3, 0.2), (15.0, 80.0, 250.0)):
        sigma = float(max(2.0, min(scale, sigma_cap)))
        blurred = np.clip(cv2.GaussianBlur(luminance, (0, 0), sigmaX=sigma, sigmaY=sigma), 1e-3, 1.0)
        residual += weight * (log_luminance - np.log(blurred))
    residual -= float(residual.mean())
    return residual


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


def _colorize_illumination(illumination: np.ndarray) -> np.ndarray:
    level = np.clip(illumination * 255.0, 0, 255).astype(np.uint8)
    return cv2.applyColorMap(level, cv2.COLORMAP_INFERNO)


def enhance_classical(
    bgr: np.ndarray,
    *,
    include_intermediates: bool = False,
    use_denoise: bool = True,
    use_gray_world: bool = True,
    use_retinex: bool = True,
    use_clahe: bool = True,
    use_unsharp: bool = True,
    use_highlight_rolloff: bool = True,
    use_chroma_restore: bool = True,
) -> tuple[np.ndarray, dict]:
    """Run the classical pipeline and return the BGR result plus measured metadata."""

    if bgr.ndim != 3 or bgr.shape[2] != 3:
        raise ValueError("Expected a 3-channel BGR image.")
    if bgr.shape[0] < 8 or bgr.shape[1] < 8:
        raise ValueError("Image is too small. The minimum size is 8 by 8 pixels.")

    original_y = _luminance(bgr)
    input_stats = measure_luminance(original_y)
    sigma = estimate_noise_sigma(original_y)
    stages: list[str] = ["noise_estimate"]
    intermediates: dict[str, np.ndarray] = {}

    current = bgr
    if use_denoise:
        current, denoised = _denoise(current, sigma)
        if denoised:
            stages.append("bilateral_denoise")
            if include_intermediates:
                intermediates["denoised"] = current.copy()

    if use_gray_world:
        current, balanced = _gray_world(current)
        if balanced:
            stages.append("adaptive_white_balance")

    ycrcb = cv2.cvtColor(current, cv2.COLOR_BGR2YCrCb)
    base_y = ycrcb[:, :, 0].copy()
    luminance = base_y
    gamma_value = 1.0
    if use_retinex:
        illumination = _illumination(current)
        gamma_map = _gamma_map(illumination)
        if include_intermediates:
            intermediates["illumination"] = _colorize_illumination(illumination)
        if float(gamma_map.min()) < 0.999:
            luminance = _apply_retinex(base_y, illumination, gamma_map)
            detail = _msr_detail(base_y)
            shadow = np.clip((80.0 - base_y.astype(np.float32)) / 80.0, 0.0, 1.0)
            delta = detail * 18.0 * shadow
            if float(np.max(np.abs(delta))) > 0.5:
                luminance = np.clip(luminance.astype(np.float32) + delta, 0, 255).astype(np.uint8)
                stages.append("msr_detail")
            stages.append("multiscale_retinex")
            gamma_value = round(float(gamma_map.mean()), 4)
            if include_intermediates:
                intermediates["retinex"] = _replace_luma(current, luminance)

    if use_clahe:
        luminance = _clahe(luminance)
        stages.append("clahe")
        if include_intermediates:
            intermediates["clahe"] = _replace_luma(current, luminance)

    if use_unsharp:
        luminance = _unsharp(luminance)
        stages.append("luminance_unsharp")

    if use_highlight_rolloff:
        luminance = _protect_highlights(luminance, original_y)
        stages.append("highlight_rolloff")

    if use_chroma_restore:
        original_chroma = ycrcb[:, :, 1].copy()
        ycrcb = _restore_chroma(ycrcb, base_y, luminance)
        if not np.array_equal(ycrcb[:, :, 1], original_chroma):
            stages.append("chroma_restore")
    else:
        ycrcb = ycrcb.copy()
        ycrcb[:, :, 0] = luminance

    enhanced = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
    output_y = _luminance(enhanced)
    meta = {
        "gamma": gamma_value,
        "stages": stages,
        "input": input_stats,
        "output": measure_luminance(output_y),
        "fusion_weights": None,
        "model": None,
        "intermediates": intermediates if include_intermediates else None,
    }
    return enhanced, meta


def encode_jpeg(bgr: np.ndarray, quality: int) -> bytes:
    ok, encoded = cv2.imencode(
        ".jpg",
        bgr,
        [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)],
    )
    if not ok:
        raise RuntimeError("Could not encode the enhanced image.")
    return encoded.tobytes()
