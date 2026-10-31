# IndusSpine Releases

Public release information and the website download catalog for IndusSpine.

- [Download catalog](downloads.json)
- [v0.3.6 release](https://github.com/Timminater/IndusSpine-Releases/releases/tag/v0.3.6)
- [v0.3.5 release](https://github.com/Timminater/IndusSpine-Releases/releases/tag/v0.3.5)
- [v0.3.4 release](https://github.com/Timminater/IndusSpine-Releases/releases/tag/v0.3.4)
- [Catalog maintenance](docs/catalog-maintenance.md)

The catalog automatically follows published GitHub releases through the [catalog workflow](.github/workflows/sync-download-catalog.yml), with version-specific Dutch and English notes. SHA-256 checksums are available alongside the releases. Existing hand-curated entries are preserved. Automatic entries use GitHub's SHA-256 asset digests and do not claim compiled-source protection or installation approval. Paid licensing and production entitlement activation require separately provisioned signed entitlement/truststore material and validated production endpoints.

The catalog is public display metadata and does not replace the signed distribution and update system.

Version 0.3.6 uses a small Docker download kit. Run its `download.sh` to fetch and verify the parts of the complete compiled installation archive; for an offline PC transfer that complete archive after download. See the release notes and [Docker installation guide](https://www.indusspine.nl/documentation/docker).
