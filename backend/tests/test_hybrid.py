"""Fusion weights have to follow the picture, not a constant mix."""

import numpy as np

from app.services.hybrid import _fusion_weights


def test_dark_regions_receive_more_network_weight_than_highlights():
    height, width = 128, 800
    bgr = np.zeros((height, width, 3), dtype=np.uint8)
    bgr[:, : width // 2] = (25, 25, 25)
    bgr[:, width // 2 :] = (210, 210, 210)
    _classical, deep, summary = _fusion_weights(bgr)
    assert summary["deep_learning_dark_mean"] > summary["deep_learning_bright_mean"] + 0.2
    assert abs(summary["classical_mean"] + summary["deep_learning_mean"] - 1.0) < 0.02
    assert abs(summary["deep_learning_mean"] - 0.5) > 0.05
    assert float(deep[:, 30:90].mean()) > float(deep[:, -90:-30].mean())
