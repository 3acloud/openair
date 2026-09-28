#!/usr/bin/env bash
# Weights for MiniMax H3. About 47 GB for the default set.
#
#   ./install/download-models.sh --dir /path/to/ComfyUI/models
#   ./install/download-models.sh --dir DIR --base bf16     # full precision base
#   ./install/download-models.sh --dir DIR --list          # sizes, download nothing
#
# The pruned int8 base is the default because it is what these workflows are
# tuned against and it fits a single 24 GB card. The bf16 base is 40 GB and only
# makes sense if you have the room and want to compare.
set -euo pipefail

DIR=""; BASE="pruned-int8"; LIST=0
while [ $# -gt 0 ]; do
  case "$1" in
    --dir) DIR="$2"; shift 2 ;;
    --base) BASE="$2"; shift 2 ;;
    --list) LIST=1; shift ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

H3="https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main"
LORA="https://huggingface.co/larryvrh/MiniMax-H3-Turbo-Lora/resolve/main"

case "$BASE" in
  pruned-int8) BASE_FILE="minimax_h3_fl2va_pruned_int8_convrot.safetensors"; BASE_SIZE="21 GB" ;;
  int8)        BASE_FILE="minimax_h3_fl2va_int8_convrot.safetensors";        BASE_SIZE="34 GB" ;;
  bf16)        BASE_FILE="minimax_h3_fl2va_bf16.safetensors";                BASE_SIZE="66 GB" ;;
  *) echo "--base must be pruned-int8, int8 or bf16" >&2; exit 2 ;;
esac

# subdir | filename | url | size | note
FILES=(
  "diffusion_models|$BASE_FILE|$H3/diffusion_models/$BASE_FILE|$BASE_SIZE|the model itself"
  "text_encoders|qwen3vl_32b_minimax_h3_int8_convrot.safetensors|$H3/text_encoders/qwen3vl_32b_minimax_h3_int8_convrot.safetensors|25 GB|prompt encoder, already int8"
  "vae|minimax_h3_video_vae_fp16.safetensors|$H3/vae/minimax_h3_video_vae_fp16.safetensors|500 MB|frames"
  "vae|minimax_h3_audio_vae_fp32.safetensors|$H3/vae/minimax_h3_audio_vae_fp32.safetensors|600 MB|audio"
  "loras|minimax_h3_turbo_v4_step600_ema.safetensors|$LORA/minimax_h3_turbo_v4_step600_ema.safetensors|780 MB|turbo LoRA, 4-8 steps instead of 20"
  "loras|minimax_h3_turbo_4step_ema_ckpt850.safetensors|$LORA/minimax_h3_turbo_4step_ema_ckpt850.safetensors|780 MB|older turbo LoRA, friendlier at 4 steps with heavy motion"
)

if [ "$LIST" = 1 ]; then
  printf '%-18s %-62s %8s  %s\n' "folder" "file" "size" "what for"
  for row in "${FILES[@]}"; do
    IFS='|' read -r sub name url size note <<< "$row"
    printf '%-18s %-62s %8s  %s\n' "$sub" "$name" "$size" "$note"
  done
  exit 0
fi

[ -n "$DIR" ] || { echo "need --dir /path/to/ComfyUI/models" >&2; exit 2; }
command -v curl >/dev/null || { echo "curl is required" >&2; exit 1; }

for row in "${FILES[@]}"; do
  IFS='|' read -r sub name url size note <<< "$row"
  mkdir -p "$DIR/$sub"
  dst="$DIR/$sub/$name"
  if [ -s "$dst" ]; then
    printf '\033[32mhave\033[0m  %s\n' "$sub/$name"
    continue
  fi
  printf '\033[1mget\033[0m   %s  (%s, %s)\n' "$sub/$name" "$size" "$note"
  # -C - resumes a half-finished file instead of starting the 25 GB over
  curl -fL -C - --retry 3 --progress-bar -o "$dst" "$url" || {
    echo "failed: $name" >&2
    rm -f "$dst"
    exit 1
  }
done

echo
echo "done. Both turbo LoRAs are here on purpose: v4 is the better one in general,"
echo "ckpt850 holds up better at 4 steps when the shot is full of fast motion."
