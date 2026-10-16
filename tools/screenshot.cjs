// Takes review screenshots of the site with Playwright (Chromium).
//   python3 -m http.server 8765 &        (from the repo root)
//   NODE_PATH=$(npm root -g) node tools/screenshot.cjs http://localhost:8765 ./shots [light|dark]
// Needs the `playwright` package and a Chromium build (PLAYWRIGHT_BROWSERS_PATH if it lives elsewhere).
const { chromium } = require('playwright');
const { mkdirSync } = require('node:fs');

const base = (process.argv[2] ?? 'http://localhost:8765').replace(/\/$/, '');
const out = process.argv[3] ?? './shots';
const scheme = process.argv[4] ?? 'dark';
mkdirSync(out, { recursive: true });

const shots = [
  ['home-en-390', '/', 390],
  ['home-en-1280', '/', 1280],
  ['home-zh-390', '/zh/', 390],
  ['home-zh-1280', '/zh/', 1280],
  ['terms-en-390', '/terms/', 390],
  ['privacy-en-390', '/privacy/', 390],
];

(async () => {
const browser = await chromium.launch();
for (const [name, path, width] of shots) {
  const ctx = await browser.newContext({ viewport: { width, height: width < 600 ? 844 : 800 }, deviceScaleFactor: width < 600 ? 2 : 1, colorScheme: scheme });
  const page = await ctx.newPage();
  const external = [];
  page.on('request', (r) => { if (!r.url().startsWith(base)) external.push(r.url()); });
  await page.goto(base + path, { waitUntil: 'networkidle' });
  // Full-page shots don't scroll, so lazy images would stay blank: load them all first.
  await page.evaluate(async () => {
    document.querySelectorAll('img[loading="lazy"]').forEach((i) => { i.loading = 'eager'; });
    await Promise.all([...document.images].map((i) => i.complete ? null : new Promise((r) => { i.onload = i.onerror = r; })));
    await document.fonts.ready;
  });
  await page.screenshot({ path: `${out}/${name}${scheme === 'light' ? '-light' : ''}.png`, fullPage: true });
  if (external.length) console.log(`${name}: external requests: ${external.join(', ')}`);
  console.log(`${name}: ok`);
  await ctx.close();
}
await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
