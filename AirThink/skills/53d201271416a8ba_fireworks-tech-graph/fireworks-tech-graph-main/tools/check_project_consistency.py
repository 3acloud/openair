#!/usr/bin/env python3
"""Fail CI when product, package, site, and installation claims drift."""

from __future__ import annotations

import hashlib
import json
import re
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALL_SOURCE = "yizhiyanhua-ai/fireworks-tech-graph/skills/fireworks-tech-graph"
STYLE_CATALOG = {
    1: ("style-1-flat-icon.md", "mem0-style1.json", "sample-style1-flat.png"),
    2: ("style-2-dark-terminal.md", "tool-call-style2.json", "sample-style2-dark.png"),
    3: ("style-3-blueprint.md", "microservices-style3.json", "sample-style3-blueprint.png"),
    4: ("style-4-notion-clean.md", "agent-memory-types-style4.json", "sample-style4-notion.png"),
    5: ("style-5-glassmorphism.md", "multi-agent-style5.json", "sample-style5-glass.png"),
    6: ("style-6-claude-official.md", "system-architecture-style6.json", "sample-style6-claude.png"),
    7: ("style-7-openai.md", "api-flow-style7.json", "sample-style7-openai.png"),
    8: ("style-8-dark-luxury.md", "dark-luxury-style8.svg", "sample-style8-dark-luxury.png"),
    9: ("style-9-c4-review-canvas.md", "c4-review-canvas-style9.json", "sample-style9-c4-review-canvas.png"),
    10: ("style-10-cloud-fabric.md", "cloud-fabric-style10.json", "sample-style10-cloud-fabric.png"),
    11: ("style-11-event-transit.md", "event-transit-style11.json", "sample-style11-event-transit.png"),
    12: ("style-12-ops-pulse.md", "ops-pulse-style12.json", "sample-style12-ops-pulse.png"),
}
GENERATOR_STYLES = (1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12)
ANIMATED_SHOWCASE = (
    "showcase-12-styles.gif",
    "sample-style1-flat.gif",
    "sample-style2-dark.gif",
    "sample-style3-blueprint.gif",
    "sample-style4-notion.gif",
    "sample-style5-glass.gif",
    "sample-style6-claude.gif",
    "sample-style7-openai.gif",
    "sample-style8-dark-luxury.gif",
    "sample-style9-c4-review-canvas.gif",
    "sample-style10-cloud-fabric.gif",
    "sample-style11-event-transit.gif",
    "sample-style12-ops-pulse.gif",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_gif_sub_blocks(data: bytes, offset: int) -> tuple[bytes, int]:
    chunks: list[bytes] = []
    while True:
        if offset >= len(data):
            raise ValueError("truncated GIF sub-block stream")
        size = data[offset]
        offset += 1
        if size == 0:
            return b"".join(chunks), offset
        if offset + size > len(data):
            raise ValueError("truncated GIF sub-block payload")
        chunks.append(data[offset : offset + size])
        offset += size


def _inspect_gif(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if len(data) < 13 or data[:6] not in (b"GIF87a", b"GIF89a"):
        raise ValueError("invalid GIF header")
    width, height = struct.unpack_from("<HH", data, 6)
    packed = data[10]
    offset = 13
    if packed & 0x80:
        offset += 3 * (2 ** ((packed & 0x07) + 1))

    delays: list[int] = []
    pending_delay: int | None = None
    loop_count: int | None = None
    frames = 0
    while offset < len(data):
        marker = data[offset]
        offset += 1
        if marker == 0x3B:
            break
        if marker == 0x21:
            if offset >= len(data):
                raise ValueError("truncated GIF extension")
            label = data[offset]
            offset += 1
            if label == 0xF9:
                if offset + 6 > len(data) or data[offset] != 4:
                    raise ValueError("invalid GIF graphic control extension")
                pending_delay = struct.unpack_from("<H", data, offset + 2)[0]
                terminator = offset + 5
                if data[terminator] != 0:
                    raise ValueError("unterminated GIF graphic control extension")
                offset = terminator + 1
            elif label == 0xFF:
                if offset >= len(data):
                    raise ValueError("truncated GIF application extension")
                block_size = data[offset]
                offset += 1
                if offset + block_size > len(data):
                    raise ValueError("truncated GIF application identifier")
                application = data[offset : offset + block_size]
                offset += block_size
                payload, offset = _read_gif_sub_blocks(data, offset)
                if application in (b"NETSCAPE2.0", b"ANIMEXTS1.0") and len(payload) >= 3 and payload[0] == 1:
                    loop_count = struct.unpack_from("<H", payload, 1)[0]
            else:
                _, offset = _read_gif_sub_blocks(data, offset)
            continue
        if marker != 0x2C:
            raise ValueError(f"unexpected GIF block marker: 0x{marker:02x}")
        if offset + 9 > len(data):
            raise ValueError("truncated GIF image descriptor")
        local_packed = data[offset + 8]
        offset += 9
        if local_packed & 0x80:
            offset += 3 * (2 ** ((local_packed & 0x07) + 1))
        if offset >= len(data):
            raise ValueError("truncated GIF image data")
        offset += 1  # LZW minimum code size
        _, offset = _read_gif_sub_blocks(data, offset)
        frames += 1
        delays.append(0 if pending_delay is None else pending_delay)
        pending_delay = None

    delay_histogram: dict[str, int] = {}
    for delay in delays:
        key = str(delay)
        delay_histogram[key] = delay_histogram.get(key, 0) + 1
    return {
        "width": width,
        "height": height,
        "frames": frames,
        "duration_seconds": sum(delays) / 100,
        "delay_histogram": delay_histogram,
        "loop_count": loop_count,
    }


def main() -> int:
    problems: list[str] = []
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    version = str(package["version"])
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if f"## {version} " not in changelog:
        problems.append(f"CHANGELOG.md has no {version} release heading")
    release_notes = ROOT / "docs" / "releases" / f"v{version}.md"
    if not release_notes.is_file():
        problems.append(f"missing release notes: {release_notes.relative_to(ROOT)}")
    elif not release_notes.read_text(encoding="utf-8").startswith(
        f"# Fireworks Tech Graph v{version}\n"
    ):
        problems.append(f"release notes title does not match package version: {release_notes.relative_to(ROOT)}")
    if any(str(entry).startswith("skills") for entry in package.get("files", [])):
        problems.append("package.json files must not include skills/")

    for relative in ("README.md", "README.zh.md", "index.html"):
        text = (ROOT / relative).read_text(encoding="utf-8")
        if INSTALL_SOURCE not in text:
            problems.append(f"{relative} is missing the nested skills install source")
        if "Codex" not in text or "Claude Code" not in text:
            problems.append(f"{relative} must describe both Codex and Claude Code")
        if relative != "index.html" and "12" not in text:
            problems.append(f"{relative} is missing the twelve-style claim")

    showcase = Path("assets") / "samples" / "showcase-12-styles.gif"
    if not (ROOT / showcase).is_file():
        problems.append(f"missing latest showcase overview: {showcase}")
    for relative in ("README.md", "README.zh.md"):
        readme = (ROOT / relative).read_text(encoding="utf-8")
        if showcase.as_posix() not in readme:
            problems.append(f"{relative} is missing the latest showcase overview")
        static_images = re.findall(r"!\[[^]]*\]\((assets/samples/[^)]+\.png)\)", readme)
        if static_images:
            problems.append(f"{relative} still embeds static showcase images: {', '.join(static_images)}")

    samples = ROOT / "assets" / "samples"
    manifest_path = samples / "showcase-gif-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        problems.append(f"cannot read animated showcase manifest: {error}")
        manifest = {}
    if not isinstance(manifest, dict):
        problems.append("animated showcase manifest must be a JSON object")
        manifest = {}
    entries = manifest.get("assets", [])
    by_name = {
        str(entry.get("file")): entry
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("file"), str)
    }
    if manifest.get("schema_version") != 1:
        problems.append("animated showcase manifest must use schema_version 1")
    if manifest.get("source_contract") != "user-approved +2s-settled-flow":
        problems.append("animated showcase manifest is missing the approved motion contract")
    approval = manifest.get("approval")
    if not isinstance(approval, dict) or approval != {
        "status": "user-approved",
        "style_count": 12,
        "full_size_frame_count": 1380,
        "compatibility_frames_accepted": 852,
        "compatibility_frames_total": 852,
    }:
        problems.append("animated showcase manifest has incomplete public approval evidence")
    if set(by_name) != set(ANIMATED_SHOWCASE):
        problems.append("animated showcase manifest must describe exactly the overview plus 12 styles")
    for name in ANIMATED_SHOWCASE:
        path = samples / name
        if not path.is_file():
            problems.append(f"missing animated showcase asset: {path.relative_to(ROOT)}")
            continue
        entry = by_name.get(name)
        if not entry:
            continue
        if path.read_bytes()[:6] not in (b"GIF87a", b"GIF89a"):
            problems.append(f"animated showcase asset is not a GIF: {path.relative_to(ROOT)}")
        if entry.get("bytes") != path.stat().st_size:
            problems.append(f"animated showcase byte size drifted: {path.relative_to(ROOT)}")
        if entry.get("sha256") != _sha256(path):
            problems.append(f"animated showcase hash drifted: {path.relative_to(ROOT)}")
        try:
            media = _inspect_gif(path)
        except ValueError as error:
            problems.append(f"cannot inspect animated showcase asset {path.relative_to(ROOT)}: {error}")
            continue
        for field in ("width", "height", "frames", "duration_seconds"):
            if media[field] != entry.get(field):
                problems.append(f"animated showcase {field} drifted: {path.relative_to(ROOT)}")
        if media["loop_count"] != 0:
            problems.append(f"animated showcase must loop infinitely: {path.relative_to(ROOT)}")
        if name == "showcase-12-styles.gif":
            if (
                entry.get("width") != 1200
                or entry.get("height") != 1280
                or entry.get("fps") != "12/1"
                or entry.get("duration_seconds") != 5.75
                or entry.get("frames") != 69
            ):
                problems.append("animated overview metadata must remain 1200x1280, 12fps, 69 frames, and 5.75 seconds")
            if media["delay_histogram"] != {"8": 46, "9": 23}:
                problems.append("animated overview must retain its 46x8cs + 23x9cs cadence")
            if path.stat().st_size > 2 * 1024 * 1024:
                problems.append("animated overview exceeds the 2 MiB README budget")
        elif (
            entry.get("width") != 960
            or entry.get("fps") != "20/1"
            or entry.get("duration_seconds") != 5.75
            or entry.get("frames") != 115
        ):
            problems.append(f"animated style metadata drifted from the approved timeline: {name}")
        elif media["delay_histogram"] != {"5": 115}:
            problems.append(f"animated style cadence drifted from 20fps: {name}")

    for relative in ("README.md", "README.zh.md"):
        readme = (ROOT / relative).read_text(encoding="utf-8")
        for name in ANIMATED_SHOWCASE:
            target = (Path("assets") / "samples" / name).as_posix()
            if target not in readme:
                problems.append(f"{relative} is missing animated showcase asset: {target}")

    index = (ROOT / "index.html").read_text(encoding="utf-8")
    for stale in (
        "npx skills add yizhiyanhua-ai/fireworks-tech-graph\n",
        "All eight styles are generator-backed",
        "See 8 styles",
        "One system, eight aesthetics",
        "8 visual styles",
        "across 8 distinct visual styles",
        "Adaptive Workflow Engine",
    ):
        if stale in index:
            problems.append(f"index.html contains stale claim: {stale.strip()}")
    if "Agent Runtime Architecture" not in index:
        problems.append("index.html Style 8 title does not match the fixture")
    if showcase.as_posix() not in index:
        problems.append("index.html is missing the animated twelve-style overview")
    for name in ANIMATED_SHOWCASE:
        if name == showcase.name:
            continue
        target = (Path("assets") / "samples" / name).as_posix()
        if target not in index:
            problems.append(f"index.html is missing animated showcase asset: {target}")

    for style_id, (reference, fixture, sample) in STYLE_CATALOG.items():
        for relative in (
            Path("references") / reference,
            Path("fixtures") / fixture,
            Path("assets") / "samples" / sample,
        ):
            if not (ROOT / relative).is_file():
                problems.append(f"Style {style_id} is missing catalog artifact: {relative}")
        if f"STYLE {style_id:02d}" not in index:
            problems.append(f"index.html is missing the Style {style_id:02d} gallery card")

    for style_id in GENERATOR_STYLES:
        baseline = ROOT / "fixtures" / "quality-baseline" / f"agent-runtime-style{style_id}.json"
        if not baseline.is_file():
            problems.append(f"Style {style_id} is missing its same-topology quality baseline")

    semantic_source = (ROOT / "scripts" / "semantic_contracts.py").read_text(encoding="utf-8")
    for style_id, name in ((9, "C4 Review Canvas"), (10, "Cloud Fabric"), (11, "Event Transit"), (12, "Ops Pulse")):
        if f'{style_id}: "{name}"' not in semantic_source:
            problems.append(f"semantic style catalog is missing Style {style_id}: {name}")

    for path in (
        "scripts/fireworks.py",
        "scripts/diagram_ir.py",
        "scripts/fireworks_geometry.py",
        "scripts/interactive_html.py",
        "scripts/semantic_contracts.py",
        "schemas/diagram-v1.schema.json",
        "docs/CAPABILITIES.md",
        "assets/icons/cloud/manifest-v1.json",
    ):
        if not (ROOT / path).is_file():
            problems.append(f"missing required capability file: {path}")

    markdown_link = re.compile(r"\[[^]]+\]\((?!https?://|mailto:|#)([^)]+)\)")
    for relative in ("README.md", "README.zh.md", "CONTRIBUTING.md", "docs/CAPABILITIES.md"):
        source = ROOT / relative
        for raw_target in markdown_link.findall(source.read_text(encoding="utf-8")):
            target = raw_target.split("#", 1)[0].strip().strip("<>")
            if target and not (source.parent / target).resolve().exists():
                problems.append(f"broken local link in {relative}: {raw_target}")

    if problems:
        for problem in sorted(set(problems)):
            print(problem)
        return 1
    print(f"project consistency passed for v{version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
