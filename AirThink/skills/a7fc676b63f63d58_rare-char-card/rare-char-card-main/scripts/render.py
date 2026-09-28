#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生僻字卡片渲染器
用法 1（JSON 数据文件）:
  render.py --data data.json --style magnolia-blue --out card.png
用法 2（命令行内联）:
  render.py --char 囦 --pinyin yuán --homophone "同「渊」" --meaning "..." \
            --copy "第一行" --copy "第二行" --style fan-orange --out card.png

data.json 格式:
{
  "title": "每天认识一组生僻字",   # 可选
  "pinyin": "yuán",
  "char": "囦",
  "homophone": "同「渊」",
  "meaning": "指水面回旋的深潭",
  "copy": ["行1", "行2"],
  "cta": "快试试你手机能打出来吗"
}
"""
import argparse
import html
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_ROOT / "templates" / "card.html"

STYLES = ("magnolia-blue", "magnolia-sage", "fan-orange", "wave-beige")

# 每种风格的装饰配色（花枝/花朵/花蕊）
STYLE_DECO = {
    "magnolia-blue": {"BRANCH_COLOR": "#C9A96A", "FLOWER_COLOR": "#F2DFAE", "FLOWER_CORE": "#E9C784"},
    "magnolia-sage": {"BRANCH_COLOR": "#E4DECB", "FLOWER_COLOR": "#F2EDE0", "FLOWER_CORE": "#D8CFB4"},
    "fan-orange":    {"BRANCH_COLOR": "#C05A22", "FLOWER_COLOR": "#F8F1E4", "FLOWER_CORE": "#C05A22"},
    "wave-beige":    {"BRANCH_COLOR": "#8A6B4F", "FLOWER_COLOR": "#EDE6D6", "FLOWER_CORE": "#8A6B4F"},
}

DEFAULT_CTA = "快试试你手机能打出来吗"


def find_chrome() -> str:
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    found = shutil.which("chromium") or shutil.which("google-chrome") or shutil.which("chrome")
    if found:
        return found
    sys.exit("错误: 找不到 Chrome/Chromium，请安装 Google Chrome")


def render_html(data: dict, style: str, bg: str = "", overlay: float = 0.25) -> str:
    tpl = TEMPLATE.read_text(encoding="utf-8")
    title = data.get("title", "").strip()
    if style == "wave-beige" and title:
        title = f"「{title}」"
    copy_lines = data.get("copy") or []
    bg_class, bg_img_html = "", ""
    if bg:
        bg_uri = Path(bg).resolve().as_uri()
        bg_class = " bg-custom"
        bg_img_html = (
            f'<img class="bg-img" src="{bg_uri}">\n'
            f'  <div class="bg-overlay" style="background:rgba(0,0,0,{overlay});"></div>'
        )
    repl = {
        "STYLE": style,
        "TITLE_HTML": html.escape(title),
        "PINYIN": html.escape(data.get("pinyin", "")),
        "CHAR": html.escape(data.get("char", "")),
        "HOMOPHONE": html.escape(data.get("homophone", "")),
        "MEANING": html.escape(data.get("meaning", "")),
        "COPY_HTML": "<br>".join(html.escape(l) for l in copy_lines),
        "CTA": html.escape(data.get("cta", DEFAULT_CTA)),
        "BG_CLASS": bg_class,
        "BG_IMG_HTML": bg_img_html,
        **STYLE_DECO[style],
    }
    for k, v in repl.items():
        tpl = tpl.replace("{{" + k + "}}", v)
    return tpl


def screenshot(html_path: Path, out_path: Path, width: int, height: int) -> None:
    chrome = find_chrome()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        chrome, "--headless=new", "--no-sandbox", "--disable-gpu",
        "--disable-gpu-compositing", "--disable-software-rasterizer",
        "--hide-scrollbars", "--force-device-scale-factor=1",
        "--virtual-time-budget=3000",
        f"--window-size={width},{height}",
        f"--screenshot={out_path}",
        html_path.as_uri(),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if not out_path.exists():
        # 旧版 Chrome 不识别 --headless=new，退回 --headless
        cmd[cmd.index("--headless=new")] = "--headless"
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if not out_path.exists():
            sys.exit(f"截图失败:\n{r.stdout}\n{r.stderr}")


def main():
    ap = argparse.ArgumentParser(description="生僻字卡片渲染器")
    ap.add_argument("--data", help="JSON 数据文件路径")
    ap.add_argument("--style", choices=STYLES, default="magnolia-blue")
    ap.add_argument("--out", default="card.png")
    ap.add_argument("--save-html", help="顺便保存中间 HTML（调试用）")
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1440)
    ap.add_argument("--title", help="卡片标题（可省略）")
    ap.add_argument("--pinyin")
    ap.add_argument("--char")
    ap.add_argument("--homophone")
    ap.add_argument("--meaning")
    ap.add_argument("--copy", action="append", help="文案行，可重复")
    ap.add_argument("--cta")
    ap.add_argument("--bg", help="自定义背景图路径（搭配图片模型生成的背景，文字自动变白色+暗色遮罩）")
    ap.add_argument("--overlay", type=float, default=0.25, help="自定义背景时的暗色遮罩强度 0~1，默认 0.25")
    args = ap.parse_args()

    if args.data:
        data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    else:
        data = {k: getattr(args, k) for k in
                ("title", "pinyin", "char", "homophone", "meaning", "copy", "cta")}
        data = {k: v for k, v in data.items() if v is not None}

    for req in ("char", "pinyin", "homophone", "meaning"):
        if not data.get(req):
            sys.exit(f"错误: 缺少必填字段 {req}（JSON 或命令行二选一提供）")

    html_str = render_html(data, args.style, args.bg, args.overlay)

    if args.save_html:
        Path(args.save_html).write_text(html_str, encoding="utf-8")

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html_str)
        tmp = Path(f.name)
    try:
        screenshot(tmp, Path(args.out), args.width, args.height)
        print(f"OK: {args.out}")
    finally:
        tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
