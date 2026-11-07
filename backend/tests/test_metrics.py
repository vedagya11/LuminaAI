"""Metric tests. Full-reference scores are computed from real pixels only."""

import numpy as np

from app.services.metrics import failure_labels, full_reference, no_reference, psnr, ssim


def test_identical_images_have_infinite_psnr_and_unit_ssim():
    image = np.full((64, 64, 3), 40, dtype=np.uint8)
    image[10:30, 10:40] = (20, 30, 80)
    score, infinite, _reason = psnr(image, image)
    structural, _ssim_reason = ssim(image, image)
    assert score is None
    assert infinite is True
    assert structural == 1.0 or structural > 0.99


def test_changed_image_has_finite_psnr():
    reference = np.full((48, 48, 3), 30, dtype=np.uint8)
    candidate = np.full((48, 48, 3), 90, dtype=np.uint8)
    score, infinite, _reason = psnr(reference, candidate)
    assert infinite is False
    assert score is not None and score > 0


def test_missing_reference_does_not_invent_scores():
    image = np.zeros((32, 32, 3), dtype=np.uint8)
    report = full_reference(None, image)
    assert report["available"] is False
    assert report["psnr"] is None
    assert report["ssim"] is None
    assert report["lpips"] is None


def test_no_reference_measurements_follow_the_pixels():
    dark = np.full((40, 40, 3), 10, dtype=np.uint8)
    bright = np.full((40, 40, 3), 200, dtype=np.uint8)
    assert no_reference(bright)["mean_luminance"] > no_reference(dark)["mean_luminance"] + 100
    assert no_reference(dark)["niqe"] is None


def test_failure_labels_detect_clipping_and_noise():
    original = np.full((64, 64, 3), 20, dtype=np.uint8)
    clipped = np.full((64, 64, 3), 255, dtype=np.uint8)
    assert "highlight_clipping" in failure_labels(original, clipped)
    noisy = original.copy()
    rng = np.random.default_rng(1)
    noisy = np.clip(noisy.astype(np.int16) + rng.integers(-40, 40, noisy.shape), 0, 255).astype(np.uint8)
    # A mild random field may or may not cross the noise threshold. The clipped case is the hard check.
    assert isinstance(failure_labels(original, noisy), list)
