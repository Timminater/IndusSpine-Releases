# Download catalog maintenance

`downloads.json` is public display metadata, not the signed distribution/update feed or an authorization source. Website downloads resolve the exact asset in the published GitHub release for the matching tag. Do not put URLs, private application source, credentials, keys or binaries in this repository. Release notes use Markdown. The website strips raw HTML and disallows unsafe links when rendering them. There is no GitHub Actions publication workflow.

For each new release:

1. Independently verify that the release tag, artifact version and trusted compiled build manifest match. Audit the actual published payload and any embedded image layers and driver bundles for protected Python core and proprietary driver source. Check the contents of Python files: short loader shims, the driver SDK and third-party dependencies have different purposes from protected implementation source. A regular unencrypted tar archive is acceptable; an archive header alone proves neither protection nor leakage.
2. Check the asset names, architecture, sizes and hashes from the published release and compare downloaded bytes against its SHA-256 list. Only add an artifact when its version and protection review are complete. Do not infer an image's protection from an archive that merely refers to it.
3. Add the version and tag, publish time, channel, bilingual release notes and reviewed asset entries to `downloads.json`. Omit unreviewed files; an empty `downloads` array is allowed. Write notes from actual release evidence. The optional `compiled_protection` field is a publisher statement, not cryptographic proof.
4. Validate JSON and release links locally and request review of the resulting public metadata before publication. Publishing a catalog entry does not change or replace existing signed update admission.

The initial v0.3.5 package contains an image and drivers audited from downloaded assets; v0.3.4 drivers were audited separately, while its package references a registry image whose contents have not been reviewed for this catalog. The v0.3.4 installation package is therefore omitted pending that review. SHA-256 lists can include files absent from the catalog.

The root has `schema`, `repository`, `latest`, and `releases`; each release has `version`, `tag`, `published_at`, `channel`, `changelog` (`nl` and `en` paths), and `downloads`. Each download has a slug `id`, exact `asset` name, `kind`, `platform`, `architecture`, localized `label`, and lowercase `sha256`; `compiled_protection` is optional. See the actual catalog for examples.
