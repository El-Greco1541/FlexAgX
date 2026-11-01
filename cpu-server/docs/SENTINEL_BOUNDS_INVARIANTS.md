# Sentinel, Initialization, Bound and Fallback Policy

The staged application and its harness must never emit JSON `null`, `NaN`, `Infinity` or `-Infinity`. Negative input and malicious raw JSON may contain these tokens intentionally as fuzz fixtures: rejection is the expected behavior. API metadata uses typed sentinel objects (`kind`, `reason`, `fallback`) instead of nullable result fields.

The controller's 11 persistent `State` fields use declared defaults and a state-lifecycle marker. Numeric parameters are constrained by Pydantic schemas before endpoint processing. The harness validates all result artifacts recursively for JSON-domain finiteness, null exclusion, maximum nesting, and phase/accounting consistency. Native-library and kernel termination are outside static proof scope.

The test harness's retry/timeout/failure paths return structured status (`PASS` or `FAIL`), explicit failure reasons, or a sentinel for genuinely inapplicable attributes. They cannot turn a missing evidence file into a successful phase. All child-process watchdogs and output budgets are bounded.
