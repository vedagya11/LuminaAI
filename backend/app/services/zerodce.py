"""Zero-DCE++ inference.

The network and iteration count follow the authors' `enhance_net_nopool`
(Li, Guo, Loy), scale factor 12, eight quadratic curve iterations, and the
published Epoch99 checkpoint. Curve parameters are estimated on a 12x
downsample and applied at the working resolution. This module never
initializes a random network and never returns a classically brightened
image in place of a failed load.

Upstream repository: https://github.com/Li-Chongyi/Zero-DCE_extension
That repository does not ship a LICENSE file. The checkpoint is used with
attribution, not relicensed by LUMINA AI.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import threading

import cv2
import numpy as np

OFFICIAL_SHA256 = "ca8855b90df9a80fa4195a831f33d3476b1964f787eb70602797c773067f3b84"
OFFICIAL_FILENAME = "zerodce_pp_epoch99.pth"
PAPER = "Li, Guo, Loy. Learning to Enhance Low-Light Image via Zero-Reference Deep Curve Estimation. IEEE TPAMI, 2022."

_lock = threading.Lock()
_model = None
_model_key: str | None = None
_status = None
_status_key: str | None = None


class ModelUnavailable(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class ModelStatus:
    available: bool
    reason: str
    sha256: str = ""
    path: str = ""


def bundled_weights_path() -> Path:
    return Path(__file__).resolve().parents[2] / "models" / OFFICIAL_FILENAME


def resolved_weights_path() -> Path:
    from app.config import get_settings

    configured = get_settings().zerodce_weights.strip()
    if configured:
        return Path(configured).expanduser()
    return bundled_weights_path()


def reset_model_cache() -> None:
    global _model, _model_key, _status, _status_key
    with _lock:
        _model = None
        _model_key = None
        _status = None
        _status_key = None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _build_network(scale_factor: int):
    import torch
    from torch import nn
    import torch.nn.functional as F

    class CurveLayer(nn.Module):
        def __init__(self, in_channels: int, out_channels: int) -> None:
            super().__init__()
            self.depth_conv = nn.Conv2d(
                in_channels, in_channels, kernel_size=3, stride=1, padding=1, groups=in_channels
            )
            self.point_conv = nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=1, padding=0)

        def forward(self, incoming):
            return self.point_conv(self.depth_conv(incoming))

    class ZeroDCEPlus(nn.Module):
        def __init__(self, scale: int) -> None:
            super().__init__()
            self.relu = nn.ReLU(inplace=True)
            self.scale_factor = scale
            filters = 32
            self.e_conv1 = CurveLayer(3, filters)
            self.e_conv2 = CurveLayer(filters, filters)
            self.e_conv3 = CurveLayer(filters, filters)
            self.e_conv4 = CurveLayer(filters, filters)
            self.e_conv5 = CurveLayer(filters * 2, filters)
            self.e_conv6 = CurveLayer(filters * 2, filters)
            self.e_conv7 = CurveLayer(filters * 2, 3)

        def enhance(self, image, curve):
            result = image
            for _ in range(8):
                result = result + curve * (torch.pow(result, 2) - result)
            return result

        def forward(self, image):
            if self.scale_factor == 1:
                downsampled = image
            else:
                downsampled = F.interpolate(
                    image, scale_factor=1 / self.scale_factor, mode="bilinear", align_corners=False
                )
            first = self.relu(self.e_conv1(downsampled))
            second = self.relu(self.e_conv2(first))
            third = self.relu(self.e_conv3(second))
            fourth = self.relu(self.e_conv4(third))
            fifth = self.relu(self.e_conv5(torch.cat([third, fourth], 1)))
            sixth = self.relu(self.e_conv6(torch.cat([second, fifth], 1)))
            curve = torch.tanh(self.e_conv7(torch.cat([first, sixth], 1)))
            if self.scale_factor != 1:
                curve = F.interpolate(
                    curve,
                    size=image.shape[-2:],
                    mode="bilinear",
                    align_corners=False,
                )
            return self.enhance(image, curve), curve

    return ZeroDCEPlus(scale_factor), torch


def get_model_status() -> ModelStatus:
    global _status, _status_key
    path = resolved_weights_path()
    key = str(path.resolve()) if path.exists() else str(path)
    with _lock:
        if _status is not None and _status_key == key:
            return _status
        status = _inspect_status(path)
        _status = status
        _status_key = key
        return status


def _inspect_status(path: Path) -> ModelStatus:
    if not path.is_file():
        return ModelStatus(
            False,
            "Zero-DCE++ weights were not found. Deep learning and hybrid enhancement are unavailable.",
            path=str(path),
        )
    try:
        digest = _sha256(path)
    except OSError as exc:
        return ModelStatus(False, f"Zero-DCE++ weights could not be read: {exc}", path=str(path))
    if path.name == OFFICIAL_FILENAME and digest != OFFICIAL_SHA256:
        return ModelStatus(
            False,
            "The bundled Zero-DCE++ checkpoint failed its SHA-256 check.",
            sha256=digest,
            path=str(path),
        )
    try:
        import torch  # noqa: F401
    except ImportError:
        return ModelStatus(
            False,
            "PyTorch is not installed, so Zero-DCE++ cannot run.",
            sha256=digest,
            path=str(path),
        )
    return ModelStatus(True, "", sha256=digest, path=str(path))


def _load_model():
    global _model, _model_key
    status = get_model_status()
    if not status.available:
        raise ModelUnavailable(status.reason)
    from app.config import get_settings

    settings = get_settings()
    key = f"{status.path}:{settings.zerodce_scale}"
    with _lock:
        if _model is not None and _model_key == key:
            return _model
        import torch

        network, torch_module = _build_network(settings.zerodce_scale)
        try:
            state = torch_module.load(status.path, map_location="cpu", weights_only=True)
        except TypeError:
            state = torch_module.load(status.path, map_location="cpu")
        if isinstance(state, dict) and "state_dict" in state and isinstance(state["state_dict"], dict):
            state = state["state_dict"]
        if not isinstance(state, dict):
            raise ModelUnavailable("Zero-DCE++ checkpoint does not contain a state dict.")
        cleaned = {name.removeprefix("module."): value for name, value in state.items()}
        network.load_state_dict(cleaned, strict=True)
        network.eval()
        for parameter in network.parameters():
            parameter.requires_grad_(False)
        _model = network
        _model_key = key
        return network


def _fit_working_size(bgr: np.ndarray, max_side: int) -> tuple[np.ndarray, bool]:
    height, width = bgr.shape[:2]
    long_side = max(height, width)
    if long_side <= max_side:
        return bgr, False
    scale = max_side / float(long_side)
    resized = cv2.resize(
        bgr,
        (max(12, int(round(width * scale))), max(12, int(round(height * scale)))),
        interpolation=cv2.INTER_AREA,
    )
    return resized, True


def _pad_reflect(tensor, multiple: int):
    import torch.nn.functional as F

    height, width = tensor.shape[-2:]
    pad_h = (multiple - height % multiple) % multiple
    pad_w = (multiple - width % multiple) % multiple
    if pad_h == 0 and pad_w == 0:
        return tensor
    # Reflection padding must be smaller than the source side.
    if pad_h >= height or pad_w >= width:
        return F.pad(tensor, (0, pad_w, 0, pad_h), mode="replicate")
    return F.pad(tensor, (0, pad_w, 0, pad_h), mode="reflect")


def enhance_zerodce(bgr: np.ndarray, *, include_intermediates: bool = False) -> tuple[np.ndarray, dict]:
    """Run Zero-DCE++ on CPU and return a BGR uint8 image."""

    from app.config import get_settings

    if bgr.ndim != 3 or bgr.shape[2] != 3:
        raise ValueError("Expected a 3-channel BGR image.")
    status = get_model_status()
    if not status.available:
        raise ModelUnavailable(status.reason)

    import torch

    settings = get_settings()
    original_shape = bgr.shape
    working, resized = _fit_working_size(bgr, settings.max_inference_side)
    network = _load_model()
    rgb = cv2.cvtColor(working, cv2.COLOR_BGR2RGB)
    tensor = torch.from_numpy(np.ascontiguousarray(rgb)).to(dtype=torch.float32).div(255.0)
    tensor = tensor.permute(2, 0, 1).unsqueeze(0)
    padded = _pad_reflect(tensor, settings.zerodce_scale)
    with _lock:
        with torch.inference_mode():
            enhanced, curve = network(padded)
    enhanced = enhanced[:, :, : tensor.shape[-2], : tensor.shape[-1]]
    curve = curve[:, :, : tensor.shape[-2], : tensor.shape[-1]]
    array = enhanced.squeeze(0).permute(1, 2, 0).clamp(0, 1).mul(255.0).to(dtype=torch.uint8).cpu().numpy()
    result = cv2.cvtColor(array, cv2.COLOR_RGB2BGR)
    if resized:
        result = cv2.resize(result, (original_shape[1], original_shape[0]), interpolation=cv2.INTER_CUBIC)

    from app.services.enhance import _luminance, measure_luminance

    intermediates = None
    if include_intermediates:
        curve_map = curve.squeeze(0).mean(dim=0).mul(0.5).add(0.5).clamp(0, 1)
        curve_u8 = curve_map.mul(255.0).to(dtype=torch.uint8).cpu().numpy()
        colored = cv2.applyColorMap(curve_u8, cv2.COLORMAP_TURBO)
        if resized:
            colored = cv2.resize(colored, (original_shape[1], original_shape[0]), interpolation=cv2.INTER_CUBIC)
        intermediates = {"curve_parameters": colored}

    output_y = _luminance(result)
    return result, {
        "gamma": None,
        "stages": ["zerodce_pp"],
        "input": measure_luminance(_luminance(bgr)),
        "output": measure_luminance(output_y),
        "fusion_weights": None,
        "model": {
            "name": "Zero-DCE++",
            "checkpoint": "Epoch99",
            "scale_factor": settings.zerodce_scale,
            "device": "cpu",
            "sha256": status.sha256,
            "paper": PAPER,
            "license": "No license file is published in the upstream Zero-DCE_extension repository.",
            "resized_for_inference": resized,
            "inference_width": int(working.shape[1]),
            "inference_height": int(working.shape[0]),
        },
        "intermediates": intermediates,
    }
