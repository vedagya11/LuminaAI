# API

Base path: `/api`. Interactive schemas are served at `/docs` when the backend is running.

All errors use `{"detail": "..."}` and a specific status code.

| Code | When |
| --- | --- |
| 400 | Unsupported type, empty file, corrupt bytes, extension/content mismatch, image under 8×8, unknown method |
| 413 | Upload larger than `MAX_UPLOAD_BYTES`, or pixel count above `MAX_IMAGE_PIXELS` |
| 422 | Missing multipart fields |
| 501 | Method exists but is not integrated (`deep_learning`, `hybrid`) |
| 500 | Unexpected processing failure. The body does not include a traceback |

## `GET /api/health`

```json
{"status": "ok", "service": "LUMINA AI", "version": "1.0.0"}
```

## `GET /api/info`

Returns supported formats (`jpeg`, `jpg`, `png`, `webp`), the active upload and pixel limits, and every method. `available` is true only for Classical CV in this phase. The React app enables radios from this payload.

## `POST /api/upload`

Multipart field: `file`.

The handler reads the body in 1 MiB chunks, stops past the size limit, checks the extension, writes a `lumina_<uuid>` file mode `0600` under the temp directory, and decodes it with Pillow (`load()`, EXIF transpose, still-frame check). The temp file is deleted before the response. Nothing is kept on disk.

```json
{
  "request_id": "uuid",
  "filename": "night.png",
  "format": "png",
  "width": 160,
  "height": 120,
  "size_bytes": 8421
}
```

`filename` is the basename only.

## `POST /api/enhance`

Multipart fields: `file`, `method`.

`method` must be an id from `/api/info`. Classical CV runs the pipeline in `docs/PIPELINE.md` and returns a JPEG (quality from `JPEG_QUALITY`, default 92) plus measurements.

```json
{
  "request_id": "uuid",
  "method": "classical",
  "width": 160,
  "height": 120,
  "input_bytes": 8421,
  "output_bytes": 12004,
  "processing_time_ms": 37.41,
  "media_type": "image/jpeg",
  "image_base64": "...",
  "gamma": 0.61,
  "stages": ["multiscale_retinex", "clahe", "luminance_unsharp", "highlight_rolloff"],
  "input": {"mean_luminance": 21.4, "contrast_stddev": 8.2, "noise_sigma": 1.1},
  "output": {"mean_luminance": 96.7, "contrast_stddev": 28.4, "noise_sigma": 2.4}
}
```

Upload and enhance each generate their own request id. Enhance does not look up a previous upload; send the image again. The browser does both calls so a corrupt file fails before the longer pipeline runs.

Alpha is composited onto black. Animated WebP and GIF are rejected.
