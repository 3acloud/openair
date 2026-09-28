#!/usr/bin/env node
// 把 hero.html 渲染成 PNG。横版画布比 lieflat-xhs-cover 的竖版脚本宽，
// 所以单独走一份 viewport 配置，避免元素截图被裁掉。
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

const arg = (n, d) => {
  const i = process.argv.indexOf(`--${n}`);
  return i === -1 ? d : process.argv[i + 1];
};

const html = arg("html", "hero.html");
const out = arg("out", "gongwen-dna-hero-zh.jpg");
// 头图 1600px 宽，对 GitHub 约 850px 的正文栏已经是 2 倍图，scale 再翻倍
// 只把体积从 155KB 推到 605KB，肉眼无差别，所以默认 1。
const scale = Number(arg("scale", "1"));
const width = Number(arg("width", "1760"));
const height = Number(arg("height", "900"));

const { chromium } = await import(
  arg("playwright", "/opt/homebrew/lib/node_modules/playwright/index.mjs")
);

const browser = await chromium.launch({ headless: true, args: ["--disable-gpu"] });
const page = await browser.newPage({
  viewport: { width, height },
  deviceScaleFactor: scale,
});
await page.goto(pathToFileURL(resolve(html)).href, { waitUntil: "load" });
await page.evaluate(() => document.fonts?.ready);
await page.waitForTimeout(600); // 让雨滴画几帧再截

const scene = page.locator(".scene").first();
await scene.waitFor({ state: "visible", timeout: 5000 });
// 纸纹是满版噪点，PNG 压不动（1.4MB）；这版式本质是一张纸的照片，
// 走 JPEG q92 体积降到 ~170KB，且不像调色板量化那样吃掉 logo 的绿。
const jpeg = /\.jpe?g$/i.test(out);
await scene.screenshot({
  path: resolve(out),
  ...(jpeg ? { type: "jpeg", quality: 92 } : {}),
});

const m = await page.evaluate(() => {
  const s = document.querySelector(".scene");
  const a = s.querySelector(".article");
  const r = s.getBoundingClientRect();
  return {
    css: [Math.round(r.width), Math.round(r.height)],
    scroll: a.scrollHeight,
    client: a.clientHeight,
    overflowX: a.scrollWidth > a.clientWidth ? a.scrollWidth - a.clientWidth : 0,
  };
});
await browser.close();

const bad = m.scroll > m.client || m.overflowX > 0;
console.log(
  `${out}  ${m.css[0]}x${m.css[1]} css → ${m.css[0] * scale}x${m.css[1] * scale} px  ` +
    `scroll ${m.scroll}/${m.client}  ${bad ? `OVERFLOW y+${m.scroll - m.client} x+${m.overflowX}` : "ok"}`
);
process.exit(bad ? 1 : 0);
