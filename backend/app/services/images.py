"""Upload validation, safe temp files, and image decoding."""

from contextlib import contextmanager
from dataclasses import dataclass
import os
from pathlib import Path
import tempfile
from uuid import uuid4

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError
from PIL.Image import DecompressionBombError

from app.config import Settings, get_settings

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
PIL_FORMAT_FOR_EXTENSION = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".webp": "WEBP",
}
FORMAT_NAME = {"JPEG": "jpeg", "PNG": "png", "WEBP": "webp"}


class ImageRejected(Exception):
    """A user-facing rejection with an HTTP status code."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass
class DecodedImage:
    bgr: np.ndarray
    width: int
    height: int
    format: str
    filename: str
    size_bytes: int


def display_name(filename: str | None) -> str:
    raw = filename or "upload"
    base = os.path.basename(raw).replace("\x00", "").strip()
    if base in {"", ".", ".."}:
        return "upload"
    return base[:180]


def extension_of(filename: str | None) -> str:
    return os.path.splitext(display_name(filename))[1].lower()


def read_limited(data: bytes, filename: str | None, settings: Settings) -> tuple[bytes, str, str]:
    """Validate extension and size of an already-buffered upload."""

    name = display_name(filename)
    ext = extension_of(name)
    if ext not in ALLOWED_EXTENSIONS:
        raise ImageRejected(
            "Unsupported file type. Upload a JPG, JPEG, PNG, or WEBP image."
        )
    if not data:
        raise ImageRejected("The uploaded file is empty.")
    if len(data) > settings.max_upload_bytes:
        raise ImageRejected(
            f"File exceeds the {settings.max_upload_bytes} byte upload limit.",
            status_code=413,
        )
    return data, ext, name


@contextmanager
def temporary_upload(data: bytes, extension: str):
    """Write bytes to a uniquely named temp file and always delete it."""

    if extension not in ALLOWED_EXTENSIONS:
        raise ImageRejected("Unsupported file type.")
    settings = get_settings()
    directory = settings.temp_dir
    os.makedirs(directory, mode=0o700, exist_ok=True)
    fd, path = tempfile.mkstemp(
        prefix=f"lumina_{uuid4().hex}_",
        suffix=extension,
        dir=directory,
    )
    try:
        os.fchmod(fd, 0o600)
        os.write(fd, data)
    finally:
        os.close(fd)
    try:
        yield path
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def decode_image(path: str, extension: str, filename: str, size_bytes: int, settings: Settings) -> DecodedImage:
    """Decode a still image with Pillow, then hand OpenCV a BGR array.

    Pillow is the content check: extension, declared format, and pixel data
    must all agree. EXIF orientation is applied so phone photos are upright.
    """

    expected = PIL_FORMAT_FOR_EXTENSION[extension]
    Image.MAX_IMAGE_PIXELS = settings.max_image_pixels
    try:
        with Image.open(path) as image:
            image.load()
            pil_format = image.format or ""
            if pil_format == "MPO" and expected == "JPEG":
                pil_format = "JPEG"
            if pil_format not in FORMAT_NAME:
                raise ImageRejected(
                    f"Unsupported image content ({pil_format or 'unknown'}). "
                    "Upload a JPG, JPEG, PNG, or WEBP still image."
                )
            if pil_format != expected:
                raise ImageRejected(
                    f"File content is {pil_format}, which does not match the "
                    f"{extension} extension."
                )
            frames = getattr(image, "n_frames", 1) or 1
            if frames > 1:
                raise ImageRejected(
                    "Animated images are not supported. Upload a single still frame."
                )
            oriented = ImageOps.exif_transpose(image)
            if oriented.mode == "RGBA":
                background = Image.new("RGB", oriented.size, (0, 0, 0))
                background.paste(oriented, mask=oriented.getchannel("A"))
                rgb_image = background
            elif oriented.mode != "RGB":
                rgb_image = oriented.convert("RGB")
            else:
                rgb_image = oriented
            rgb = np.asarray(rgb_image, dtype=np.uint8).copy()
    except ImageRejected:
        raise
    except DecompressionBombError as exc:
        raise ImageRejected(
            "Image dimensions exceed the configured pixel limit.",
            status_code=413,
        ) from exc
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ImageRejected("The file is corrupted or is not a readable image.") from exc

    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ImageRejected("The image must contain three color channels.")
    height, width = rgb.shape[:2]
    if width < 8 or height < 8:
        raise ImageRejected("Image is too small. The minimum size is 8 by 8 pixels.")
    if width * height > settings.max_image_pixels:
        raise ImageRejected(
            "Image dimensions exceed the configured pixel limit.",
            status_code=413,
        )

    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    return DecodedImage(
        bgr=bgr,
        width=width,
        height=height,
        format=FORMAT_NAME[expected],
        filename=filename,
        size_bytes=size_bytes,
    )


def leftover_temp_files(directory: str | None = None) -> list[Path]:
    folder = Path(directory or get_settings().temp_dir)
    if not folder.exists():
        return []
    return [path for path in folder.iterdir() if path.name.startswith("lumina_")]
