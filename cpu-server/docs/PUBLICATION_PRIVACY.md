# Publication and privacy audit

This publicly visible **research/staging** branch contains no intentionally included contributor personal profiles, private workstation paths, machine hostnames, account IDs, tokens, credentials, private addresses, live session IDs, or raw log bundles.

- The technical work is attributed to an independent CPU-server research adaptation, not named participants.
- **Required attribution is preserved:** the original upstream shader by El-Greco1541 and its MIT license remain intact, including upstream license notices and public origin links.
- GitHub's repository owner, fork relationship and commit author/committer information are public service metadata. This source-content audit cannot hide that information or promise anonymous GitHub activity.
- The included test evidence has synthetic IDs and historical bounded test metrics. No authenticated service traffic or customer data is included.
- Static privacy checks are best-effort; do not treat this as a formal privacy certification or vulnerability audit.
- No authentication, secrets, or live deployment configuration is included. Development API must remain loopback-only.

## Handling rules

Before additional public commits, scan added assets for secrets, local paths, identifying names, GPS/network addresses other than localhost, crash dumps, cookies, API request recordings, and real user data. Never commit `.env`, `.venv`, `__pycache__`, `.pytest_cache`, or runtime test outputs generated from real sessions.

## v0.5.0 note

The transaction journal stores complete image-result receipts locally. Do not publish SQLite databases, cached real-session frames, connection credentials or crash dumps. Test packages use synthetic images and ephemeral temporary SQLite files, and no database is committed. GitHub metadata and original MIT attribution remain public.
