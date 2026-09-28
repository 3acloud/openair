/**
 * Clean data/results/*.md and refresh types-index taglines.
 * Maintenance only — not required at runtime.
 */
import { readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const resDir = join(root, 'data', 'results');
const indexPath = join(root, 'data', 'types-index.json');

function cleanMd(text) {
  let out = text.replace(/\r\n/g, '\n');
  // Join hard-wrapped lines (HTML export artifact)
  out = out.replace(/\n[ \t]{4,}(\S)/g, '$1');
  return out
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .split('\n')
    .map((l) => l.trimEnd())
    .join('\n')
    .trim() + '\n';
}

function extractTagline(md) {
  const m =
    md.match(/## 概览\n\n([\s\S]*?)\n\n## /) ||
    md.match(/## [^\n]+\n\n([\s\S]*?)\n\n## /);
  if (!m) return '';
  let t = m[1].replace(/\s+/g, ' ').trim();
  if (t.length > 80) t = `${t.slice(0, 77)}…`;
  return t;
}

for (const f of readdirSync(resDir).filter((x) => x.endsWith('.md'))) {
  const p = join(resDir, f);
  const cleaned = cleanMd(readFileSync(p, 'utf8'));
  writeFileSync(p, cleaned);
}

const index = JSON.parse(readFileSync(indexPath, 'utf8'));
for (const [code, data] of Object.entries(index)) {
  const md = readFileSync(join(resDir, `${code}.md`), 'utf8');
  data.tagline = extractTagline(md);
}
writeFileSync(indexPath, `${JSON.stringify(index, null, 2)}\n`);
console.log('Cleaned', readdirSync(resDir).filter((x) => x.endsWith('.md')).length, 'result files');
