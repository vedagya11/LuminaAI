"""HTTP API for validation and classical low-light enhancement."""

import base64
from logging import getLogger
import time
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import get_settings
from app.schemas import (
    EnhanceResponse,
    HealthResponse,
    InfoResponse,
    LuminanceStats,
    MethodInfo,
    UploadResponse,
)
from app.services.enhance import encode_jpeg, enhance_classical
from app.services.images import ImageRejected, decode_image, read_limited, temporary_upload
from app.services.methods import METHODS, SUPPORTED_FORMATS

logger = getLogger("lumina.api")
router = APIRouter()


async def _buffer_upload(upload: UploadFile) -> bytes:
    settings = get_settings()
    payload = bytearray()
    while True:
        chunk = await upload.read(1024 * 1024)
        if not chunk:
            break
        if len(payload) + len(chunk) > settings.max_upload_bytes:
            raise ImageRejected(
                f"File exceeds the {settings.max_upload_bytes} byte upload limit.",
                status_code=413,
            )
        payload.extend(chunk)
    return bytes(payload)


def _ingest(upload_name: str | None, payload: bytes):
    settings = get_settings()
    data, extension, name = read_limited(payload, upload_name, settings)
    with temporary_upload(data, extension) as path:
        return decode_image(path, extension, name, len(data), settings)


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", service=settings.app_name, version=settings.version)


@router.get("/info", response_model=InfoResponse)
def info() -> InfoResponse:
    settings = get_settings()
    methods = [
        MethodInfo(
            id=spec.id,
            name=spec.name,
            available=spec.available,
            description=spec.description,
        )
        for spec in METHODS.values()
    ]
    return InfoResponse(
        service=settings.app_name,
        version=settings.version,
        supported_formats=SUPPORTED_FORMATS,
        max_upload_bytes=settings.max_upload_bytes,
        max_image_pixels=settings.max_image_pixels,
        methods=methods,
    )


@router.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)) -> UploadResponse:
    try:
        payload = await _buffer_upload(file)
        decoded = _ingest(file.filename, payload)
    except ImageRejected as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return UploadResponse(
        request_id=str(uuid4()),
        filename=decoded.filename,
        format=decoded.format,
        width=decoded.width,
        height=decoded.height,
        size_bytes=decoded.size_bytes,
    )


@router.post("/enhance", response_model=EnhanceResponse)
async def enhance(
    file: UploadFile = File(...),
    method: str = Form(...),
) -> EnhanceResponse:
    method_id = method.strip().lower()
    spec = METHODS.get(method_id)
    if spec is None:
        raise HTTPException(
            status_code=400,
            detail="Unknown enhancement method. Use a method id returned by /api/info.",
        )
    if not spec.available:
        raise HTTPException(status_code=501, detail=spec.unavailable_reason)

    settings = get_settings()
    try:
        payload = await _buffer_upload(file)
        decoded = _ingest(file.filename, payload)
        started = time.perf_counter()
        enhanced, meta = enhance_classical(decoded.bgr)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        encoded = encode_jpeg(enhanced, settings.jpeg_quality)
    except ImageRejected as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Enhancement failed for method %s", method_id)
        raise HTTPException(status_code=500, detail="Image enhancement failed.") from exc

    height, width = enhanced.shape[:2]
    return EnhanceResponse(
        request_id=str(uuid4()),
        method=method_id,
        width=width,
        height=height,
        input_bytes=decoded.size_bytes,
        output_bytes=len(encoded),
        processing_time_ms=round(elapsed_ms, 2),
        media_type="image/jpeg",
        image_base64=base64.b64encode(encoded).decode("ascii"),
        gamma=meta["gamma"],
        stages=meta["stages"],
        input=LuminanceStats(**meta["input"]),
        output=LuminanceStats(**meta["output"]),
    )
