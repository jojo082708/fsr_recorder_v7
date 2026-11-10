const { chromium } = require('playwright');
(async () => {
  const [,, url, outdir, fps, only] = process.argv;
  const b = await chromium.launch({ args: ['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  p.on('pageerror', e => console.log('pageerror', e.message));
  await p.goto(url); await p.waitForFunction(() => window.ready === true, null, { timeout: 120000 });
  const dur = await p.evaluate(() => window.DUR); const n = Math.round(dur * fps);
  const list = only ? only.split(',').map(Number) : [...Array(n).keys()];
  console.log('dur', dur, 'frames', n);
  for (const i of list) {
    await p.evaluate(t => window.renderAt(t), i / fps);
    await p.screenshot({ path: `${outdir}/f${String(i).padStart(5,'0')}.png` });
  }
  await b.close();
})();
