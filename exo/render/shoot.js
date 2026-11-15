const { chromium } = require('playwright');
const shots = JSON.parse(process.argv[2]);
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  for (const s of shots) {
    const p = await b.newPage({ viewport: { width: s.w, height: s.h } });
    p.on('console', m => console.log('console:', m.text()));
    p.on('pageerror', e => console.log('err:', e.message));
    await p.goto('http://127.0.0.1:8765/render.html?' + s.q + `&w=${s.w}&h=${s.h}`);
    await p.waitForFunction(() => window.__done === true, null, { timeout: 240000 });
    await p.screenshot({ path: s.out });
    console.log('ok', s.out);
    await p.close();
  }
  await b.close();
})();
