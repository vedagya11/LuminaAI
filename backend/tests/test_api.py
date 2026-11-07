"""HTTP tests for health, validation, and enhancement."""

from uuid import UUID

import cv2
import numpy as np
import pytest

from app.config import get_settings
from app.services.images import leftover_temp_files
from tests.conftest import dark_scene, rgb_bytes


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "LUMINA AI"
    assert body["version"] == "1.0.0"


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["health"] == "/api/health"


def test_info_lists_only_classical_as_available(client):
    response = client.get("/api/info")
    assert response.status_code == 200
    body = response.json()
    assert set(body["supported_formats"]) == {"jpeg", "jpg", "png", "webp"}
    assert body["max_upload_bytes"] > 0
    methods = {item["id"]: item for item in body["methods"]}
    assert methods["classical"]["available"] is True
    assert methods["deep_learning"]["available"] is False
    assert methods["hybrid"]["available"] is False
    assert "Zero-DCE" in methods["deep_learning"]["description"]


def test_cors_allows_configured_frontend_origin(client):
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_valid_png_upload(client):
    payload = rgb_bytes(dark_scene(), "PNG")
    response = client.post(
        "/api/upload",
        files={"file": ("night.png", payload, "image/png")},
    )
    assert response.status_code == 200
    body = response.json()
    UUID(body["request_id"])
    assert body["format"] == "png"
    assert body["width"] == 160
    assert body["height"] == 120
    assert body["size_bytes"] == len(payload)
    assert body["filename"] == "night.png"


def test_valid_jpeg_and_webp_upload(client):
    scene = dark_scene(96, 80)
    jpeg = rgb_bytes(scene, "JPEG", quality=90)
    webp = rgb_bytes(scene, "WEBP", quality=80)
    jpeg_response = client.post("/api/upload", files={"file": ("a.jpeg", jpeg, "image/jpeg")})
    webp_response = client.post("/api/upload", files={"file": ("a.webp", webp, "image/webp")})
    assert jpeg_response.status_code == 200
    assert jpeg_response.json()["format"] == "jpeg"
    assert webp_response.status_code == 200
    assert webp_response.json()["format"] == "webp"


def test_invalid_text_disguised_as_jpeg(client):
    response = client.post(
        "/api/upload",
        files={"file": ("notes.jpg", b"this is not an image", "image/jpeg")},
    )
    assert response.status_code == 400
    assert "corrupted" in response.json()["detail"].lower()


def test_unsupported_extension(client):
    response = client.post(
        "/api/upload",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400
    assert "Unsupported" in response.json()["detail"]


def test_content_does_not_match_extension(client):
    payload = rgb_bytes(dark_scene(64, 64), "PNG")
    response = client.post(
        "/api/upload",
        files={"file": ("really.png.jpg", payload, "image/jpeg")},
    )
    assert response.status_code == 400
    assert "does not match" in response.json()["detail"]


def test_corrupted_jpeg_header(client):
    payload = b"\xff\xd8\xff" + b"\x00" * 64 + b"not-a-real-body"
    response = client.post(
        "/api/upload",
        files={"file": ("broken.jpg", payload, "image/jpeg")},
    )
    assert response.status_code == 400
    assert "corrupted" in response.json()["detail"].lower()


def test_empty_file(client):
    response = client.post(
        "/api/upload",
        files={"file": ("empty.png", b"", "image/png")},
    )
    assert response.status_code == 400


def test_oversized_image(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_upload_bytes", 500)
    payload = rgb_bytes(np.random.default_rng(0).integers(0, 255, (80, 80, 3), dtype=np.uint8), "PNG")
    assert len(payload) > 500
    response = client.post(
        "/api/upload",
        files={"file": ("big.png", payload, "image/png")},
    )
    assert response.status_code == 413
    assert "limit" in response.json()["detail"].lower()


def test_tiny_image_rejected(client):
    payload = rgb_bytes(np.zeros((4, 4, 3), dtype=np.uint8), "PNG")
    response = client.post("/api/upload", files={"file": ("tiny.png", payload, "image/png")})
    assert response.status_code == 400
    assert "too small" in response.json()["detail"].lower()


def test_temp_files_are_removed(client, monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "temp_dir", str(tmp_path))
    payload = rgb_bytes(dark_scene(), "PNG")
    response = client.post("/api/upload", files={"file": ("night.png", payload, "image/png")})
    assert response.status_code == 200
    assert leftover_temp_files(str(tmp_path)) == []


def test_enhance_classical_returns_a_real_image(client):
    scene = dark_scene(180, 140)
    payload = rgb_bytes(scene, "JPEG", quality=95)
    response = client.post(
        "/api/enhance",
        files={"file": ("night.jpg", payload, "image/jpeg")},
        data={"method": "classical"},
    )
    assert response.status_code == 200
    body = response.json()
    UUID(body["request_id"])
    assert body["method"] == "classical"
    assert body["width"] == 180
    assert body["height"] == 140
    assert body["processing_time_ms"] > 0
    assert body["media_type"] == "image/jpeg"
    assert body["output"]["mean_luminance"] > body["input"]["mean_luminance"] + 10
    assert "clahe" in body["stages"]
    assert "multiscale_retinex" in body["stages"]

    decoded = cv2.imdecode(
        np.frombuffer(__import__("base64").b64decode(body["image_base64"]), dtype=np.uint8),
        cv2.IMREAD_COLOR,
    )
    assert decoded is not None
    assert decoded.shape[1] == 180
    assert decoded.shape[0] == 140
    assert body["output_bytes"] == len(__import__("base64").b64decode(body["image_base64"]))


def test_enhance_rejects_unavailable_and_unknown_methods(client):
    payload = rgb_bytes(dark_scene(64, 64), "PNG")
    files = {"file": ("night.png", payload, "image/png")}
    deep = client.post("/api/enhance", files=files, data={"method": "deep_learning"})
    hybrid = client.post("/api/enhance", files=files, data={"method": "hybrid"})
    unknown = client.post("/api/enhance", files=files, data={"method": "magic"})
    assert deep.status_code == 501
    assert "Zero-DCE" in deep.json()["detail"]
    assert hybrid.status_code == 501
    assert unknown.status_code == 400


def test_enhance_corrupted_file(client):
    response = client.post(
        "/api/enhance",
        files={"file": ("broken.jpg", b"\xff\xd8\xffgarbage", "image/jpeg")},
        data={"method": "classical"},
    )
    assert response.status_code == 400


def test_enhance_missing_file(client):
    response = client.post("/api/enhance", data={"method": "classical"})
    assert response.status_code == 422


def test_path_traversal_filename_is_reduced_to_basename(client):
    payload = rgb_bytes(dark_scene(32, 32), "PNG")
    response = client.post(
        "/api/upload",
        files={"file": ("../../etc/passwd.png", payload, "image/png")},
    )
    assert response.status_code == 200
    assert response.json()["filename"] == "passwd.png"
    assert "/" not in response.json()["filename"]
