#!/usr/bin/env node
// 给设计小样截图、录屏和做基本检查。只依赖 Node 22+ 和本机的 Chrome / Chromium / Edge。
// 用法见 references/tools.md；`node shoot.mjs --help` 打印同样的说明。
import { spawn, spawnSync } from "node:child_process";
import { createServer } from "node:http";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, rmSync, statSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { tmpdir } from "node:os";
import { basename, dirname, extname, isAbsolute, join, relative, resolve, sep } from "node:path";

const HELP = `用法：node shoot.mjs <页面地址或文件> [选项]

  --out <目录>          输出目录，默认 ./shots
  --size <宽x高,...>    视口，默认 390x844；可写多个，例如 390x844,1280x900
  --states <a,b,...>    依次用 ?state=<名字> 打开并各截一张
  --param <名字>        状态参数名，默认 state
  --zoom <倍数>         设备像素比，默认 1；2 即 200% 截图
  --full                截整页，默认只截视口
  --mask                另截一份遮掉全部文字的版本
  --sheet               把所有状态拼成一张并排图（配合 --mask 再拼一张遮字版）
  --steps "<动作>"      截图前先执行的动作，用分号分隔：
                        click <选择器> | hover <选择器> | drag <选择器> <dx> <dy>
                        选择器里有空格时加引号：click ".nav .item"
                        type <选择器> <文字> | key <按键> | scroll <dy> | wait <毫秒>
  --record              录下 --steps 的执行过程，输出 record.mp4 和开始、中间、结束三帧
  --entry               配合 --record：先开始录再打开页面，录下首次进入的出场
  --hold <毫秒>         录屏时动作结束后再录多久，默认 1200
  --motion              探测动效：首次进入、--steps 动作、首屏滚动、从头滚到底里
                        有没有动画、幅度多大，没有或太小记为问题；首屏滚动
                        1.5 屏内几层在变只作报告，供选了首屏景深的页面核对；
                        页面本身不能滚动时（单屏 App）跳过滚动检查
  --wait <毫秒>         页面加载后等多久再截，默认 400

每张图都会检查控制台错误、横向溢出和加载失败的图片，结果写进 report.json。`;

const args = process.argv.slice(2);
if (!args.length || args.includes("--help") || args.includes("-h")) {
  console.log(HELP);
  process.exit(args.length ? 0 : 1);
}
if (typeof WebSocket !== "function") fail("需要 Node 22 或更新的版本。");

const opt = { out: "shots", size: "390x844", param: "state", zoom: "1", hold: "1200", wait: "400" };
const options = [...HELP.matchAll(/^  (--\S+)/gm)].map((m) => m[1]);
const flags = new Set();
let target = null;
for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if (a === "--force") continue;
  if (["--full", "--mask", "--sheet", "--record", "--motion", "--entry"].includes(a)) flags.add(a.slice(2));
  else if (a.startsWith("--")) {
    if (!options.includes(a)) fail(`不认识的选项 ${a}\n可用选项：${options.join(" ")}`);
    if (i + 1 >= args.length || args[i + 1].startsWith("--")) fail(`${a} 需要一个值`);
    opt[a.slice(2)] = args[++i];
  } else target = a;
}
if (!target) fail("缺少页面地址或文件。");

const sizes = opt.size.split(",").map((s) => {
  const m = s.trim().match(/^(\d+)x(\d+)$/);
  if (!m) fail(`尺寸写成 宽x高，例如 390x844：${s}`);
  return { w: +m[1], h: +m[2] };
});
const states = opt.states ? opt.states.split(",").map((s) => s.trim()).filter(Boolean) : [null];
const stateIds = states.map((s, i) => !s ? "page" : /^[A-Za-z0-9_-]{1,80}$/.test(s) ? s :
  `state-${i + 1}-${createHash("sha256").update(s).digest("hex").slice(0, 12)}`);
const zoom = Number(opt.zoom) || 1;
const out = resolve(opt.out);
mkdirSync(out, { recursive: true });

function fail(message) {
  console.error(`shoot：${message}`);
  process.exit(1);
}

// ---------- 本地文件用一个只监听本机的静态服务器打开，模块脚本和 fetch 才能正常工作 ----------
const MIME = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
  ".webp": "image/webp", ".gif": "image/gif", ".avif": "image/avif", ".woff2": "font/woff2", ".woff": "font/woff",
  ".ttf": "font/ttf", ".otf": "font/otf", ".mp4": "video/mp4", ".webm": "video/webm",
};
let server = null;
async function resolveTarget(t) {
  if (/^https?:\/\//.test(t)) return t;
  const file = resolve(t);
  if (!existsSync(file)) fail(`找不到文件：${t}`);
  const root = realpathSync(statSync(file).isDirectory() ? file : dirname(file));
  const page = statSync(file).isDirectory() ? "index.html" : basename(file);
  server = createServer((req, res) => {
    try {
      const path = decodeURIComponent(new URL(req.url, "http://x").pathname);
      const local = realpathSync(resolve(join(root, path)));
      const fromRoot = relative(root, local);
      if (fromRoot === ".." || fromRoot.startsWith(`..${sep}`) || isAbsolute(fromRoot) || !statSync(local).isFile()) {
        res.writeHead(404).end();
        return;
      }
      res.writeHead(200, { "Content-Type": MIME[extname(local).toLowerCase()] || "application/octet-stream" });
      res.end(readFileSync(local));
    } catch {
      res.writeHead(404).end();
    }
  });
  await new Promise((ok) => server.listen(0, "127.0.0.1", ok));
  return `http://127.0.0.1:${server.address().port}/${encodeURIComponent(page)}`;
}

// ---------- 启动一个独立的临时浏览器，不碰用户自己的浏览器数据 ----------
function findChrome() {
  const env = process.env.CHROME_PATH;
  if (env && existsSync(env)) return env;
  const candidates = {
    darwin: [
      "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
      "/Applications/Chromium.app/Contents/MacOS/Chromium",
      "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ],
    win32: [
      `${process.env["PROGRAMFILES"]}\\Google\\Chrome\\Application\\chrome.exe`,
      `${process.env["PROGRAMFILES(X86)"]}\\Google\\Chrome\\Application\\chrome.exe`,
      `${process.env["PROGRAMFILES(X86)"]}\\Microsoft\\Edge\\Application\\msedge.exe`,
    ],
  }[process.platform];
  for (const c of candidates || []) if (c && existsSync(c)) return c;
  for (const name of ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge"]) {
    const r = spawnSync("which", [name], { encoding: "utf8" });
    if (r.status === 0 && r.stdout.trim()) return r.stdout.trim();
  }
  fail("没找到 Chrome、Chromium 或 Edge；安装其一，或用环境变量 CHROME_PATH 指定路径。");
}

const chromePath = findChrome();
const profile = mkdtempSync(join(tmpdir(), "oil-shoot-"));
const chrome = spawn(chromePath, [
  "--headless=new", "--enable-unsafe-swiftshader", "--remote-debugging-port=0", `--user-data-dir=${profile}`, "--no-first-run",
  "--no-default-browser-check", "--hide-scrollbars", "--mute-audio", "--disable-extensions", "about:blank",
], { stdio: ["ignore", "ignore", "pipe"] });

let cleaning;
function cleanup() {
  return cleaning ||= (async () => {
    if (chrome.exitCode === null && chrome.signalCode === null) {
      await new Promise((ok) => {
        const timer = setTimeout(() => { chrome.kill("SIGKILL"); ok(); }, 3000);
        chrome.once("close", () => { clearTimeout(timer); ok(); });
        chrome.kill();
      });
    }
    server?.close();
    rmSync(profile, { recursive: true, force: true });
  })();
}
// Early startup failures still use process.exit; its handlers must clean up synchronously.
process.on("exit", () => {
  try { chrome.kill(); } catch {}
  try { server?.close(); } catch {}
  try { rmSync(profile, { recursive: true, force: true }); } catch {}
});
process.on("SIGINT", async () => { await cleanup(); process.exit(130); });
process.on("SIGTERM", async () => { await cleanup(); process.exit(143); });
chrome.on("error", (error) => fail(`浏览器启动失败：${error.message}`));

const wsUrl = await new Promise((ok) => {
  let buf = "";
  const timer = setTimeout(() => fail("浏览器 15 秒内没有启动。"), 15000);
  chrome.stderr.on("data", (d) => {
    buf += d;
    const m = buf.match(/DevTools listening on (ws:\/\/\S+)/);
    if (m) { clearTimeout(timer); ok(m[1]); }
  });
});

// ---------- Chrome DevTools 协议 ----------
const ws = new WebSocket(wsUrl);
await new Promise((ok, no) => { ws.onopen = ok; ws.onerror = () => no(new Error("连接浏览器失败")); });
let seq = 0;
const pending = new Map();
const listeners = [];
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.id && pending.has(msg.id)) {
    const { ok, no } = pending.get(msg.id);
    pending.delete(msg.id);
    msg.error ? no(new Error(msg.error.message)) : ok(msg.result);
  } else if (msg.method) listeners.forEach((fn) => fn(msg));
};
const send = (method, params = {}, sessionId) => new Promise((ok, no) => {
  const id = ++seq;
  pending.set(id, { ok, no });
  ws.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }));
});

const { targetId } = await send("Target.createTarget", { url: "about:blank" });
const { sessionId } = await send("Target.attachToTarget", { targetId, flatten: true });
const cdp = (method, params) => send(method, params, sessionId);
await cdp("Page.enable");
await cdp("Runtime.enable");
await cdp("Log.enable");
// 记下创建失败或丢失的 WebGL 上下文：截图照样成功，画布却是空的。
// 先试 webgl2、失败后退回 webgl 的页面不算失败，只看最后有没有拿到。
await cdp("Page.addScriptToEvaluateOnNewDocument", { source: `(() => {
  const gl = window.__oilWebgl = { failed: [], ok: [], lost: 0 };
  const get = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function (type, ...rest) {
    const ctx = get.call(this, type, ...rest);
    if (/^(webgl2?|experimental-webgl)$/.test(type)) {
      if (!ctx) gl.failed.push(this);
      else if (!gl.ok.includes(this)) { gl.ok.push(this); this.addEventListener("webglcontextlost", () => gl.lost++); }
    }
    return ctx;
  };
})()` });

let problems = [];
listeners.push((m) => {
  if (m.sessionId !== sessionId) return;
  if (m.method === "Runtime.exceptionThrown") problems.push(`脚本错误：${m.params.exceptionDetails?.exception?.description?.split("\n")[0] || m.params.exceptionDetails?.text}`);
  if (m.method === "Runtime.consoleAPICalled" && m.params.type === "error") problems.push(`控制台错误：${m.params.args.map((a) => a.value ?? a.description ?? "").join(" ").slice(0, 200)}`);
  if (m.method === "Log.entryAdded" && m.params.entry.level === "error") problems.push(`加载错误：${m.params.entry.text.slice(0, 200)} ${m.params.entry.url || ""}`.trim());
});

const evaluate = async (expression) => {
  const r = await cdp("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
  return r.result.value;
};
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function setViewport(w, h, scale) {
  await cdp("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: scale, mobile: w < 600 });
  await cdp("Emulation.setTouchEmulationEnabled", { enabled: w < 600 });
}

async function open(url) {
  const loaded = new Promise((ok) => {
    const fn = (m) => { if (m.sessionId === sessionId && m.method === "Page.loadEventFired") { listeners.splice(listeners.indexOf(fn), 1); ok(); } };
    listeners.push(fn);
  });
  const nav = await cdp("Page.navigate", { url });
  if (nav.errorText) throw new Error(`打不开 ${url}：${nav.errorText}`);
  await Promise.race([loaded, sleep(15000)]);
  await evaluate(`document.fonts ? document.fonts.ready.then(() => true) : true`);
  await sleep(Number(opt.wait));
}

async function check() {
  const found = await evaluate(`(() => {
    const out = [];
    const doc = document.documentElement;
    if (doc.scrollWidth > innerWidth + 1) out.push("横向溢出：页面宽 " + doc.scrollWidth + "px，视口 " + innerWidth + "px");
    for (const img of document.images) if (img.complete && img.naturalWidth === 0) out.push("图片没加载出来：" + (img.getAttribute("src") || "").slice(0, 120));
    const gl = window.__oilWebgl;
    if (gl) {
      const blank = new Set(gl.failed.filter((c) => !gl.ok.includes(c))).size;
      if (blank) out.push("WebGL：" + blank + " 个画布没能创建绘图上下文，截图里是空的");
      if (gl.lost) out.push("WebGL：绘图上下文丢失 " + gl.lost + " 次");
    }
    return out;
  })()`);
  return [...problems, ...found];
}

async function screenshot(file, full) {
  let clip;
  if (full) {
    const { contentSize } = await cdp("Page.getLayoutMetrics");
    clip = { x: 0, y: 0, width: Math.ceil(contentSize.width), height: Math.ceil(contentSize.height), scale: 1 };
  }
  const { data } = await cdp("Page.captureScreenshot", { format: "png", captureBeyondViewport: !!full, ...(clip ? { clip } : {}) });
  writeFileSync(file, Buffer.from(data, "base64"));
  return file;
}

// Keep color intact: SVG icons and CSS decorations may use currentColor.
const MASK_CSS = `*,*::before,*::after{text-shadow:none!important;-webkit-text-fill-color:transparent!important;caret-color:transparent!important}
::placeholder{color:transparent!important}svg text,svg tspan{fill:transparent!important;stroke:transparent!important}`;
const mask = () => evaluate(`(() => { const s = document.createElement("style"); s.id = "oil-mask"; s.textContent = ${JSON.stringify(MASK_CSS)}; document.head.append(s); return true; })()`);

// ---------- 动作 ----------
function tokenize(text) {
  return [...text.matchAll(/"([^"]*)"|'([^']*)'|(\S+)/g)].map((m) => m[1] ?? m[2] ?? m[3]);
}
const KEYS = { ArrowUp: 38, ArrowDown: 40, ArrowLeft: 37, ArrowRight: 39, Enter: 13, Escape: 27, Tab: 9, " ": 32, Space: 32, Home: 36, End: 35, PageUp: 33, PageDown: 34, Backspace: 8 };
async function center(selector) {
  const box = await evaluate(`(() => { const el = document.querySelector(${JSON.stringify(selector)}); if (!el) return null; el.scrollIntoView({ block: "center", inline: "center" }); const r = el.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; })()`);
  if (!box) throw new Error(`找不到元素：${selector}`);
  return box;
}
const mouse = (type, x, y, extra = {}) => cdp("Input.dispatchMouseEvent", { type, x, y, button: "left", pointerType: "mouse", ...extra });
async function runSteps(text) {
  for (const raw of (text || "").split(";").map((s) => s.trim()).filter(Boolean)) {
    const [verb, ...rest] = tokenize(raw);
    const arity = { click: 1, hover: 1, drag: 3 }[verb];
    if (arity && rest.length !== arity) throw new Error(`动作参数不对：${raw}。选择器里有空格时要加引号，例如 ${verb} ".nav .item"${verb === "drag" ? " 0 -80" : ""}`);
    if (verb === "wait") await sleep(Number(rest[0]) || 0);
    else if (verb === "click") { const p = await center(rest[0]); await mouse("mouseMoved", p.x, p.y); await mouse("mousePressed", p.x, p.y, { clickCount: 1 }); await mouse("mouseReleased", p.x, p.y, { clickCount: 1 }); await sleep(120); }
    else if (verb === "hover") { const p = await center(rest[0]); await mouse("mouseMoved", p.x, p.y); await sleep(200); }
    else if (verb === "drag") {
      const p = await center(rest[0]); const dx = Number(rest[1]) || 0; const dy = Number(rest[2]) || 0;
      await mouse("mouseMoved", p.x, p.y); await mouse("mousePressed", p.x, p.y, { clickCount: 1, buttons: 1 });
      for (let i = 1; i <= 24; i++) { await mouse("mouseMoved", p.x + (dx * i) / 24, p.y + (dy * i) / 24, { buttons: 1 }); await sleep(16); }
      await mouse("mouseReleased", p.x + dx, p.y + dy, { clickCount: 1 }); await sleep(150);
    } else if (verb === "type") {
      await evaluate(`(() => { const el = document.querySelector(${JSON.stringify(rest[0])}); if (!el) throw new Error(${JSON.stringify("找不到元素：" + rest[0])}); el.focus(); return true; })()`);
      await cdp("Input.insertText", { text: rest.slice(1).join(" ") }); await sleep(120);
    } else if (verb === "key") {
      const key = rest[0] === "Space" ? " " : rest[0]; const code = KEYS[rest[0]] ?? key.toUpperCase().charCodeAt(0);
      await cdp("Input.dispatchKeyEvent", { type: "keyDown", key, code: rest[0], windowsVirtualKeyCode: code });
      await cdp("Input.dispatchKeyEvent", { type: "keyUp", key, code: rest[0], windowsVirtualKeyCode: code }); await sleep(80);
    } else if (verb === "scroll") { await evaluate(`scrollBy(0, ${Number(rest[0]) || 0}), true`); await sleep(200); }
    else throw new Error(`不认识的动作：${raw}`);
  }
}

// ---------- 并排图：用同一个浏览器把截图排成一张 ----------
async function sheet(items, file, w, h) {
  const cell = Math.min(w, 420);
  const escapeHtml = (text) => String(text).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const figures = items.map(({ path, label }) =>
    `<figure><img src="data:image/png;base64,${readFileSync(path).toString("base64")}"><figcaption>${escapeHtml(label)}</figcaption></figure>`).join("");
  const html = `<!doctype html><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><style>body{margin:0;padding:32px;background:#ececea;font:13px -apple-system,"PingFang SC",sans-serif;color:#555}
main{display:flex;gap:24px;align-items:flex-start}figure{margin:0;width:${cell}px}img{width:100%;display:block;border-radius:12px;box-shadow:0 1px 3px #0002}
figcaption{margin-top:10px}</style><main>${figures}</main>`;
  const tmp = join(profile, "sheet.html");
  writeFileSync(tmp, html);
  const width = items.length * cell + (items.length - 1) * 24 + 64;
  await setViewport(width, Math.round((cell * h) / w) + 120, 1);
  await open(`file://${tmp}`);
  return screenshot(file, true);
}

// ---------- 录屏 ----------
async function record(url, w, h) {
  const frames = [];
  const dir = join(out, "frames");
  mkdirSync(dir, { recursive: true });
  const onFrame = (m) => {
    if (m.sessionId !== sessionId || m.method !== "Page.screencastFrame") return;
    const name = join(dir, `f${String(frames.length).padStart(4, "0")}.jpg`);
    writeFileSync(name, Buffer.from(m.params.data, "base64"));
    frames.push({ name, t: m.params.metadata.timestamp });
    cdp("Page.screencastFrameAck", { sessionId: m.params.sessionId }).catch(() => {});
  };
  await setViewport(w, h, zoom);
  const entry = flags.has("entry");
  if (!entry) await open(url);
  listeners.push(onFrame);
  await cdp("Page.startScreencast", { format: "jpeg", quality: 88, everyNthFrame: 1 });
  if (entry) {
    await open(url);
    // 丢掉页面第一次有内容之前的空白帧，开始帧就是出场的起点
    const painted = await evaluate(`(() => { const p = performance.getEntriesByName("first-contentful-paint")[0] || performance.getEntriesByType("paint")[0]; return p ? (performance.timeOrigin + p.startTime) / 1000 : 0; })()`);
    if (painted) { const firstPainted = frames.findIndex((f) => f.t >= painted - 0.02); if (firstPainted > 0) frames.splice(0, firstPainted); }
  } else await sleep(500);
  await runSteps(opt.steps);
  await sleep(Number(opt.hold));
  const finished = Date.now() / 1000;
  const issues = await check();
  await cdp("Page.stopScreencast");
  listeners.splice(listeners.indexOf(onFrame), 1);
  if (!frames.length) throw new Error("录屏没有拿到画面");
  const pick = { start: frames[0], mid: frames[Math.floor(frames.length / 2)], end: frames[frames.length - 1] };
  for (const [k, f] of Object.entries(pick)) writeFileSync(join(out, `motion-${k}.jpg`), readFileSync(f.name));
  const ffmpeg = spawnSync("ffmpeg", ["-version"]).status === 0;
  if (!ffmpeg) return { issues, message: `录屏：没装 ffmpeg，只留了 ${frames.length} 帧和 motion-start/mid/end.jpg` };
  // Generated basenames are safe for concat's quoting, even when --out contains an apostrophe.
  // Keep the final still frame through the end of --hold; screencasts only emit changed frames.
  const list = frames.map((f, i) => `file '${basename(f.name)}'\nduration ${Math.max(0.016, ((frames[i + 1]?.t ?? finished) - f.t)).toFixed(3)}`).join("\n") + `\nfile '${basename(frames.at(-1).name)}'\n`;
  writeFileSync(join(dir, "list.txt"), list);
  const r = spawnSync("ffmpeg", ["-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", join(dir, "list.txt"),
    "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,fps=30", "-pix_fmt", "yuv420p", join(out, "record.mp4")], { encoding: "utf8" });
  if (r.status !== 0) return { issues, message: `录屏：ffmpeg 合成失败（${r.stderr.trim().split("\n").pop()}），帧留在 frames/` };
  rmSync(dir, { recursive: true, force: true });
  return { issues, message: `录屏：record.mp4（${(finished - frames[0].t).toFixed(1)} 秒）和 motion-start/mid/end.jpg` };
}


// ---------- 动效探测 ----------
// Runs before page scripts: records which elements animate in each phase and how far they move.
const MOTION_PROBE = `(() => {
  if (window.__oilMotion) return;
  const tracked = new Map();
  let phase = "load";
  const seen = new Set();
  function touch(el, source) {
    if (!(el instanceof Element) || el.id === "oil-mask") return;
    let t = tracked.get(el);
    if (!t) { if (tracked.size >= 400) return; t = { phases: {} }; tracked.set(el, t); }
    let p = t.phases[phase];
    if (!p) p = t.phases[phase] = { first: null, last: null, frames: 0, move: 0, size: 0, opacity: 0, sources: new Set() };
    p.sources.add(source);
    if (source.startsWith("js:")) t.lastJs = performance.now();
  }
  addEventListener("animationstart", (e) => touch(e.target, "css:" + e.animationName), true);
  addEventListener("transitionrun", (e) => touch(e.target, "transition:" + e.propertyName), true);
  new MutationObserver((list) => { for (const m of list) touch(m.target, "js:" + m.attributeName); })
    .observe(document, { subtree: true, attributes: true, attributeFilter: ["style", "transform", "viewBox", "d", "x", "y", "cx", "cy", "r", "points", "opacity", "stroke-dashoffset"] });
  // 首屏阶段按视口坐标量：被固定住的舞台不算在动，舞台里的层次变化才算。
  function read(el) {
    const r = el.getBoundingClientRect();
    const page = phase === "hero" ? 0 : 1;
    return { x: r.left + scrollX * page, y: r.top + scrollY * page, w: r.width, h: r.height, o: +getComputedStyle(el).opacity };
  }
  function sample() {
    if (document.getAnimations) for (const a of document.getAnimations()) {
      if (a.playState !== "running" || !a.effect || !a.effect.target) continue;
      const tl = a.timeline && a.timeline.constructor && a.timeline.constructor.name;
      const scrollLinked = tl === "ScrollTimeline" || tl === "ViewTimeline";
      if (scrollLinked) touch(a.effect.target, "scroll-timeline:" + (a.animationName || "animation"));
      else if (!seen.has(a)) { seen.add(a); if (!a.animationName && !a.transitionProperty) touch(a.effect.target, "waapi"); }
    }
    for (const [el, t] of tracked) {
      const p = t.phases[phase];
      if (!p || !el.isConnected) continue;
      const now = read(el);
      if (!p.first) { p.first = p.last = now; continue; }
      const l = p.last;
      if (Math.abs(now.x - l.x) + Math.abs(now.y - l.y) + Math.abs(now.w - l.w) + Math.abs(now.h - l.h) > 0.1 || Math.abs(now.o - l.o) > 0.005) p.frames++;
      p.last = now;
      p.move = Math.max(p.move, Math.hypot(now.x - p.first.x, now.y - p.first.y));
      p.size = Math.max(p.size, Math.abs(now.w - p.first.w) / Math.max(1, p.first.w), Math.abs(now.h - p.first.h) / Math.max(1, p.first.h));
      p.opacity = Math.max(p.opacity, Math.abs(now.o - p.first.o));
    }
    requestAnimationFrame(sample);
  }
  requestAnimationFrame(sample);
  window.__oilMotion = {
    setPhase(next) { phase = next; },
    summary(name) {
      const items = [];
      for (const [el, t] of tracked) {
        const p = t.phases[name];
        if (!p) continue;
        const label = el.tagName.toLowerCase() + (el.id ? "#" + el.id : "") + (typeof el.className === "string" && el.className.trim() ? "." + el.className.trim().split(/\\s+/).slice(0, 2).join(".") : "");
        const infinite = el.getAnimations ? el.getAnimations().some((a) => a.effect && a.effect.getTiming && a.effect.getTiming().iterations === Infinity) : false;
        const loop = infinite || (t.lastJs && performance.now() - t.lastJs < 250);
        if (p.frames < 3) continue; // one-off jumps are state writes, not motion
        items.push({ el: label, move: Math.round(p.move), size: +p.size.toFixed(3), opacity: +p.opacity.toFixed(2), loop: !!loop, sources: [...p.sources].slice(0, 3) });
      }
      const visible = items.filter((i) => ((name !== "scroll" && name !== "hero") || !i.loop) && (i.move >= 1 || i.size >= 0.005 || i.opacity >= 0.05 || i.sources.some((s) => s.startsWith("scroll-timeline"))));
      visible.sort((a, b) => (b.move + b.size * 400 + b.opacity * 40) - (a.move + a.size * 400 + a.opacity * 40));
      return {
        elements: visible.length,
        loops: visible.filter((i) => i.loop).length,
        maxMove: Math.max(0, ...visible.map((i) => i.move)),
        maxSize: Math.max(0, ...visible.map((i) => i.size)),
        maxOpacity: Math.max(0, ...visible.map((i) => i.opacity)),
        top: visible.slice(0, 8),
      };
    },
  };
})()`;

async function probeMotion(url, w, h) {
  const { identifier } = await cdp("Page.addScriptToEvaluateOnNewDocument", { source: MOTION_PROBE });
  problems = [];
  await setViewport(w, h, 1);
  await open(url);
  await sleep(1200);
  const phases = { load: await evaluate(`__oilMotion.summary("load")`) };
  if (opt.steps) {
    await evaluate(`__oilMotion.setPhase("steps"), true`);
    await runSteps(opt.steps);
    await sleep(900);
    phases.steps = await evaluate(`__oilMotion.summary("steps")`);
  }
  await evaluate(`(scrollTo(0, 0), __oilMotion.setPhase("hero"), true)`);
  await sleep(150);
  const height = await evaluate(`document.documentElement.scrollHeight - innerHeight`);
  const scrollable = height > 4;
  const heroEnd = Math.min(height, Math.round(h * 1.5));
  for (let y = 0; y <= heroEnd; y += Math.round(h / 10)) { await evaluate(`scrollTo(0, ${y}), true`); await sleep(70); }
  await sleep(400);
  phases.hero = await evaluate(`__oilMotion.summary("hero")`);
  await evaluate(`(__oilMotion.setPhase("scroll"), true)`);
  for (let y = heroEnd; y < height; y += Math.round(h / 4)) { await evaluate(`scrollTo(0, ${y}), true`); await sleep(90); }
  await evaluate(`scrollTo(0, ${height}), true`);
  await sleep(600);
  phases.scroll = await evaluate(`__oilMotion.summary("scroll")`);
  await cdp("Page.removeScriptToEvaluateOnNewDocument", { identifier });

  const issues = [];
  const names = { load: "首次进入", steps: "--steps 动作", hero: "首屏滚动", scroll: "从头滚到底" };
  const weak = (p) => p.maxMove < 4 && p.maxSize < 0.02 && p.maxOpacity < 0.3;
  for (const [k, p] of Object.entries(phases)) {
    // 首屏景深是可选手法：只报告层数和幅度，供选了它的页面核对，不记为问题。
    if (k === "hero") {
      p.layers = p.top.filter((i) => i.size >= 0.05 || i.move >= h * 0.05).length;
      continue;
    }
    if (k === "scroll") {
      p.scrollable = scrollable;
      if (!p.elements && scrollable) issues.push("滚动：没有检测到随滚动出现的变化；落地页、品牌页、发布页和展览页需要一段滚动叙事");
      continue;
    }
    if (!p.elements) issues.push(`${names[k]}：没有检测到动画`);
    else if (p.loops === p.elements) issues.push(`${names[k]}：只有持续循环的动画，没有一次性的${k === "load" ? "出场" : "反馈"}`);
    else if (weak(p)) issues.push(`${names[k]}：动画幅度太小，看不出来（最大位移 ${p.maxMove}px，尺寸变化 ${(p.maxSize * 100).toFixed(1)}%，透明度变化 ${p.maxOpacity}）`);
  }
  const brief = (k, p) => k === "scroll" && !p.scrollable ? "页面不滚动，跳过滚动检查" : k === "hero" ? `首屏滚动 ${p.layers} 层在变，最大缩放 ${(p.maxSize * 100).toFixed(1)}%，最大位移 ${p.maxMove}px`
    : `${names[k]} ${p.elements} 个元素在动，最大位移 ${p.maxMove}px，透明度变化 ${p.maxOpacity}`;
  return { phases, issues: [...problems, ...issues], message: "动效探测：" + Object.entries(phases).map(([k, p]) => brief(k, p)).join("；") };
}

// ---------- 主流程 ----------
const base = await resolveTarget(target);
const withState = (s) => {
  if (!s) return base;
  const u = new URL(base);
  u.searchParams.set(opt.param, s);
  return u.toString();
};
const report = [];
const lines = [];
try {
  if (flags.has("motion")) {
    const result = await probeMotion(withState(states[0]), sizes[0].w, sizes[0].h);
    lines.push(result.message + (result.issues.length ? "  ⚠ " + result.issues.join("；") : ""));
    report.push({ file: "motion-probe", state: states[0], size: `${sizes[0].w}x${sizes[0].h}`, zoom: 1, motion: result.phases, issues: result.issues });
  }
  if (flags.has("record")) {
    const result = await record(withState(states[0]), sizes[0].w, sizes[0].h);
    lines.push(result.message);
    report.push({ file: "motion-end.jpg", state: states[0], size: `${sizes[0].w}x${sizes[0].h}`, zoom, issues: result.issues });
  } else {
    for (const { w, h } of sizes) {
      const shots = [], masked = [];
      for (const [stateIndex, s] of states.entries()) {
        problems = [];
        await setViewport(w, h, zoom);
        await open(withState(s));
        if (opt.steps) await runSteps(opt.steps);
        const name = [stateIds[stateIndex], sizes.length > 1 ? `${w}x${h}` : "", zoom !== 1 ? `@${zoom}x` : ""].filter(Boolean).join("-");
        const file = await screenshot(join(out, `${name}.png`), flags.has("full"));
        const issues = await check();
        report.push({ file: basename(file), state: s, size: `${w}x${h}`, zoom, issues });
        shots.push({ path: file, label: s || "page" });
        if (flags.has("mask")) {
          await mask();
          await sleep(60);
          masked.push({ path: await screenshot(join(out, `${name}-masked.png`), flags.has("full")), label: s || "page" });
        }
        lines.push(`${basename(file)}${issues.length ? "  ⚠ " + issues.join("；") : ""}`);
      }
      if (flags.has("sheet") && shots.length > 1) {
        const suffix = sizes.length > 1 ? `-${w}x${h}` : "";
        lines.push(basename(await sheet(shots, join(out, `sheet${suffix}.png`), w, h)));
        if (masked.length) lines.push(basename(await sheet(masked, join(out, `sheet${suffix}-masked.png`), w, h)));
      }
    }
  }
  writeFileSync(join(out, "report.json"), JSON.stringify(report, null, 2));
} catch (error) {
  console.error(`shoot：${error.message}`);
  process.exitCode = 1;
}
console.log(`输出目录：${out}`);
for (const l of lines) console.log(`- ${l}`);
const total = report.reduce((n, r) => n + r.issues.length, 0);
if (report.length) console.log(total ? `发现 ${total} 个问题，详见 report.json` : `检查通过：没有控制台错误、横向溢出或加载失败的图片${flags.has("motion") ? "，三段动效都检测到了" : ""}`);
ws.close();
await cleanup();
process.exit(process.exitCode || 0);
