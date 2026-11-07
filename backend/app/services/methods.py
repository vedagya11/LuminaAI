"""Enhancement methods exposed by the API.

Availability of the learned methods follows a successful Zero-DCE++ weight
check. Descriptions stay explicit when the checkpoint or PyTorch is missing.
"""

from dataclasses import dataclass

from app.services.zerodce import get_model_status


@dataclass(frozen=True)
class MethodSpec:
    id: str
    name: str
    available: bool
    description: str
    unavailable_reason: str = ""


CLASSICAL_DESCRIPTION = (
    "Luminance-weighted gray-world balance, noise-adaptive bilateral filtering, "
    "multi-scale Retinex with a per-pixel gamma, CLAHE, and highlight protection."
)

LEARNED_DESCRIPTION = (
    "Zero-DCE++ (Epoch99) estimates per-channel light-enhancement curves with "
    "a pretrained PyTorch network and applies them iteratively. CPU inference."
)

HYBRID_DESCRIPTION = (
    "Spatially adaptive fusion of Classical CV and Zero-DCE++. Dark clean "
    "regions take more of the network output; noise and existing highlights "
    "take more of the classical output. Fusion weights are measured, not fixed."
)


def method_catalog() -> dict[str, MethodSpec]:
    status = get_model_status()
    learned_reason = status.reason or "Zero-DCE++ is unavailable."
    hybrid_reason = (
        status.reason
        or "Hybrid enhancement is unavailable because Zero-DCE++ did not load."
    )
    return {
        "classical": MethodSpec(
            id="classical",
            name="Classical CV",
            available=True,
            description=CLASSICAL_DESCRIPTION,
        ),
        "deep_learning": MethodSpec(
            id="deep_learning",
            name="Deep Learning",
            available=status.available,
            description=LEARNED_DESCRIPTION if status.available else f"{LEARNED_DESCRIPTION} {learned_reason}",
            unavailable_reason="" if status.available else learned_reason,
        ),
        "hybrid": MethodSpec(
            id="hybrid",
            name="Hybrid AI",
            available=status.available,
            description=HYBRID_DESCRIPTION if status.available else f"{HYBRID_DESCRIPTION} {hybrid_reason}",
            unavailable_reason="" if status.available else hybrid_reason,
        ),
    }


SUPPORTED_FORMATS = ["jpeg", "jpg", "png", "webp"]
