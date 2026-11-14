const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  for (const n of ['A', 'B', 'C']) {
    const p = await b.newPage({ viewport: { width: 2245, height: 3179 }, deviceScaleFactor: 1.6 });
    await p.goto('file://' + __dirname + `/poster_${n}.html`); await p.waitForTimeout(600);
    await p.screenshot({ path: `out_${n}.png` });
    await p.pdf({ path: `out_${n}.pdf`, width: '594mm', height: '841mm', printBackground: true });
    await p.close();
  }
  await b.close();
})();
