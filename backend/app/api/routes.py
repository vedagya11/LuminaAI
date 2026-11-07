"""HTTP API for validation, restoration, comparison, and measured metrics."""

import base64
from logging import getLogger
import time
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import get_settings
from app.schemas import (
    CompareResponse,
    EnhanceResponse,
    FullReferenceMetrics,
    HealthResponse,
    InfoResponse,
    IntermediateImage,
    LuminanceStats,
    MethodInfo,
    NoReferenceMetrics,
    UploadResponse,
)
from app.services.enhance import encode_jpeg, enhance_classical
from app.services.hybrid import enhance_hybrid
from app.services.images import ImageRejected, decode_image, read_limited, temporary_upload
from app.services.methods import SUPPORTED_FORMATS, method_catalog
from app.services.metrics import full_reference, no_reference
from app.services.zerodce import ModelUnavailable, enhance_zerodce

logger = getLogger("lumina.api")
router = APIRouter()

RUNNERS = {
    "classical": enhance_classical,
    "deep_learning": enhance_zerodce,
    "hybrid": enhance_hybrid,
}


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


def _encode_intermediates(images: dict | None, quality: int) -> list[IntermediateImage] | None:
    if not images:
        return None
    encoded = []
    for name, image in images.items():
        payload = encode_jpeg(image, quality)
        encoded.append(
            IntermediateImage(
                name=name,
                media_type="image/jpeg",
                image_base64=base64.b64encode(payload).decode("ascii"),
            )
        )
    return encoded


def _run(method_id: str, decoded, reference_bgr, include_intermediates: bool) -> EnhanceResponse:
    settings = get_settings()
    spec = method_catalog()[method_id]
    request_id = str(uuid4())
    if not spec.available:
        raise ModelUnavailable(spec.unavailable_reason)
    started = time.perf_counter()
    enhanced, meta = RUNNERS[method_id](decoded.bgr, include_intermediates=include_intermediates)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    encoded = encode_jpeg(enhanced, settings.jpeg_quality)
    height, width = enhanced.shape[:2]
    measured = no_reference(enhanced)
    reference_metrics = full_reference(reference_bgr, enhanced)
    logger.info(
        "enhanced method=%s time_ms=%.2f width=%s height=%s",
        method_id,
        elapsed_ms,
        width,
        height,
    )
    return EnhanceResponse(
        request_id=request_id,
        method=method_id,
        available=True,
        width=width,
        height=height,
        input_bytes=decoded.size_bytes,
        output_bytes=len(encoded),
        processing_time_ms=round(elapsed_ms, 2),
        media_type="image/jpeg",
        image_base64=base64.b64encode(encoded).decode("ascii"),
        gamma=meta.get("gamma"),
        stages=meta.get("stages") or [],
        input=LuminanceStats(**meta["input"]),
        output=LuminanceStats(**meta["output"]),
        no_reference=NoReferenceMetrics(**measured),
        full_reference=FullReferenceMetrics(**reference_metrics),
        fusion_weights=meta.get("fusion_weights"),
        model=meta.get("model"),
        intermediates=_encode_intermediates(meta.get("intermediates"), settings.jpeg_quality),
    )


async def _optional_reference(reference: UploadFile | None):
    if reference is None or not reference.filename:
        return None
    payload = await _buffer_upload(reference)
    if not payload:
        return None
    return _ingest(reference.filename, payload)


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
        for spec in method_catalog().values()
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
    include_intermediates: bool = Form(False),
    reference: UploadFile | None = File(None),
) -> EnhanceResponse:
    method_id = method.strip().lower()
    catalog = method_catalog()
    spec = catalog.get(method_id)
    if spec is None:
        raise HTTPException(
            status_code=400,
            detail="Unknown enhancement method. Use a method id returned by /api/info.",
        )
    if not spec.available:
        raise HTTPException(status_code=501, detail=spec.unavailable_reason)
    try:
        payload = await _buffer_upload(file)
        decoded = _ingest(file.filename, payload)
        reference_image = await _optional_reference(reference)
        reference_bgr = None if reference_image is None else reference_image.bgr
        if reference_bgr is not None and reference_bgr.shape[:2] != decoded.bgr.shape[:2]:
            raise ImageRejected("The reference image must have the same dimensions as the upload.")
        return _run(method_id, decoded, reference_bgr, include_intermediates)
    except ImageRejected as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except ModelUnavailable as exc:
        raise HTTPException(status_code=501, detail=exc.message) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Enhancement failed for method %s", method_id)
        raise HTTPException(status_code=500, detail="Image enhancement failed.") from exc


@router.post("/compare", response_model=CompareResponse)
async def compare(
    file: UploadFile = File(...),
    include_intermediates: bool = Form(False),
    reference: UploadFile | None = File(None),
) -> CompareResponse:
    try:
        payload = await _buffer_upload(file)
        decoded = _ingest(file.filename, payload)
        reference_image = await _optional_reference(reference)
        reference_bgr = None if reference_image is None else reference_image.bgr
        if reference_bgr is not None and reference_bgr.shape[:2] != decoded.bgr.shape[:2]:
            raise ImageRejected("The reference image must have the same dimensions as the upload.")
    except ImageRejected as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    results: list[EnhanceResponse] = []
    for spec in method_catalog().values():
        if not spec.available:
            results.append(
                EnhanceResponse(
                    request_id=str(uuid4()),
                    method=spec.id,
                    available=False,
                    width=decoded.width,
                    height=decoded.height,
                    input_bytes=decoded.size_bytes,
                    output_bytes=0,
                    processing_time_ms=None,
                    media_type="image/jpeg",
                    image_base64="",
                    stages=[],
                    input=LuminanceStats(**no_reference_luma(decoded.bgr)),
                    output=LuminanceStats(**no_reference_luma(decoded.bgr)),
                    no_reference=NoReferenceMetrics(**no_reference(decoded.bgr)),
                    full_reference=FullReferenceMetrics(
                        available=False,
                        reason=spec.unavailable_reason,
                    ),
                    error=spec.unavailable_reason,
                )
            )
            continue
        try:
            results.append(_run(spec.id, decoded, reference_bgr, include_intermediates))
        except (ImageRejected, ModelUnavailable, ValueError) as exc:
            message = getattr(exc, "message", str(exc))
            results.append(_failed_result(spec.id, decoded, message))
        except Exception:
            logger.exception("Compare failed for method %s", spec.id)
            results.append(_failed_result(spec.id, decoded, "Image enhancement failed."))
    return CompareResponse(
        request_id=str(uuid4()),
        width=decoded.width,
        height=decoded.height,
        original_no_reference=NoReferenceMetrics(**no_reference(decoded.bgr)),
        results=results,
    )


def no_reference_luma(bgr) -> dict:
    measured = no_reference(bgr)
    return {
        "mean_luminance": measured["mean_luminance"],
        "contrast_stddev": measured["contrast_stddev"],
        "noise_sigma": measured["noise_sigma"],
    }


def _failed_result(method_id: str, decoded, message: str) -> EnhanceResponse:
    measured = no_reference(decoded.bgr)
    luma = no_reference_luma(decoded.bgr)
    return EnhanceResponse(
        request_id=str(uuid4()),
        method=method_id,
        available=False,
        width=decoded.width,
        height=decoded.height,
        input_bytes=decoded.size_bytes,
        output_bytes=0,
        processing_time_ms=None,
        media_type="image/jpeg",
        image_base64="",
        stages=[],
        input=LuminanceStats(**luma),
        output=LuminanceStats(**luma),
        no_reference=NoReferenceMetrics(**measured),
        full_reference=FullReferenceMetrics(available=False, reason=message),
        error=message,
    )
