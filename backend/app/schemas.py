"""API response models."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class MethodInfo(BaseModel):
    id: str
    name: str
    available: bool
    description: str


class InfoResponse(BaseModel):
    service: str
    version: str
    supported_formats: list[str]
    max_upload_bytes: int
    max_image_pixels: int
    methods: list[MethodInfo]


class UploadResponse(BaseModel):
    request_id: str
    filename: str
    format: str
    width: int
    height: int
    size_bytes: int


class LuminanceStats(BaseModel):
    mean_luminance: float
    contrast_stddev: float
    noise_sigma: float


class NoReferenceMetrics(BaseModel):
    mean_luminance: float
    contrast_stddev: float
    noise_sigma: float
    saturation_mean: float
    luminance_p5: float
    luminance_p50: float
    luminance_p95: float
    niqe: float | None = None
    niqe_reason: str


class FullReferenceMetrics(BaseModel):
    available: bool
    reason: str
    psnr: float | None = None
    psnr_is_infinite: bool = False
    ssim: float | None = None
    lpips: float | None = None
    lpips_reason: str = ""


class IntermediateImage(BaseModel):
    name: str
    media_type: str
    image_base64: str


class EnhanceResponse(BaseModel):
    request_id: str
    method: str
    available: bool = True
    width: int
    height: int
    input_bytes: int
    output_bytes: int
    processing_time_ms: float | None = None
    media_type: str
    image_base64: str
    gamma: float | None = None
    stages: list[str] = Field(description="Pipeline stages that actually ran on this image.")
    input: LuminanceStats
    output: LuminanceStats
    no_reference: NoReferenceMetrics
    full_reference: FullReferenceMetrics
    fusion_weights: dict | None = None
    model: dict | None = None
    intermediates: list[IntermediateImage] | None = None
    error: str | None = None


class CompareResponse(BaseModel):
    request_id: str
    width: int
    height: int
    original_no_reference: NoReferenceMetrics
    results: list[EnhanceResponse]


class RootResponse(BaseModel):
    service: str
    health: str
    info: str
    docs: str
