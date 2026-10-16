// Renders the Open Graph image and the PNG icons from their SVG/HTML sources with Playwright (Chromium).
//   NODE_PATH=$(npm root -g) node tools/render_images.cjs
// Then build favicon.ico from the 32px PNG (see README).
const { chromium } = require('playwright');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1200, height: 630 } });
  await page.goto('file://' + path.join(__dirname, 'og.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.locator('.og').screenshot({ path: path.join(root, 'assets/img/og.png') });
  for (const [size, out] of [[180, 'assets/img/apple-touch-icon.png'], [32, 'tools/.icon-32.png'], [48, 'tools/.icon-48.png'], [16, 'tools/.icon-16.png']]) {
    const p = await browser.newPage({ viewport: { width: size, height: size } });
    await p.setContent(`<html><body style="margin:0;background:transparent"><img src="file://${path.join(root, 'assets/img/icon.svg')}" width="${size}" height="${size}" style="display:block"></body></html>`);
    await p.waitForLoadState('load');
    await p.screenshot({ path: path.join(root, out), omitBackground: true });
  }
  await browser.close();
  console.log('rendered og.png and icons');
})().catch((e) => { console.error(e); process.exit(1); });
