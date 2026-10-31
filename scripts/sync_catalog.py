#!/usr/bin/env python3
"""Synchronize published GitHub releases into the unsigned website catalog."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

REPOSITORY = "Timminater/IndusSpine-Releases"
API = f"https://api.github.com/repos/{REPOSITORY}"
DOWNLOAD = f"https://github.com/{REPOSITORY}/releases/download"
STATE_PATH = Path(".github/catalog-sync-state.json")
MARKER = "<!-- indusspine-catalog-generated-v1 -->"
SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$")
ASSET_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,199}$")
DIGEST = re.compile(r"^sha256:([a-fA-F0-9]{64})$")
LABELS = {
    "docker": ("Downloadpakket Docker", "Docker download kit"),
    "installer": ("Installatiebestand", "Installer"),
    "archive": ("Downloadbestand", "Download"),
    "driver": ("Driverbundel", "Driver bundle"),
    "checksums": ("SHA-256-controlesommen", "SHA-256 checksums"),
}


class CatalogError(RuntimeError):
    pass


class GitHub:
    def releases(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for page in range(1, 11):
            batch = self._get(f"/releases?per_page=100&page={page}")
            if not isinstance(batch, list):
                raise CatalogError("GitHub returned an invalid releases response")
            result.extend(batch)
            if len(batch) < 100:
                return result
        raise CatalogError("More than 1000 releases: refusing an incomplete snapshot")

    def _get(self, path: str) -> Any:
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "IndusSpine-Catalog-Sync", "X-GitHub-Api-Version": "2022-11-28"}
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        for attempt in range(3):
            try:
                request = urllib.request.Request(API + path, headers=headers)
                opener = urllib.request.build_opener(NoRedirect())
                with opener.open(request, timeout=30) as response:
                    body = response.read(8_388_609)
                if len(body) > 8_388_608:
                    raise CatalogError("GitHub response exceeds the metadata size limit")
                return json.loads(body)
            except urllib.error.HTTPError as exc:
                if exc.code in {429, 500, 502, 503, 504} and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise CatalogError(f"GitHub API HTTP {exc.code}") from None
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise CatalogError("GitHub API could not be reached") from exc
        raise AssertionError("unreachable")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        # Repository API responses must not forward a write token to another host.
        return None


def version_key(value: str) -> tuple[int, int, int]:
    match = SEMVER.fullmatch(value)
    if not match or len(value) > 64:
        raise CatalogError(f"Unsupported version: {value!r}")
    for part in (match[4] or "").split("."):
        if len(part) > 1 and part.isascii() and part.isdigit() and part[0] == "0":
            raise CatalogError(f"Invalid SemVer numeric identifier: {value!r}")
    return tuple(int(match[index]) for index in (1, 2, 3))


def release_version(release: dict[str, Any]) -> str | None:
    tag = release.get("tag_name")
    if not isinstance(tag, str) or not tag.startswith("v"):
        return None
    value = tag[1:]
    try:
        version_key(value)
    except CatalogError:
        return None
    return value


def digest(asset: dict[str, Any]) -> str | None:
    match = DIGEST.fullmatch(asset.get("digest") or "")
    return match[1].lower() if match else None


def asset_kind(name: str) -> str | None:
    lowered = name.lower()
    if re.search(r"\.part\d+$", lowered):
        return None  # The download kit reconstructs split archives.
    if lowered.startswith("sha256") or lowered.endswith((".sha256", ".sha256sum")):
        return "checksums"
    if lowered.endswith(".indusdriver"):
        return "driver"
    if lowered.endswith((".exe", ".msi", ".msix", ".deb", ".rpm", ".appimage", ".dmg", ".pkg")):
        return "archive" if "portable" in lowered else "installer"
    if lowered.endswith((".zip", ".tar", ".tar.gz", ".tar.zst", ".tgz", ".7z", ".json")):
        return "docker" if "docker" in lowered or ("download-kit" in lowered and "ubuntu" in lowered) else "archive"
    return None


def classify(asset: dict[str, Any], tag: str) -> dict[str, Any] | None:
    name = asset.get("name")
    if not isinstance(name, str) or not ASSET_NAME.fullmatch(name):
        return None
    kind = asset_kind(name)
    sha = digest(asset)
    if kind is None or sha is None:
        return None
    if asset.get("browser_download_url") != f"{DOWNLOAD}/{tag}/{name}":
        raise CatalogError(f"Unexpected download URL for {tag}/{name}")
    if asset.get("state") != "uploaded" or type(asset.get("size")) is not int or not 0 < asset["size"] <= 10_737_418_240:
        raise CatalogError(f"Asset is not ready: {tag}/{name}")
    lowered = name.lower()
    platform = "all"
    if kind != "checksums":
        if lowered.endswith((".exe", ".msi", ".msix")) or re.search(r"(?:^|[-_.])(?:windows|win32|win64)(?:[-_.]|$)", lowered):
            platform = "windows"
        elif lowered.endswith((".dmg", ".pkg")) or re.search(r"(?:^|[-_.])(?:macos|darwin|osx)(?:[-_.]|$)", lowered):
            platform = "macos"
        elif lowered.endswith((".deb", ".rpm", ".appimage")) or re.search(r"(?:^|[-_.])(?:linux|ubuntu)(?:[-_.]|$)", lowered):
            platform = "linux"
    architecture = "all"
    if kind != "checksums":
        if re.search(r"(?:^|[-_.])(?:amd64|x86_64|x64)(?:[-_.]|$)", lowered):
            architecture = "amd64"
        elif re.search(r"(?:^|[-_.])(?:arm64|aarch64)(?:[-_.]|$)", lowered):
            architecture = "arm64"
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")[:80].rstrip("-")
    identifier = f"{slug}-{hashlib.sha256(name.encode()).hexdigest()[:8]}"
    return {"id": identifier, "kind": kind, "platform": platform, "architecture": architecture,
            "label": {locale: f"{prefix}: {name}"[:150] for locale, prefix in zip(("nl", "en"), LABELS[kind])},
            "asset": name, "sha256": sha}


def notes_body(release: dict[str, Any], locale: str) -> str:
    body = release.get("body") or ""
    if not isinstance(body, str) or len(body.encode("utf-8")) > 48_000:
        raise CatalogError("Release notes exceed the supported metadata size")
    # Optional bilingual blocks; otherwise retain the author's original language.
    markers = re.compile(r"<!--\s*(nl|en)\s*-->", re.IGNORECASE)
    sections = list(markers.finditer(body))
    for index, section in enumerate(sections):
        if section[1].lower() == locale:
            return body[section.end():sections[index + 1].start() if index + 1 < len(sections) else len(body)].strip()
    return body.strip()


def render_notes(release: dict[str, Any], version: str, locale: str) -> str:
    preview = release["prerelease"]
    title = release.get("name") or f"IndusSpine {version}"
    if not isinstance(title, str) or len(title.encode("utf-8")) > 1000:
        raise CatalogError("Invalid release title")
    body = notes_body(release, locale)
    if locale == "nl":
        intro = "**Preview/testversie.**" if preview else "Gepubliceerde release."
        description = "Automatisch overgenomen uit de GitHub-release. De oorspronkelijke taal van de auteur blijft behouden."
        empty = "Er zijn geen aanvullende GitHub-releasenotes opgegeven."
    else:
        intro = "**Preview/test release.**" if preview else "Published release."
        description = "Automatically copied from the GitHub release. The author's original language is retained."
        empty = "No additional GitHub release notes were provided."
    return f"{MARKER}\n\n# IndusSpine {version}\n\n{intro}\n\n{title}\n\n{description}\n\n{body or empty}\n"


def plan(root: Path, releases: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any], dict[Path, str], list[str]]:
    catalog = json.loads((root / "downloads.json").read_text(encoding="utf-8"))
    if catalog.get("schema") != "indusspine-downloads-v1" or catalog.get("repository") != REPOSITORY:
        raise CatalogError("Unexpected catalog schema or repository")
    existing = {item["version"]: item for item in catalog["releases"]}
    if len(existing) != len(catalog["releases"]):
        raise CatalogError("Duplicate catalog versions")
    state_file = root / STATE_PATH
    state = json.loads(state_file.read_text(encoding="utf-8")) if state_file.exists() else {"schema": "indusspine-catalog-automation-v1", "managed_versions": []}
    if state.get("schema") != "indusspine-catalog-automation-v1" or not isinstance(state.get("managed_versions"), list):
        raise CatalogError("Invalid automation state")
    managed = set(state["managed_versions"])
    remote: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []
    for release in releases:
        if not isinstance(release, dict) or type(release.get("draft")) is not bool:
            raise CatalogError("Malformed GitHub release")
        if release["draft"]:
            continue
        version = release_version(release)
        if version is None:
            warnings.append(f"Unsupported tag omitted: {release.get('tag_name')!r}")
            continue
        if type(release.get("prerelease")) is not bool or release["prerelease"] != ("-" in version):
            raise CatalogError(f"Prerelease flag does not match the version: {version}")
        published = release.get("published_at")
        if not isinstance(published, str) or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", published):
            raise CatalogError(f"Invalid publication timestamp: {version}")
        try:
            datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            raise CatalogError(f"Invalid publication date: {version}") from None
        if version in remote:
            raise CatalogError(f"Duplicate GitHub version: {version}")
        assets = release.get("assets")
        if not isinstance(assets, list) or len(assets) > 100:
            raise CatalogError(f"Unsupported asset count: {version}")
        names = [asset.get("name") for asset in assets if isinstance(asset, dict)]
        if len(names) != len(assets) or any(not isinstance(name, str) for name in names) or len(set(names)) != len(names):
            raise CatalogError(f"Invalid or duplicate asset names: {version}")
        remote[version] = release
    stable = [value for value in remote if "-" not in value]
    if remote and not stable:
        raise CatalogError("The website requires a stable latest release; previews cannot replace it")
    latest = max(stable, key=version_key) if stable else None
    selected = sorted(remote, key=lambda value: remote[value]["published_at"], reverse=True)[:20]
    if latest is not None and latest not in selected:
        selected[-1] = latest
    chosen = set(selected)
    # Preserve the ordering and hand-curated metadata of already published records.
    order = [value for value in existing if value in chosen]
    order.extend(value for value in selected if value not in existing)
    updated = copy.deepcopy(catalog)
    updated["latest"] = latest
    updated["releases"] = []
    files: dict[Path, str] = {}
    next_managed: set[str] = set()
    for value in order:
        release = remote[value]
        is_managed = value in managed or value not in existing
        if not is_managed:
            record = copy.deepcopy(existing[value])
            assets = {asset["name"]: asset for asset in release["assets"]}
            for entry in record["downloads"]:
                current = assets.get(entry["asset"])
                if current is not None and digest(current) not in {None, entry["sha256"]}:
                    raise CatalogError(f"Reviewed asset digest changed: {value}/{entry['asset']}")
        else:
            entries = []
            for asset in release["assets"]:
                entry = classify(asset, release["tag_name"])
                if entry is not None:
                    entries.append(entry)
                else:
                    warnings.append(f"Unlisted or digest-less asset: {release['tag_name']!r}/{asset['name']!r}")
            if len(entries) > 50:
                raise CatalogError(f"More than 50 website downloads: {value}")
            record = {"version": value, "tag": release["tag_name"], "published_at": release["published_at"],
                      "channel": "preview" if release["prerelease"] else "stable",
                      "changelog": {locale: f"changelogs/v{value}.{locale}.md" for locale in ("nl", "en")}, "downloads": entries}
            next_managed.add(value)
        record["published_at"] = release["published_at"]
        record["channel"] = "preview" if release["prerelease"] else "stable"
        for locale in ("nl", "en"):
            relative = Path(f"changelogs/v{value}.{locale}.md")
            if is_managed or not (root / relative).exists():
                files[relative] = render_notes(release, value, locale)
        updated["releases"].append(record)
    next_state = {"schema": "indusspine-catalog-automation-v1", "managed_versions": sorted(next_managed)}
    return updated, next_state, files, warnings


def synchronize(root: Path, releases: list[dict[str, Any]], *, check: bool = False) -> list[str]:
    catalog, state, notes, warnings = plan(root, releases)
    candidates = {**notes, STATE_PATH: json.dumps(state, ensure_ascii=False, indent=2) + "\n"}
    old = json.loads((root / "downloads.json").read_text(encoding="utf-8"))
    if catalog != old:
        candidates[Path("downloads.json")] = json.dumps(catalog, ensure_ascii=False, indent=2) + "\n"
    changed = []
    for relative, content in candidates.items():
        target = root / relative
        if target.exists() and target.read_text(encoding="utf-8") == content:
            continue
        changed.append(relative.as_posix())
        if not check:
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + ".sync-tmp")
            temporary.write_text(content, encoding="utf-8", newline="\n")
            os.replace(temporary, target)
    for warning in warnings:
        print(f"WARNING: {warning}")
    print(f"Catalog: {len(catalog['releases'])} releases; latest stable: {catalog['latest']}; changed files: {len(changed)}")
    for value in changed:
        print(f"  {value}")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true", help="Report changes without writing files")
    args = parser.parse_args()
    try:
        synchronize(args.root.resolve(), GitHub().releases(), check=args.check)
    except (CatalogError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Catalog synchronization failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
