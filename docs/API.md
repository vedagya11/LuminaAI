# API

Base path `/api`. Schemas are also at `/docs`.

Errors use `{"detail": "..."}`.

| Code | When |
| --- | --- |
| 400 | Bad type, empty file, corrupt bytes, extension mismatch, image under 8×8, unknown method, reference size mismatch |
| 413 | Upload or pixel count over the configured limit |
| 422 | Missing multipart fields |
| 501 | Method id exists but Zero-DCE++ did not load (`deep_learning`, `hybrid`) |
| 500 | Unexpected processing failure, without a traceback in the body |

## `GET /api/health`

`status`, `service`, `version`.

## `GET /api/info`

Formats, upload limit, pixel limit, and methods. `available` for `deep_learning` and `hybrid` is true only after the weight file and PyTorch both check out. The description text changes with that state. The React cards use this payload.

## `POST /api/upload`

Multipart field `file`. Validates bytes, writes a unique `0600` temp file, decodes with Pillow, deletes the temp file, and returns id, basename, format, dimensions, and size.

## `POST /api/enhance`

Multipart fields:

- `file` (required)
- `method`: `classical`, `deep_learning`, or `hybrid`
- `include_intermediates`: `true` or `false`
- `reference`: optional same-size image

The JSON result includes the JPEG as base64, `processing_time_ms` around the restorer only, input and output luminance statistics, `no_reference` metrics, and `full_reference`. Without `reference`, `full_reference.available` is false and PSNR, SSIM, and LPIPS are null.

`fusion_weights` is present for hybrid. `model` is present when Zero-DCE++ ran. `intermediates` is a list of named JPEGs only when requested. `gamma` is the mean of the classical gamma map, and null for the network-only method.

## `POST /api/compare`

Same file fields except `method`. Returns one entry per method. A method that did not load has `available: false`, `processing_time_ms: null`, an empty image, and `error` set to the loader reason. It does not contain a substitute image.

`original_no_reference` is measured on the upload.
