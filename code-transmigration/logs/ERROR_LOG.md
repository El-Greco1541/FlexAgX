# Error and limitation register

| ID | Type | Status | Mitigation / scope |
|---|---|---|---|
| CT-01 | Port equivalence | OPEN | CPU frame rendering grouped; eight FX pass mapping is descriptive not isolated pass parity |
| CT-02 | Shader GPU parity | OPEN | Requires FX compilation, backend measurements and numerical tolerance choices |
| CT-03 | Core dependency | BOUNDED | Depends on sibling cpu-server/ v0.5.0; startup fails if it is unavailable |
| CT-04 | State correctness | TESTED (LOCAL) | SQLite transactional receipts/replay via existing SessionStore; no multi-node guarantees |
| CT-05 | API security | OPEN | Local-only; no authentication or hardened external transport |
| CT-06 | Legacy endpoint bypass | CONTAINED | New facade exports no direct unsequenced controller mutation endpoints |
| CT-07 | Native numerical bounds | OPEN | Native code termination proof and resource quotas not established |
