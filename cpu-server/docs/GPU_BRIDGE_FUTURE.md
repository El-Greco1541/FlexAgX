# GPU/ReShade Bridge — interface proposal only (NOT IMPLEMENTED)

**The current v0.1.0 is a CPU research port, not a live ReShade service.** The original shader has no native HTTP server or component-addressable FX runtime.

A GPU-connected follow-on could choose one of three architectures, subject to Operator review:

1. **Local capture adapter:** an explicitly installed, user-controlled ReShade add-on or frame-capture host extracts framebuffer snapshots and invokes the API as an *analysis/preview side channel*. It must not send frames across untrusted networks. GPU output remains controlled by the original shader.
2. **Embedded compute:** port the observer, controller, LUT and renderer to native GPU compute libraries, expose state and texture handles through a local RPC facade; remove PNG/base64 transport.
3. **Control-plane-only API:** keep ReShade GPU rendering unmodified, and expose only UI settings, profiles, diagnostics and performance logs through a separately authenticated local add-on.

None of these is automatically compatible with the original shader. They require graphic API-specific synchronization, resource sharing, color-space metadata, readback/capture policy, latency accounting, authentication, process isolation, and careful handling of upstream clip/transfer semantics.

**Gate:** No runtime injection, deployment or addon execution without explicit separate Operator clearance. No auto-install or network exposure is implemented.
