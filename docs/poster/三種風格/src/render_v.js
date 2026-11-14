const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  for (const n of process.argv.slice(2)) {
    const p = await b.newPage({ viewport: { width: 2245, height: 3179 } });
    await p.goto('file://' + __dirname + `/poster_${n}.html`); await p.waitForTimeout(600);
    const m = await p.evaluate(() => [...document.querySelectorAll('.cols > div')].map((c) => Math.round(c.lastElementChild.getBoundingClientRect().bottom)));
    console.log(n, JSON.stringify(m));
    await p.screenshot({ path: `prev_${n}.png` });
    await p.close();
  }
  await b.close();
})();
