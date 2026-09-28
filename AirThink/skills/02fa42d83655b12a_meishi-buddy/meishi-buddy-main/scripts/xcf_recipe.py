#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""下厨房菜谱完整抓取（用料 + 步骤图 + 步骤文案 + 成品图）—— meishi-buddy skill 专用
用法: python3 xcf_recipe.py <菜名> [--pick N] [--out DIR] [--size orig|800]
      --pick  选搜索结果第 N 个（默认 1）
      --out   输出根目录（默认 <创作空间>/outputs/food-content）
输出: <out>/<菜名>_recipe/
      00_成品图.jpg / step_01.jpg ... / 菜谱.md / recipe.json
"""
import html as htmllib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA_DESKTOP = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
UA_MOBILE = ("Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
             "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1")
HEADERS = {"Referer": "https://www.xiachufang.com/"}
DEFAULT_OUT = Path("/Users/wangzhifeng/Documents/000创作/obsidian/outputs/food-content")

CARD_RE = re.compile(
    r'href="(/recipe/(\d+)/)"[^>]*>\s*<div class="cover[^"]*">\s*'
    r'<img[^>]+data-src="([^"]+)"[^>]*alt="([^"]*)"', re.S)


def fetch(url: str, ua: str) -> str:
    headers = {**HEADERS, "User-Agent": ua}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def download(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(url.split("?")[0], headers=HEADERS)
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        if len(data) < 5000:
            return False
        dest.write_bytes(data)
        return True
    except Exception as e:
        print(f"  [下载失败] {dest.name}: {e}")
        return False


def sanitize(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|\s]+', "_", name.strip())[:50]


def search(keyword: str):
    url = f"https://www.xiachufang.com/search/?keyword={urllib.parse.quote(keyword)}"
    html = fetch(url, UA_DESKTOP)
    cards, seen = [], set()
    for href, rid, img, alt in CARD_RE.findall(html):
        if rid not in seen and alt.strip():
            seen.add(rid)
            cards.append({"recipe_id": rid, "title": alt.strip()})
    return cards


def parse_recipe(html_text: str, base_url: str):
    m = re.search(r'<title[^>]*>【步骤图】(.+?)的做法_', html_text)
    title = htmllib.unescape(m.group(1)).strip() if m else "未知菜谱"
    m = re.search(r'<span class="author[^>]*>\s*<a[^>]*>([^<]+)</a>', html_text)
    author = htmllib.unescape(m.group(1)).strip() if m else None
    ingredients = []
    for m in re.finditer(
            r'<div class="ing-name"[^>]*>\s*([^<]+?)\s*</div>\s*'
            r'<div class="ing-amount"[^>]*>\s*([^<]*?)\s*</div>', html_text):
        ingredients.append({"name": htmllib.unescape(m.group(1)),
                            "amount": htmllib.unescape(m.group(2)) or "适量"})
    steps = []
    for m in re.finditer(
            r'<div class="sub-title"[^>]*>\s*步骤\s*(\d+)\s*</div>\s*'
            r'<div[^>]*>.*?<mip-img src="([^"]+)"[^>]*/?>.*?'
            r'<p class="step-text"[^>]*>([\s\S]*?)</p>', html_text):
        n = int(m.group(1))
        img = m.group(2)
        text = htmllib.unescape(re.sub(r'<[^>]+>', '', m.group(3))).strip()
        steps.append({"n": n, "img": img, "text": text})
    cover = None
    for m in re.finditer(r'<mip-img src="(https://i2\.chuimg\.com[^"]+)"[^>]*alt="([^"]*)"',
                         html_text):
        if "的做法" in m.group(2) and title[:6] in m.group(2):
            cover = m.group(1)
            break
    return {"title": title, "author": author, "url": base_url,
            "ingredients": ingredients, "steps": steps, "cover": cover}


def to_markdown(r: dict) -> str:
    lines = [f"# {r['title']}", ""]
    if r["author"]:
        lines += [f"作者：{r['author']}  |  来源：[下厨房]({r['url']})", ""]
    lines += ["## 用料", ""]
    for ing in r["ingredients"]:
        lines.append(f"- {ing['name']}：{ing['amount']}")
    lines += ["", "## 步骤", ""]
    for s in r["steps"]:
        lines.append(f"### 步骤 {s['n']}")
        lines.append(f"![步骤{s['n']}](step_{s['n']:02d}.jpg)")
        lines.append("")
        lines.append(s["text"])
        lines.append("")
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    keyword = sys.argv[1]
    pick, out_base = 1, DEFAULT_OUT
    if "--pick" in sys.argv:
        pick = int(sys.argv[sys.argv.index("--pick") + 1])
    if "--out" in sys.argv:
        out_base = Path(sys.argv[sys.argv.index("--out") + 1])

    cards = search(keyword)
    if not cards:
        print(f"SEARCH_EMPTY: 搜索「{keyword}」无结果")
        sys.exit(2)
    print(f"搜索「{keyword}」找到 {len(cards)} 个菜谱：")
    for i, c in enumerate(cards[:8], 1):
        mark = " ← 本次选择" if i == pick else ""
        print(f"  {i}. {c['title']}{mark}")
    pick = min(pick, len(cards))
    chosen = cards[pick - 1]

    url = f"https://hanwuji.xiachufang.com/recipe/{chosen['recipe_id']}/"
    print(f"\n抓取菜谱详情: {url}")
    html_text = fetch(url, UA_MOBILE)
    r = parse_recipe(html_text, url)
    print(f"「{r['title']}」 用料 {len(r['ingredients'])} 项 | 步骤 {len(r['steps'])} 步\n")

    out_dir = out_base / f"{sanitize(keyword)}_recipe"
    out_dir.mkdir(parents=True, exist_ok=True)

    if r["cover"]:
        if download(r["cover"], out_dir / "00_成品图.jpg"):
            print("  ✓ 00_成品图.jpg")
    ok = 0
    for s in r["steps"]:
        dest = out_dir / f"step_{s['n']:02d}.jpg"
        if download(s["img"], dest):
            ok += 1
            print(f"  ✓ step_{s['n']:02d}.jpg  {s['text'][:30]}")
        time.sleep(0.3)

    (out_dir / "recipe.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "菜谱.md").write_text(to_markdown(r), encoding="utf-8")
    print(f"\nDONE: {ok}/{len(r['steps'])} 步骤图 → {out_dir}")
    print(f"DIR: {out_dir}")


if __name__ == "__main__":
    main()
