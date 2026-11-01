# Short fallback matrix

- **IDENTITY:** Bypass returns original encoded framebuffer, explicit not-applicable sentinels.
- **REJECT:** Input/domain/limit and internal unexpected failure. Never publish an unchecked frame or silently zero invalid values.
- **RETRY_EXPLICIT:** Only caller-controlled retries; no automatic resubmission of an uncertain distributed commit.
- **HOLD:** Persistent state remains as-is when a frame is aborted. Existing exposure freeze remains a separate user control.
- **SKIP:** Non-applicable test metadata uses a documented typed sentinel, not null.

The fallback of last resort is **bounded rejection**, not fabrication of a successful processed image.
