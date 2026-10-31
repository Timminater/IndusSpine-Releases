# Catalog automation validation — 2026-10-31

Implementation commit: `c170bcc7a90c9ff7880d23805b57971d037ec5f5`.

- The 19 synchronization tests passed locally and in the actual GitHub-hosted job. They cover discovery of stable/pre-release versions, asset hashes, bilingual notes, deletion, later uploads, idempotence, limits, invalid metadata and preservation of reviewed records.
- [Workflow run 41186094746](https://github.com/Timminater/IndusSpine-Releases/actions/runs/41186094746) completed successfully. The repository-scoped bot pushed commit `a32449da78eac5d6717aadb8283a3c734964ee35`, creating the automation state without changing the four existing reviewed catalog records.
- The production [public API](https://www.indusspine.nl/api/downloads/v1/releases) returned `status=available`, four releases and `latest=0.3.6`. It included the separately labelled rejected R8 preview. Website source and deployment were not changed for this automation.
- The existing R8 preview was labelled more explicitly as rejected on GitHub. Its historical tag predates the workflow; that edit did not start an Actions job. New tags must target the current `main`. Existing tags remain immutable. The hourly reconciliation and manual dispatch cover this case.

At this checkpoint, publication of a newly tagged release through the automatic `published` event has not yet been used as an end-to-end acceptance proof. The successful real job was explicitly dispatched; new-release discovery was verified with synthetic metadata in the tests. Do not describe that checkpoint as proof of a new automatic public release.

GitHub documents the release event's tag ref and commit in [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#release). No EXE build, artifact publication, website deployment or signed update-feed operation is part of this workflow.
