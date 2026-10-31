# Catalog automation validation — 2026-10-31

## Accepted automatic release-to-website proof

The newly published [Windows R12 test candidate](https://github.com/Timminater/IndusSpine-Releases/releases/tag/v0.3.6-windows-candidate.12.20261031)
triggered the workflow through the actual `release` event, without a manual
dispatch. [Run 41201573892](https://github.com/Timminater/IndusSpine-Releases/actions/runs/41201573892)
passed, including all 19 tests, and the repository-scoped bot pushed
[`7cb27b8a5c56b5ec434375a750da2bc408c3437b`](https://github.com/Timminater/IndusSpine-Releases/commit/7cb27b8a5c56b5ec434375a750da2bc408c3437b).
That commit adds the release and its five hashed assets to `downloads.json`,
creates both changelogs, and records the managed version. The workflow ran
from 12:32:40Z to 12:32:47Z after publication at 12:32:35Z.

At 12:37:24Z the production [public API](https://www.indusspine.nl/api/downloads/v1/releases)
returned HTTP 200, `status=available`, five releases and stable `latest=0.3.6`.
The R12 preview exposed all five download links with the expected sizes and
SHA-256 values; anonymous HEAD requests to all five returned HTTP 200. The
[version page](https://www.indusspine.nl/downloads/0.3.6-windows-candidate.12.20261031)
and [release notes](https://www.indusspine.nl/downloads/releasenotes/0.3.6-windows-candidate.12.20261031)
returned HTTP 200. Dutch notes contained `Windows-testversie R12`; after the
ordinary public locale form switched a temporary session, English notes
rendered with `html lang=en` and `Windows test candidate R12`.

No manual `downloads.json` edit, website source change, website deployment,
signed updater-feed operation or app build via Actions was performed. These
are API/HTML/link checks; no visual browser acceptance is claimed. The existing
website catalog cache can take a few minutes to expose a newly synchronized
release. Stable remains latest and the older rejected R8 tag/assets are
unchanged. Windows EXEs were built and tested locally; this workflow only
synchronizes catalog metadata and release notes.

## Earlier manual-dispatch checkpoint

Implementation commit: `c170bcc7a90c9ff7880d23805b57971d037ec5f5`.

- The 19 synchronization tests passed locally and in the actual GitHub-hosted job. They cover discovery of stable/pre-release versions, asset hashes, bilingual notes, deletion, later uploads, idempotence, limits, invalid metadata and preservation of reviewed records.
- [Workflow run 41186094746](https://github.com/Timminater/IndusSpine-Releases/actions/runs/41186094746) completed successfully. The repository-scoped bot pushed commit `a32449da78eac5d6717aadb8283a3c734964ee35`, creating the automation state without changing the four existing reviewed catalog records.
- The production [public API](https://www.indusspine.nl/api/downloads/v1/releases) returned `status=available`, four releases and `latest=0.3.6`. It included the separately labelled rejected R8 preview. Website source and deployment were not changed for this automation.
- The existing R8 preview was labelled more explicitly as rejected on GitHub. Its historical tag predates the workflow; that edit did not start an Actions job. New tags must target the current `main`. Existing tags remain immutable. The hourly reconciliation and manual dispatch cover this case.

At this checkpoint, publication of a newly tagged release through the automatic `published` event has not yet been used as an end-to-end acceptance proof. The successful real job was explicitly dispatched; new-release discovery was verified with synthetic metadata in the tests. Do not describe that checkpoint as proof of a new automatic public release.

GitHub documents the release event's tag ref and commit in [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#release). No EXE build, artifact publication, website deployment or signed update-feed operation is part of this workflow.
