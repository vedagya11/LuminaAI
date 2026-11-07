"""Enhancement methods exposed by the API.

Only methods with available=True are executed. Descriptions of unfinished
methods are honest so clients can show them as disabled.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MethodSpec:
    id: str
    name: str
    available: bool
    description: str
    unavailable_reason: str = ""


CLASSICAL = MethodSpec(
    id="classical",
    name="Classical CV",
    available=True,
    description=(
        "Edge-preserving denoise, gray-world color constancy, multi-scale "
        "Retinex illumination correction, CLAHE, and luminance sharpening. "
        "No learned model is used."
    ),
)

DEEP_LEARNING = MethodSpec(
    id="deep_learning",
    name="Deep Learning",
    available=False,
    description="Zero-DCE is planned for a later phase and is not integrated.",
    unavailable_reason=(
        "Deep learning enhancement is not available. Zero-DCE has not been "
        "integrated in this build."
    ),
)

HYBRID = MethodSpec(
    id="hybrid",
    name="Hybrid AI",
    available=False,
    description=(
        "Hybrid classical plus learned enhancement is planned for a later "
        "phase and is not integrated."
    ),
    unavailable_reason=(
        "Hybrid enhancement is not available. No learned model is integrated "
        "in this build."
    ),
)

METHODS: dict[str, MethodSpec] = {
    CLASSICAL.id: CLASSICAL,
    DEEP_LEARNING.id: DEEP_LEARNING,
    HYBRID.id: HYBRID,
}

SUPPORTED_FORMATS = ["jpeg", "jpg", "png", "webp"]
