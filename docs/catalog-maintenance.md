# Download catalog maintenance

`downloads.json` is public display metadata, not the signed distribution/update feed or an authorization source. Website downloads resolve the exact asset in the published GitHub release for the matching tag. Do not put URLs, private application source, credentials, keys or binaries in this repository. Release notes use Markdown. The website strips raw HTML and disallows unsafe links when rendering them.

## Automatic publication

The `Synchronize download catalog` GitHub Actions workflow updates the catalog on release publication, editing, deletion or unpublication. It can also be dispatched manually. An hourly reconciliation covers missed token-generated events and assets uploaded after publication. The workflow only tests and updates public catalog metadata; it never builds or starts an executable, publishes software artifacts, changes the website, or signs an update feed.

Publish a release with a `vX.Y.Z` tag for stable or a hyphenated SemVer tag (for example `v0.3.7-rc.1`) marked **pre-release**. Prefer uploading all assets to a draft and publishing it afterwards. The workflow keeps `latest` on the highest stable version. A preview never replaces stable/latest. The website's existing cache can delay visibility by several minutes.

Supported uploaded assets with GitHub SHA-256 digests are classified by extension and filename. Missing digests are reported and those assets are omitted rather than given invented hashes. Split archive parts are omitted; publish a download kit for their reconstruction. `all` means no platform or architecture was specified in the filename, not verified compatibility. New entries do not receive a `compiled_protection` assertion. Limits mirror the website: 20 releases, 50 listed downloads per release, 100 GitHub assets per tag, and version strings at most 64 characters. Unsupported tags are reported and ignored; incompatible prerelease flags fail the run before publication.

Existing reviewed records and hand-written NL/EN changelogs remain intact. A changed SHA-256 for a reviewed asset fails synchronization and needs explicit review; publish immutable versioned assets. Newly discovered versions are tracked in `.github/catalog-sync-state.json`, and their generated notes follow later release edits. For authored bilingual notes, put `<!-- nl -->` before Dutch text and `<!-- en -->` before English text in the GitHub release body. Otherwise each generated language page clearly labels the release body's original, untranslated language. Do not manually edit generated notes: edit the GitHub release instead.

To test locally without network access:

```sh
python3 -m unittest discover -s tests -v
```

To inspect a synchronization without changing files:

```sh
GH_TOKEN=... python3 scripts/sync_catalog.py --check
```

The workflow uses the repository-scoped `GITHUB_TOKEN` with `contents: write`, a serialized concurrency group, and a checkout pinned to a full commit. Release bodies and tags are data, never shell code. There is no PAT or website credential to configure. If the default branch is protected against bot pushes, the workflow fails; it does not bypass branch protections or force-push.

## Manual review and exceptions

For manual overrides or reviewed compilation/protection assertions:

1. Independently verify that the release tag, artifact version and trusted compiled build manifest match. Audit the actual published payload and any embedded image layers and driver bundles for protected Python core and proprietary driver source. Check the contents of Python files: short loader shims, the driver SDK and third-party dependencies have different purposes from protected implementation source. A regular unencrypted tar archive is acceptable; an archive header alone proves neither protection nor leakage.
2. Check the asset names, architecture, sizes and hashes from the published release and compare downloaded bytes against its SHA-256 list. Only add an artifact when its version and protection review are complete. Do not infer an image's protection from an archive that merely refers to it.
3. Add the version and tag, publish time, channel, bilingual release notes and reviewed asset entries to `downloads.json`. Omit unreviewed files; an empty `downloads` array is allowed. Write notes from actual release evidence. The optional `compiled_protection` field is a publisher statement, not cryptographic proof.
4. Validate JSON and release links locally and request review of the resulting public metadata before publication. Publishing a catalog entry does not change or replace existing signed update admission.

The initial v0.3.5 package contains an image and drivers audited from downloaded assets; v0.3.4 drivers were audited separately, while its package references a registry image whose contents have not been reviewed for this catalog. The v0.3.4 installation package is therefore omitted pending that review. SHA-256 lists can include files absent from the catalog.

The root has `schema`, `repository`, `latest`, and `releases`; each release has `version`, `tag`, `published_at`, `channel`, `changelog` (`nl` and `en` paths), and `downloads`. Each download has a slug `id`, exact `asset` name, `kind`, `platform`, `architecture`, localized `label`, and lowercase `sha256`; `compiled_protection` is optional. See the actual catalog for examples.
