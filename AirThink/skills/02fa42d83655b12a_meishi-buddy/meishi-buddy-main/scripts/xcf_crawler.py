#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""下厨房成品图批量抓取 —— meishi-buddy skill 专用（配图补充/备选用）
用法: python3 xcf_crawler.py <菜名> [数量] [--out DIR] [--size orig|800]
输出: <out>/<菜名>/  01_菜名.jpg ... _manifest.json
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
HEADERS = {"User-Agent": UA, "Referer": "https://www.xiachufang.com/"}
SEARCH_URL = "https://www.xiachufang.com/search/?keyword={kw}&page={page}"
DEFAULT_OUT = Path("/Users/wangzhifeng/Documents/000创作/obsidian/outputs/food-content")

CARD_RE = re.compile(
    r'href="(/recipe/(\d+)/)"[^>]*>\s*<div class="cover[^"]*">\s*'
    r'<img[^>]+data-src="([^"]+)"[^>]*alt="([^"]*)"', re.S)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def download(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        if len(data) < 5000:
            return False
        dest.write_bytes(data)
        return True
    except Exception as e:
        print(f"  [跳过] {dest.name}: {e}")
        return False


def resize_url(url: str, size: str) -> str:
    if size == "orig":
        return url.split("?")[0]
    m = re.match(r"(.+\?imageView2/1/w/)(\d+)(/h/)(\d+)(.*)", url)
    if m:
        w = int(size) if size.isdigit() else 800
        h = int(w * 3 / 4)
        return f"{m.group(1)}{w}{m.group(3)}{h}{m.group(5)}"
    return url


def sanitize(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|\s]+', "_", name.strip())[:50]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    keyword = sys.argv[1]
    count, size, out_base = 8, "orig", DEFAULT_OUT
    if len(sys.argv) > 2 and sys.argv[2].isdigit():
        count = int(sys.argv[2])
    if "--size" in sys.argv:
        size = sys.argv[sys.argv.index("--size") + 1]
    if "--out" in sys.argv:
        out_base = Path(sys.argv[sys.argv.index("--out") + 1])

    out_dir = out_base / sanitize(keyword)
    out_dir.mkdir(parents=True, exist_ok=True)

    cards, seen_ids, page = [], set(), 1
    while len(cards) < count and page <= 5:
        url = SEARCH_URL.format(kw=urllib.parse.quote(keyword), page=page)
        try:
            html = fetch(url)
        except Exception as e:
            print(f"[第{page}页抓取失败] {e}")
            break
        found = CARD_RE.findall(html)
        if not found:
            break
        for href, rid, img, alt in found:
            if rid not in seen_ids and alt.strip():
                seen_ids.add(rid)
                cards.append({"recipe_id": rid, "title": alt.strip(),
                              "url": img, "page": page})
        page += 1
        time.sleep(0.8)

    print(f"关键词「{keyword}」共找到 {len(cards)} 个菜谱，下载前 {min(count, len(cards))} 张（尺寸: {size}）\n")

    manifest, ok = [], 0
    for i, c in enumerate(cards[:count], 1):
        img_url = resize_url(c["url"], size)
        fname = f"{i:02d}_{sanitize(c['title'])}.jpg"
        dest = out_dir / fname
        if download(img_url, dest):
            ok += 1
            manifest.append({**c, "file": str(dest)})
            print(f"  ✓ {fname}")
        time.sleep(0.3)

    (out_dir / "_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDONE: {ok}/{min(count, len(cards))} 张 → {out_dir}")


if __name__ == "__main__":
    main()
