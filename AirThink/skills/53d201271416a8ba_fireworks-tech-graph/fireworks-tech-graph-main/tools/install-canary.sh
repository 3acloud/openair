#!/bin/bash
# Verify that skills CLI installs a complete copy for Codex and Claude Code.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="${1:-${ROOT}/skills/fireworks-tech-graph}"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/fireworks-tech-graph-install.XXXXXX")"
trap 'rm -rf "$TMP_ROOT"' EXIT
mkdir -p "$TMP_ROOT/home" "$TMP_ROOT/npm-cache"

HOME="$TMP_ROOT/home" npm_config_cache="$TMP_ROOT/npm-cache" \
    npx -y skills@1.5.17 add "$SOURCE" \
    --agent codex claude-code -g -y --copy

for install_root in \
    "$TMP_ROOT/home/.agents/skills/fireworks-tech-graph" \
    "$TMP_ROOT/home/.claude/skills/fireworks-tech-graph"
do
    test -f "$install_root/SKILL.md"
    for directory in agents assets docs fixtures references schemas scripts templates tests; do
        test -d "$install_root/$directory"
    done
    cmp "$install_root/SKILL.md" "$ROOT/SKILL.md"
    cmp "$install_root/agents/openai.yaml" "$ROOT/agents/openai.yaml"
    cmp "$install_root/scripts/generate-from-template.py" "$ROOT/scripts/generate-from-template.py"
    cmp "$install_root/scripts/semantic_contracts.py" "$ROOT/scripts/semantic_contracts.py"
    test -f "$install_root/references/style-12-ops-pulse.md"
    test -f "$install_root/assets/icons/cloud/manifest-v1.json"
    test -f "$install_root/assets/samples/sample-style12-ops-pulse.png"
    test -f "$install_root/assets/samples/sample-style12-ops-pulse.gif"
    test -f "$install_root/assets/samples/showcase-12-styles.gif"
    test -f "$install_root/assets/samples/showcase-gif-manifest.json"
    test -x "$install_root/scripts/generate-diagram.sh"
    test -x "$install_root/scripts/fireworks.py"
done

python3 "$TMP_ROOT/home/.agents/skills/fireworks-tech-graph/scripts/fireworks.py" \
    render architecture \
    "$TMP_ROOT/home/.agents/skills/fireworks-tech-graph/fixtures/c4-review-canvas-style9.json" \
    "$TMP_ROOT/canary.svg" \
    --report "$TMP_ROOT/canary-layout.json"

python3 "$TMP_ROOT/home/.agents/skills/fireworks-tech-graph/scripts/fireworks.py" \
    check "$TMP_ROOT/canary.svg"

test -s "$TMP_ROOT/canary.svg"
test -s "$TMP_ROOT/canary-layout.json"

if [ "${FIREWORKS_INSTALL_CANARY_MOTION:-0}" = "1" ]; then
    MOTION_NODE_MODULES="${FIREWORKS_INSTALL_CANARY_NODE_MODULES:-$ROOT/node_modules}"
    test -d "$MOTION_NODE_MODULES/puppeteer-core"
    for install_root in \
        "$TMP_ROOT/home/.agents/skills/fireworks-tech-graph" \
        "$TMP_ROOT/home/.claude/skills/fireworks-tech-graph"
    do
        ln -s "$MOTION_NODE_MODULES" "$install_root/node_modules"
        env -u FIREWORKS_PUPPETEER_PATH \
            node "$install_root/scripts/svg2gif.js" --probe > "$TMP_ROOT/$(basename "$(dirname "$(dirname "$install_root")")").motion-probe.json"
    done

    MOTION_SKILL="$TMP_ROOT/home/.agents/skills/fireworks-tech-graph"
    python3 "$MOTION_SKILL/scripts/fireworks.py" \
        render memory \
        "$MOTION_SKILL/fixtures/mem0-style1.json" \
        "$TMP_ROOT/motion-canary.svg"
    env -u FIREWORKS_PUPPETEER_PATH \
        python3 "$MOTION_SKILL/scripts/fireworks.py" \
        animate "$TMP_ROOT/motion-canary.svg" "$TMP_ROOT/motion-canary.gif" \
        > "$TMP_ROOT/motion-canary.result.json"
    test -s "$TMP_ROOT/motion-canary.gif"
    test -s "$TMP_ROOT/motion-canary.motion.json"
    test -s "$TMP_ROOT/motion-canary.result.json"

    if [ "${FIREWORKS_INSTALL_CANARY_ALL_STYLES:-0}" = "1" ]; then
        (
            cd "$MOTION_SKILL"
            env -u FIREWORKS_PUPPETEER_PATH \
                FIREWORKS_RUN_RENDER_REGRESSION=1 \
                FIREWORKS_RENDER_PROGRESS=1 \
                python3 -m unittest discover -s tests -p 'test_motion.py' -v
        )
    fi
fi

echo "install canary passed: $SOURCE"
