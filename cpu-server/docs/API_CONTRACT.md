# API Contract v1

OpenAPI JSON for all five servers is in `docs/openapi_*.json`.

## Gateway

`POST /v1/frame`

```json
{
  "session_id": "scene-01",
  "frame_index": 17,
  "dt_ms": 16.667,
  "image_png_base64": "<actual PNG in base64>",
  "settings": {
    "OverallStrength": 100,
    "AutoExposureStrength": 30,
    "ExposureOffset": 0,
    "LocalDetail": 20,
    "InputEncoding": 0,
    "OutputEncoding": 0
  }
}
```

Result includes `image_png_base64`, `width`, `height`, `mode`, and (when processed) `observation`, `control`, `tone_validation`. Settings accept source-uniform names, validated against the shader UI ranges. See `docs/openapi_gateway.json` for full schema.

- `GET /health`: gateway health and local/distributed mode.
- `GET /v1/capabilities`: backend, formats and fidelity.
- `GET /v1/sessions/{session_id}`: state snapshot in local mode.
- `DELETE /v1/sessions/{session_id}`: reset in local mode.

## Individual service endpoints

- `POST /v1/observe`: `ObserveRequest` → `Observation` (`histogram` is 64 integers; e50/e90 use source's log2 domain).
- `POST /v1/control/step`: `ControlRequest` → `ControlResult`; **mutates session state**.
- `GET /v1/control/sessions/{session_id}`; `DELETE /v1/control/sessions/{session_id}`.
- `POST /v1/tone/build`: `ToneRequest` → `ToneResult` (`lut` is 1024 floats and validation result).
- `POST /v1/render`: `RenderRequest` → `RenderResult`.

## API safety properties (development only)

PNG is checked for format and an upper bound of 2,000,000 pixels. The request model limits the input base64 field length. Session IDs permit only letters, numbers, hyphen, underscore. All relevant settings are bounded to the UI-provided ranges. The application is not a security boundary: unauthenticated parties could still use or reset sessions if network-accessible.
