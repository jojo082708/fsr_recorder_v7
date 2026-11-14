const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 2245, height: 3179 } });
  await p.goto('file://' + __dirname + '/poster.html'); await p.waitForTimeout(800);
  const m = await p.evaluate(() => { const pg = document.querySelector('.page'); const cols = [...document.querySelectorAll('.cols > div')].map(c => Math.round(c.lastElementChild.getBoundingClientRect().bottom)); return { H: window.innerHeight, cols }; });
  console.log(JSON.stringify(m));
  await p.screenshot({ path: 'preview.png' });
  await p.pdf({ path: 'poster.pdf', width: '594mm', height: '841mm', printBackground: true });
  await b.close();
})();
