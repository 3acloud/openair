# assets

README 用图。版式与配色沿用 `gongwen-dna-xhs-rain` 的 rain-note 模板（红头文件正红
`#e2000f` + 中性纸底 + 雨丝纹理），横版重排。

| 文件 | 用途 |
|---|---|
| `gongwen-dna-hero-zh.jpg` | README 顶部头图，1200×560 |
| `made-on-moxt.jpg` | 页脚 Made on Moxt 徽章，440×104 |
| `hero.html` / `badge.html` | 两张图的版式源文件 |
| `rain.js` | 雨丝动画，取自 rain-note 模板 |
| `shoot.mjs` | 截图脚本 |

## 重新生成

```bash
node shoot.mjs --width 1400 --height 760          # 头图
node shoot.mjs --html badge.html --out made-on-moxt.jpg \
  --width 640 --height 260 --scale 2              # 徽章
```

`--width/--height` 是浏览器窗口，要比画布本身大一圈，画布尺寸由 `hero.html`
里 `.scene` 的 width/height 决定。

依赖 Playwright（`/opt/homebrew/lib/node_modules/playwright`）。脚本会报告
`scroll/client` 两个数字，相等即表示内容没有溢出画布。

Moxt logo 首次运行时从 moxt.ai 官方静态资源拉取并缓存为 `.moxt-logo.png`，
该缓存不入库（见 `.gitignore`）；logo 是 Moxt 的商标，所以只引用不随仓库分发。

## 为什么是 JPEG 而不是 PNG

纸纹是满版噪点，PNG 压不下去（这个尺寸要 1MB 上下）。调色板量化虽然能压到 700KB，
但 Pillow 按像素数量分配调色板，logo 那 598 个绿点一定会被丢掉——实测绿色会变灰、
字母变红。这版式本质是一张纸的照片，走 JPEG q92 体积 ~160KB，配色和 logo 都完好。
