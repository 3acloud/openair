#!/usr/bin/env python3
"""Build and verify every Fireworks Tech Graph distribution from one payload."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import stat
import subprocess
import tarfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Optional, Sequence


ROOT = Path(__file__).resolve().parents[1]
MIRROR = ROOT / "skills" / "fireworks-tech-graph"


def _npm_pack(*arguments: str) -> list[dict[str, object]]:
    process = subprocess.run(
        ["npm", "pack", *arguments, "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode:
        raise RuntimeError(process.stderr.strip() or process.stdout.strip() or "npm pack failed")
    try:
        payload = json.loads(process.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"npm pack did not return JSON: {process.stdout[-400:]}") from error
    if not isinstance(payload, list) or not payload:
        raise RuntimeError("npm pack returned no package metadata")
    return payload


def package_file_list() -> list[Path]:
    package = _npm_pack("--dry-run")[0]
    files = package.get("files", [])
    paths = sorted(Path(str(item["path"])) for item in files if isinstance(item, dict) and item.get("path"))
    if not paths or Path("SKILL.md") not in paths or Path("package.json") not in paths:
        raise RuntimeError("npm payload is missing required skill files")
    if any(path.parts and path.parts[0] == "skills" for path in paths):
        raise RuntimeError("package payload must not recursively include skills/")
    return paths


def _file_mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode) & 0o777


def sync_nested_skill(check: bool = False) -> list[str]:
    paths = package_file_list()
    problems: list[str] = []
    expected = {path.as_posix() for path in paths}
    if check:
        if not MIRROR.is_dir():
            return [f"missing nested skill mirror: {MIRROR.relative_to(ROOT)}"]
        actual = {
            path.relative_to(MIRROR).as_posix()
            for path in MIRROR.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
        }
        for relative in sorted(expected - actual):
            problems.append(f"mirror missing: {relative}")
        for relative in sorted(actual - expected):
            problems.append(f"mirror has unexpected file: {relative}")
        for relative in sorted(expected & actual):
            source = ROOT / relative
            target = MIRROR / relative
            if source.read_bytes() != target.read_bytes():
                problems.append(f"mirror content differs: {relative}")
            if bool(_file_mode(source) & stat.S_IXUSR) != bool(_file_mode(target) & stat.S_IXUSR):
                problems.append(f"mirror executable mode differs: {relative}")
        return problems

    if MIRROR.exists():
        shutil.rmtree(MIRROR)
    for relative in paths:
        source = ROOT / relative
        target = MIRROR / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return []


def _tar_payload(tgz: Path) -> dict[str, tuple[bytes, int]]:
    payload: dict[str, tuple[bytes, int]] = {}
    with tarfile.open(tgz, "r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile() or not member.name.startswith("package/"):
                continue
            relative = PurePosixPath(member.name).relative_to("package").as_posix()
            extracted = archive.extractfile(member)
            if extracted is None:
                raise RuntimeError(f"cannot read tar member: {member.name}")
            payload[relative] = (extracted.read(), member.mode & 0o777)
    return payload


def build_release_zip(tgz: Path, output: Path) -> Path:
    payload = _tar_payload(tgz)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative, (content, mode) in sorted(payload.items()):
            info = zipfile.ZipInfo(f"fireworks-tech-graph/{relative}")
            info.date_time = (2026, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | mode) << 16
            archive.writestr(info, content)
    return output


def _zip_payload(path: Path) -> dict[str, tuple[bytes, int]]:
    payload: dict[str, tuple[bytes, int]] = {}
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir() or not info.filename.startswith("fireworks-tech-graph/"):
                continue
            relative = PurePosixPath(info.filename).relative_to("fireworks-tech-graph").as_posix()
            payload[relative] = (archive.read(info), (info.external_attr >> 16) & 0o777)
    return payload


def verify_archive_parity(tgz: Path, release_zip: Path) -> list[str]:
    tar_payload = _tar_payload(tgz)
    zip_payload = _zip_payload(release_zip)
    problems: list[str] = []
    for relative in sorted(set(tar_payload) | set(zip_payload)):
        if relative not in tar_payload:
            problems.append(f"zip-only file: {relative}")
        elif relative not in zip_payload:
            problems.append(f"tgz-only file: {relative}")
        elif hashlib.sha256(tar_payload[relative][0]).digest() != hashlib.sha256(zip_payload[relative][0]).digest():
            problems.append(f"archive content differs: {relative}")
    return problems


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_release(output_dir: Path) -> list[Path]:
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    version = str(package["version"])
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = _npm_pack("--pack-destination", str(output_dir))[0]
    filename = str(metadata.get("filename", ""))
    tgz = output_dir / filename
    if not filename or not tgz.is_file():
        raise RuntimeError("npm pack did not create the expected tarball")
    release_zip = output_dir / f"fireworks-tech-graph-v{version}.zip"
    build_release_zip(tgz, release_zip)
    problems = verify_archive_parity(tgz, release_zip)
    if problems:
        raise RuntimeError("; ".join(problems))
    checksums = output_dir / "SHA256SUMS"
    checksums.write_text(
        "".join(f"{_sha256(path)}  {path.name}\n" for path in (tgz, release_zip)),
        encoding="utf-8",
    )
    return [tgz, release_zip, checksums]


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--sync", action="store_true")
    action.add_argument("--check", action="store_true")
    action.add_argument("--build-release", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        if args.sync:
            sync_nested_skill(check=False)
            print(f"synced {MIRROR.relative_to(ROOT)}")
        elif args.check:
            problems = sync_nested_skill(check=True)
            if problems:
                for problem in problems:
                    print(problem)
                return 1
            print("nested skill mirror matches npm payload")
        else:
            for path in build_release(args.output_dir):
                print(path)
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"distribution error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
