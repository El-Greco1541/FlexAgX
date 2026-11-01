# Staging and handoff

- Location: `cpu-server/` in the designated public GitHub fork.
- Base material: CPU API/microservices v0.3.0, hardened harness v0.4.0, plus staged transaction-integrity revision v0.5.0.
- Original shader: ReShade FX 1.2, byte-identical to upstream release.
- Intended use: local experimentation, source audit, independent CPU tests and microservice orchestration.
- Prohibited inference: passing CPU tests do not constitute GPU parity, ReShade compiler compatibility, a security review, or production approval.
- Known gap: frame-index replay/idempotency and durable multi-service commit recovery.
- Guardrail: reviewable staging branch only. No implicit merge, deploy or release.
- UI/diagnostics: `GET /health`, `GET /v1/capabilities`, Swagger at `/docs`.

## Acceptance checklist

- [x] Preserve root README and MIT LICENSE without modifications
- [x] Isolate all CPU source and tests under `cpu-server/`
- [x] Preserve byte-identical original shader reference
- [x] Include standalone server README and API docs
- [x] Include no-null sentinel and bounded fallback policy
- [x] Include hardened adversarial and torture harness
- [x] Prior staging commit and GitHub tree verified; v0.5 commit requires its own verification
- [ ] Independent platform-specific run and dependency scan
- [ ] Operator clearance for any production release
