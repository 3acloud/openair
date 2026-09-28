/**
 * Regenerate data/decks/*.json from source question banks.
 * Maintenance only — not required at runtime.
 */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const dataDir = join(root, 'data');

function mulberry32(seed) {
  let t = seed >>> 0;
  return () => {
    t += 0x6d2b79f5;
    let r = Math.imul(t ^ (t >>> 15), 1 | t);
    r ^= r + Math.imul(r ^ (r >>> 7), 61 | r);
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
}

function shuffle(items, seed) {
  const arr = items.slice();
  const rand = mulberry32(seed);
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

function dedupeStemOrder(items) {
  const out = [];
  const seen = new Set();
  for (const q of items) {
    const k = q.text.trim();
    if (!seen.has(k)) {
      seen.add(k);
      out.push(q);
    }
  }
  return out;
}

const q93 = JSON.parse(readFileSync(join(dataDir, 'questions-93.json'), 'utf8'));
const q200 = JSON.parse(readFileSync(join(dataDir, 'questions-200.json'), 'utf8'));

const decks = [
  {
    deckId: 'quick-28',
    testCount: 28,
    source: 'questions-93.json',
    seed: 20260917,
    questions: dedupeStemOrder(shuffle(q93, 20260917)).slice(0, 28),
  },
  {
    deckId: 'standard-93',
    testCount: 93,
    source: 'questions-93.json',
    seed: 20260993,
    questions: shuffle(q93, 20260993),
  },
  {
    deckId: 'full-200',
    testCount: 200,
    source: 'questions-200.json',
    seed: 20260200,
    questions: shuffle(q200, 20260200),
  },
];

const outDir = join(dataDir, 'decks');
mkdirSync(outDir, { recursive: true });
for (const deck of decks) {
  writeFileSync(join(outDir, `${deck.deckId}.json`), JSON.stringify(deck, null, 2));
}
console.log('Built decks:', decks.map((d) => `${d.deckId}(${d.questions.length})`).join(', '));
