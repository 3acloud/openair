#!/usr/bin/env bash
# MiniMax H3 for ComfyUI — installer.
#
#   ./install/setup.sh check                    what you have, what is missing
#   ./install/setup.sh standard  --comfy DIR    workflows into an existing ComfyUI
#   ./install/setup.sh multi-gpu --dir DIR      build the Raylight stack from scratch
#
# The standard set runs anywhere a single 24 GB card runs. The multi-gpu set
# needs two cards or more and its own environment, because Raylight pins an
# older torch than current ComfyUI ships with — that is exactly why it goes into
# a separate directory instead of on top of your working install.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-check}"; shift || true

COMFY=""; DIR=""; TORCH_CUDA="cu128"; SKIP_SAGE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --comfy) COMFY="$2"; shift 2 ;;
    --dir) DIR="$2"; shift 2 ;;
    --cuda) TORCH_CUDA="$2"; shift 2 ;;
    --skip-sage) SKIP_SAGE=1; shift ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

say()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '  \033[32mok\033[0m    %s\n' "$*"; }
warn() { printf '  \033[33mmiss\033[0m  %s\n' "$*"; }
die()  { printf '\n\033[31m%s\033[0m\n' "$*" >&2; exit 1; }

# ---------------------------------------------------------------- detection
# uv often lives here and is missing from PATH over a non-interactive ssh
[ -d "$HOME/.local/bin" ] && PATH="$HOME/.local/bin:$PATH"

detect() {
  GPUS=0; ARCH=""; CUDA_HOME_GUESS=""
  if command -v nvidia-smi >/dev/null 2>&1; then
    GPUS=$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l | tr -d ' ')
    # compute capability drives what SageAttention gets compiled for; guessing it
    # wrong produces a wheel that imports and then fails at the first kernel
    ARCH=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader | head -1 | tr -d ' .')
  fi
  for c in /usr/local/cuda-12.8 /usr/local/cuda-12.6 /usr/local/cuda; do
    [ -d "$c" ] && { CUDA_HOME_GUESS="$c"; break; }
  done
}

# ------------------------------------------------------------------- check
do_check() {
  detect
  say "hardware"
  if [ "$GPUS" -gt 0 ]; then
    nvidia-smi --query-gpu=index,name,memory.total,power.limit --format=csv,noheader | sed 's/^/  /'
    ok "$GPUS card(s), compute capability ${ARCH:0:1}.${ARCH:1}"
    [ "$GPUS" -ge 2 ] && ok "multi-gpu set is worth installing" \
                      || warn "one card — multi-gpu set will not speed anything up, use standard"
  else
    warn "no nvidia-smi, cannot see any GPU"
  fi

  say "toolchain"
  command -v git >/dev/null && ok "git" || warn "git"
  command -v uv  >/dev/null && ok "uv" || warn "uv (curl -LsSf https://astral.sh/uv/install.sh | sh)"
  [ -n "$CUDA_HOME_GUESS" ] && ok "CUDA toolkit at $CUDA_HOME_GUESS" \
                            || warn "no CUDA toolkit — needed only to build SageAttention"

  say "power limit"
  if [ "$GPUS" -gt 0 ]; then
    nvidia-smi --query-gpu=index,power.limit,power.default_limit --format=csv,noheader | sed 's/^/  /'
    echo "  cards shipped below their default limit sample slower; raising it to the"
    echo "  default cut one of our runs by 23% (220 W -> 320 W on 3090s)"
  fi

  say "what this repo installs"
  echo "  standard    workflows for any single card, 24 GB and up"
  echo "  multi-gpu   Raylight stack: real parallelism across 2+ cards"
  echo "  models      weights, about 60 GB (install/download-models.sh)"
}

# ---------------------------------------------------------------- standard
do_standard() {
  [ -n "$COMFY" ] || die "need --comfy /path/to/ComfyUI"
  [ -d "$COMFY" ] || die "not a directory: $COMFY"
  [ -f "$COMFY/main.py" ] || die "does not look like ComfyUI (no main.py): $COMFY"

  say "workflows"
  local dst="$COMFY/user/default/workflows/minimax-h3"
  mkdir -p "$dst"
  cp "$REPO"/workflows/standard/*.json "$dst/"
  ok "$(ls "$REPO"/workflows/standard/*.json | wc -l | tr -d ' ') workflows -> $dst"

  say "long-form patch"
  # the chaining node samples in a loop; without this patch it fights MultiGPU
  # over memory and the second shot lands on the wrong device
  mkdir -p "$COMFY/custom_nodes/h3-longform-patch"
  cp "$REPO/custom-nodes/longform-patch/__init__.py" \
     "$COMFY/custom_nodes/h3-longform-patch/__init__.py"
  ok "custom_nodes/h3-longform-patch"

  say "still needed by hand"
  echo "  ComfyUI-MultiGPU, ComfyUI-KJNodes, ComfyUI-MiniMax-H3-Turbo (via Manager)"
  echo "  weights: ./install/download-models.sh --dir $COMFY/models"
}

# --------------------------------------------------------------- multi-gpu
do_multigpu() {
  [ -n "$DIR" ] || die "need --dir /path/for/the/raylight/stack"
  detect
  [ "$GPUS" -ge 2 ] || warn "only $GPUS card(s) visible — this set needs two or more to pay off"
  command -v uv >/dev/null || die "uv is required: curl -LsSf https://astral.sh/uv/install.sh | sh"

  say "ComfyUI checkout"
  if [ -d "$DIR/.git" ]; then ok "already at $DIR"
  else git clone --depth 1 https://github.com/comfyanonymous/ComfyUI "$DIR"; ok "cloned"; fi
  cd "$DIR"

  say "python 3.11 + torch (${TORCH_CUDA})"
  # torch is pinned: Raylight's xfuser path breaks on newer builds, and 2.8.1 has
  # no cu128 wheel at all
  [ -d .venv ] || uv venv --python 3.11
  uv pip install --python .venv \
     torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 \
     --index-url "https://download.pytorch.org/whl/${TORCH_CUDA}"
  uv pip install --python .venv -r requirements.txt
  ok "torch 2.8.0+${TORCH_CUDA}"

  say "ray + xfuser"
  uv pip install --python .venv "ray[default]==2.56.1" xfuser==0.4.5 yunchang==0.6.4
  ok "ray 2.56.1, xfuser 0.4.5"

  say "custom nodes"
  mkdir -p custom_nodes && cd custom_nodes
  clone_node() {
    local url="$1" name="$2"
    if [ -d "$name" ]; then ok "$name (already)"; else git clone --depth 1 "$url" "$name" >/dev/null 2>&1 && ok "$name"; fi
  }
  clone_node https://github.com/komikndr/raylight raylight
  clone_node https://github.com/Larryvrh/ComfyUI-MiniMax-H3-Turbo ComfyUI-MiniMax-H3-Turbo
  clone_node https://github.com/kijai/ComfyUI-KJNodes ComfyUI-KJNodes
  clone_node https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite ComfyUI-VideoHelperSuite
  for n in h3-ray-kit h3-turbo-ray; do
    mkdir -p "${n//-/_}" && cp "$REPO/custom-nodes/$n/__init__.py" "${n//-/_}/__init__.py"
    ok "${n//-/_} (from this repo)"
  done
  cd "$DIR"
  uv pip install --python .venv -r custom_nodes/raylight/requirements.txt 2>/dev/null || true

  say "turbo LoRA patch"
  # Ray re-imports the worker class in every process, so a monkey patch made in
  # the main process never arrives; sitecustomize runs at interpreter start
  local sp; sp="$(.venv/bin/python -c 'import site;print(site.getsitepackages()[0])')"
  cp "$REPO"/patches/{sitecustomize.py,h3_turbo_lora_ray.py,h3_turbo_ray.py} "$sp/"
  ok "patches -> $sp"

  if [ "$SKIP_SAGE" = 0 ]; then
    say "SageAttention (compiled for sm_${ARCH})"
    if .venv/bin/python -c "import sageattention" 2>/dev/null; then
      ok "already installed"
    elif [ -z "$CUDA_HOME_GUESS" ]; then
      warn "no CUDA toolkit — skipping, pass --skip-sage to silence this"
    else
      local src="$DIR/../SageAttention-src"
      [ -d "$src" ] || git clone --depth 1 https://github.com/thu-ml/SageAttention "$src"
      ( cd "$src" && CUDA_HOME="$CUDA_HOME_GUESS" TORCH_CUDA_ARCH_LIST="${ARCH:0:1}.${ARCH:1}" \
        EXT_PARALLEL=4 NVCC_APPEND_FLAGS="--threads 8" MAX_JOBS=8 \
        uv pip install --python "$DIR/.venv" --no-build-isolation . ) && ok "built" || warn "build failed, stack still runs on torch attention"
    fi
  fi

  say "workflows"
  mkdir -p user/default/workflows/raylight-h3
  cp "$REPO"/workflows/multi-gpu/*.json user/default/workflows/raylight-h3/
  ok "4 workflows -> user/default/workflows/raylight-h3"

  say "done"
  cat <<EOF
  weights:  $REPO/install/download-models.sh --dir $DIR/models
  start:    cd $DIR && ./.venv/bin/python main.py --listen 0.0.0.0 --port 8189 \\
              --disable-auto-launch --disable-dynamic-vram
  open:     http://localhost:8189  ->  Workflows  ->  raylight-h3

  The turbo LoRA patch reports itself on model load:
    [H3TurboRay rank 0] ... 208 adapters, 208 hooks + 51 adaln at run time
  No such line means the patch did not take and the run silently ignores the LoRA.
EOF
}

case "$MODE" in
  check) do_check ;;
  standard) do_standard ;;
  multi-gpu|multigpu) do_multigpu ;;
  *) die "usage: setup.sh {check|standard|multi-gpu} [--comfy DIR] [--dir DIR]" ;;
esac
