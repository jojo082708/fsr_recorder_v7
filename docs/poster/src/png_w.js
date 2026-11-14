const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 2245, height: 3179 }, deviceScaleFactor: 1.6 });
  await p.goto('file://' + __dirname + '/poster_w.html'); await p.waitForTimeout(800); await p.screenshot({ path: 'poster_w.png' }); await b.close(); })();
