from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "sync_catalog.py"
SPEC = importlib.util.spec_from_file_location("sync_catalog", SOURCE)
sync = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync)


def asset(name="IndusSpine-0.3.7-Setup.exe", *, tag="v0.3.7", sha="a" * 64):
    return {"name": name, "state": "uploaded", "size": 1234,
            "browser_download_url": f"{sync.DOWNLOAD}/{tag}/{name}", "digest": f"sha256:{sha}"}


def release(version="0.3.7", *, assets=None, body="Release notes", published="2026-10-31T12:00:00Z"):
    return {"tag_name": f"v{version}", "name": f"IndusSpine {version}", "draft": False,
            "prerelease": "-" in version, "published_at": published, "body": body,
            "assets": [asset(tag=f"v{version}")] if assets is None else assets}


class CatalogTests(unittest.TestCase):
    def setUp(self):
        output = contextlib.redirect_stdout(io.StringIO())
        output.__enter__()
        self.addCleanup(output.__exit__, None, None, None)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.base_release = release("0.3.6", assets=[asset("stable.zip", tag="v0.3.6")], published="2026-10-30T00:00:00Z")
        self.curated = {
            "version": "0.3.6", "tag": "v0.3.6", "published_at": self.base_release["published_at"], "channel": "stable",
            "changelog": {"nl": "changelogs/v0.3.6.nl.md", "en": "changelogs/v0.3.6.en.md"},
            "downloads": [{"id": "reviewed", "kind": "archive", "platform": "linux", "architecture": "amd64",
                           "label": {"nl": "Beoordeeld", "en": "Reviewed"}, "asset": "stable.zip", "sha256": "a" * 64,
                           "compiled_protection": "Nuitka"}],
        }
        self.catalog = {"schema": "indusspine-downloads-v1", "repository": sync.REPOSITORY,
                        "latest": "0.3.6", "releases": [self.curated]}
        (self.root / "downloads.json").write_text(json.dumps(self.catalog) + "\n", encoding="utf-8")
        (self.root / "changelogs").mkdir()
        for language in ("nl", "en"):
            (self.root / f"changelogs/v0.3.6.{language}.md").write_text(f"Hand-curated {language}\n", encoding="utf-8")

    def run_sync(self, *extra, check=False):
        return sync.synchronize(self.root, [self.base_release, *extra], check=check)

    def read_catalog(self):
        return json.loads((self.root / "downloads.json").read_text(encoding="utf-8"))

    def test_first_reconciliation_preserves_curated_records_and_is_idempotent(self):
        before = (self.root / "downloads.json").read_bytes()
        changed = self.run_sync()
        self.assertEqual(changed, [sync.STATE_PATH.as_posix()])
        self.assertEqual((self.root / "downloads.json").read_bytes(), before)
        self.assertEqual((self.root / "changelogs/v0.3.6.nl.md").read_text(), "Hand-curated nl\n")
        self.assertEqual(self.run_sync(), [])

    def test_new_stable_is_added_with_hashes_and_bilingual_notes(self):
        self.run_sync(release())
        catalog = self.read_catalog()
        self.assertEqual(catalog["latest"], "0.3.7")
        generated = catalog["releases"][1]
        self.assertEqual(generated["channel"], "stable")
        self.assertEqual(generated["downloads"][0]["platform"], "windows")
        self.assertEqual(generated["downloads"][0]["sha256"], "a" * 64)
        self.assertNotIn("compiled_protection", generated["downloads"][0])
        self.assertTrue((self.root / generated["changelog"]["nl"]).exists())
        self.assertTrue((self.root / generated["changelog"]["en"]).exists())
        self.assertEqual(catalog["releases"][0], self.curated)

    def test_preview_never_becomes_latest(self):
        self.run_sync(release("99.0.0-rc.1"))
        catalog = self.read_catalog()
        self.assertEqual(catalog["latest"], "0.3.6")
        self.assertEqual(catalog["releases"][1]["channel"], "preview")

    def test_latest_uses_numeric_versions(self):
        self.run_sync(release("0.3.9"), release("0.3.10"))
        self.assertEqual(self.read_catalog()["latest"], "0.3.10")

    def test_draft_is_not_visible(self):
        draft = release()
        draft["draft"] = True
        self.run_sync(draft)
        self.assertEqual(self.read_catalog(), self.catalog)

    def test_new_auto_release_is_refreshed_after_asset_upload(self):
        pending = release(assets=[])
        self.run_sync(pending)
        self.assertEqual(self.read_catalog()["releases"][1]["downloads"], [])
        self.run_sync(release())
        self.assertEqual(len(self.read_catalog()["releases"][1]["downloads"]), 1)

    def test_edited_notes_update_only_auto_managed_versions(self):
        self.run_sync(release(body="Before"))
        self.run_sync(release(body="After"))
        self.assertIn("After", (self.root / "changelogs/v0.3.7.nl.md").read_text())
        self.assertNotIn("Before", (self.root / "changelogs/v0.3.7.nl.md").read_text())
        self.assertEqual((self.root / "changelogs/v0.3.6.en.md").read_text(), "Hand-curated en\n")

    def test_bilingual_markers_and_untrusted_body_are_plain_data(self):
        body = "<!-- nl -->\nNederlandse tekst $(touch impossible)\n<!-- en -->\nEnglish text"
        self.run_sync(release(body=body))
        nl = (self.root / "changelogs/v0.3.7.nl.md").read_text()
        en = (self.root / "changelogs/v0.3.7.en.md").read_text()
        self.assertIn("Nederlandse tekst $(touch impossible)", nl)
        self.assertNotIn("English text", nl)
        self.assertIn("English text", en)
        self.assertNotIn("Nederlandse tekst", en)
        self.assertFalse((self.root / "impossible").exists())

    def test_prerelease_flag_mismatch_is_transactionally_rejected(self):
        wrong = release("0.3.7-rc.1")
        wrong["prerelease"] = False
        before = (self.root / "downloads.json").read_bytes()
        with self.assertRaises(sync.CatalogError):
            self.run_sync(release("0.3.8"), wrong)
        self.assertEqual((self.root / "downloads.json").read_bytes(), before)
        self.assertFalse((self.root / "changelogs/v0.3.8.nl.md").exists())

    def test_reviewed_asset_replacement_requires_review(self):
        self.base_release["assets"][0]["digest"] = "sha256:" + "b" * 64
        with self.assertRaisesRegex(sync.CatalogError, "Reviewed asset digest changed"):
            self.run_sync()

    def test_wrong_asset_url_is_rejected(self):
        wrong = release()
        wrong["assets"][0]["browser_download_url"] = "https://example.com/program.exe"
        with self.assertRaisesRegex(sync.CatalogError, "Unexpected download URL"):
            self.run_sync(wrong)

    def test_missing_digest_does_not_invent_checksum(self):
        incomplete = release()
        incomplete["assets"][0]["digest"] = None
        self.run_sync(incomplete)
        self.assertEqual(self.read_catalog()["releases"][1]["downloads"], [])

    def test_split_archives_and_unsupported_source_files_are_not_buttons(self):
        files = [asset("image.tar.zst.part001"), asset("private.py"), asset("SHA256SUMS.txt")]
        self.run_sync(release(assets=files))
        entries = self.read_catalog()["releases"][1]["downloads"]
        self.assertEqual([entry["kind"] for entry in entries], ["checksums"])
        self.assertEqual(entries[0]["platform"], "all")

    def test_duplicate_assets_are_rejected(self):
        with self.assertRaisesRegex(sync.CatalogError, "duplicate asset names"):
            self.run_sync(release(assets=[asset(), asset()]))

    def test_deleted_release_is_removed_without_deleting_curated_notes(self):
        sync.synchronize(self.root, [])
        self.assertEqual(self.read_catalog()["releases"], [])
        self.assertIsNone(self.read_catalog()["latest"])
        self.assertTrue((self.root / "changelogs/v0.3.6.nl.md").exists())

    def test_twenty_release_limit_retains_latest_stable(self):
        previews = [release(f"9.0.0-test.{index}") for index in range(25)]
        self.run_sync(*previews)
        catalog = self.read_catalog()
        self.assertEqual(len(catalog["releases"]), 20)
        self.assertEqual(catalog["latest"], "0.3.6")
        self.assertIn("0.3.6", [entry["version"] for entry in catalog["releases"]])

    def test_read_only_check_has_no_filesystem_side_effects(self):
        changed = self.run_sync(release(), check=True)
        self.assertIn("downloads.json", changed)
        self.assertEqual(self.read_catalog(), self.catalog)
        self.assertFalse((self.root / sync.STATE_PATH).exists())

    def test_unsupported_tag_is_ignored(self):
        unsupported = release()
        unsupported["tag_name"] = "nightly"
        self.run_sync(unsupported)
        self.assertEqual(self.read_catalog(), self.catalog)

    def test_invalid_date_is_rejected_before_writing(self):
        with self.assertRaisesRegex(sync.CatalogError, "Invalid publication date"):
            self.run_sync(release(published="2026-99-31T12:00:00Z"))
        self.assertEqual(self.read_catalog(), self.catalog)


if __name__ == "__main__":
    unittest.main()
