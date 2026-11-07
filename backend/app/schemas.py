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


class EnhanceResponse(BaseModel):
    request_id: str
    method: str
    width: int
    height: int
    input_bytes: int
    output_bytes: int
    processing_time_ms: float
    media_type: str
    image_base64: str
    gamma: float
    stages: list[str] = Field(description="Pipeline stages that actually ran on this image.")
    input: LuminanceStats
    output: LuminanceStats


class RootResponse(BaseModel):
    service: str
    health: str
    info: str
    docs: str
