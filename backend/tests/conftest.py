"""Shared fixtures for API tests."""

import io

from fastapi.testclient import TestClient
import numpy as np
from PIL import Image
import pytest

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def rgb_bytes(array: np.ndarray, image_format: str, **save_kwargs) -> bytes:
    buffer = io.BytesIO()
    Image.fromarray(array, mode="RGB").save(buffer, format=image_format, **save_kwargs)
    return buffer.getvalue()


def dark_scene(width: int = 160, height: int = 120) -> np.ndarray:
    """A dim scene with a darker corner and a small color patch. RGB uint8."""

    image = np.zeros((height, width, 3), dtype=np.uint8)
    columns = np.linspace(10, 36, width, dtype=np.float32)
    image[:, :, 0] = columns.reshape(1, width)
    image[:, :, 1] = (columns * 0.85).astype(np.uint8)
    image[:, :, 2] = (columns * 1.4).clip(0, 255).astype(np.uint8)
    image[: height // 3, : width // 4] = (6, 8, 14)
    image[height // 3 : 2 * height // 3, width // 2 : 3 * width // 4] = (18, 42, 28)
    return image
