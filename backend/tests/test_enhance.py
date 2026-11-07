"""Direct tests of the classical restoration pipeline."""

import cv2
import numpy as np

from app.services.enhance import enhance_classical


def _y(bgr: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2YCrCb)[:, :, 0]


def test_dark_image_gets_brighter_without_a_flat_offset():
    rgb = np.zeros((128, 160, 3), dtype=np.uint8)
    rgb[:, :] = (22, 26, 30)
    rgb[40:90, 30:70] = (12, 14, 40)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    enhanced, meta = enhance_classical(bgr)

    assert enhanced.shape == bgr.shape
    assert meta["output"]["mean_luminance"] > meta["input"]["mean_luminance"] + 15
    assert meta["gamma"] < 1.0
    assert "multiscale_retinex" in meta["stages"]
    assert "clahe" in meta["stages"]
    assert not np.array_equal(enhanced, bgr)


def test_shadows_are_lifted_more_than_highlights():
    """A global brightness add would move both halves by the same amount."""

    height, width = 128, 800
    bgr = np.zeros((height, width, 3), dtype=np.uint8)
    bgr[:, : width // 2] = (25, 25, 25)
    bgr[:, width // 2 :] = (210, 210, 210)

    enhanced, _meta = enhance_classical(bgr)
    luminance = _y(enhanced)
    dark_out = float(luminance[:, 20:120].mean())
    bright_out = float(luminance[:, -120:-20].mean())
    dark_gain = dark_out - 25.0
    bright_gain = bright_out - 210.0

    assert dark_gain > bright_gain + 15
    assert bright_out < 250


def test_already_bright_image_is_not_blown_out():
    bgr = np.full((96, 128, 3), 180, dtype=np.uint8)
    bgr[20:60, 20:60] = (240, 230, 220)
    enhanced, meta = enhance_classical(bgr)
    mean_out = meta["output"]["mean_luminance"]

    assert meta["gamma"] == 1.0
    assert 120 < mean_out < 245
    assert int(enhanced.max()) <= 255
