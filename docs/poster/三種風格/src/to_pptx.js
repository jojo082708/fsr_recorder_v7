// 將 poster_w.html 轉成可編輯之單頁 A1 PPTX（位置取自瀏覽器排版結果）
const path = require('path');
const { chromium } = require('playwright');
const pptxgen = require(path.join(__dirname, '../deck/node_modules/pptxgenjs'));
const OUT = process.argv[2];
const HTML = process.argv[3] || 'poster_w.html';
const PX = 96;                      // CSS px per inch
const FONT = 'DFKai-SB';

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 2245, height: 3179 } });
  await p.goto('file://' + path.join(__dirname, HTML));
  await p.waitForTimeout(800);
  const items = await p.evaluate(() => {
    const out = [];
    const R = (el) => { const r = el.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; };
    const hex = (c) => { const m = c.match(/\d+(\.\d+)?/g); if (!m) return null; if (m.length === 4 && +m[3] === 0) return null; return m.slice(0, 3).map((v) => (+v).toString(16).padStart(2, '0')).join('').toUpperCase(); };
    function runs(el) {
      const res = [];
      const walk = (n) => {
        if (n.nodeType === 3) {
          const t = n.textContent.replace(/\s+/g, ' ');
          if (!t.trim() && !res.length) return;
          const st = getComputedStyle(n.parentElement);
          const tag = n.parentElement.tagName;
          res.push({ text: t, sans: /JhengHei|WenQuanYi|sans/i.test(st.fontFamily), bold: +st.fontWeight >= 600, italic: st.fontStyle === 'italic', color: hex(st.color), size: parseFloat(st.fontSize),
            sub: tag === 'SUB', sup: tag === 'SUP' });
        } else if (n.nodeName === 'BR') { res.push({ br: true }); }
        else if (n.nodeType === 1 && getComputedStyle(n).display === 'block' && res.length && n.tagName !== 'DIV') { res.push({ br: true }); n.childNodes.forEach(walk); }
        else if (n.nodeType === 1 && n.tagName !== 'IMG' && !n.classList.contains('tab') && n.tagName !== 'TABLE' && n.tagName !== 'FIGURE' && n.tagName !== 'I') n.childNodes.forEach(walk);
      };
      el.childNodes.forEach(walk);
      while (res.length && res[res.length - 1].text !== undefined && !res[res.length - 1].text.trim()) res.pop();
      if (res.length && res[0].text) res[0].text = res[0].text.replace(/^\s+/, '');
      return res;
    }
    const txt = (el, extra = {}) => {
      const st = getComputedStyle(el);
      const r = R(el);
      const pl = parseFloat(st.paddingLeft), pr = parseFloat(st.paddingRight), pt = parseFloat(st.paddingTop), pb = parseFloat(st.paddingBottom);
      out.push({ t: 'text', x: r.x + pl, y: r.y + pt, w: r.w - pl - pr, h: r.h - pt - pb, runs: runs(el), align: st.textAlign, lh: parseFloat(st.lineHeight) || parseFloat(st.fontSize) * 1.2,
        indent: parseFloat(st.textIndent) > 0, size: parseFloat(st.fontSize), ...extra });
    };
    const box = (el, extra = {}) => {
      const st = getComputedStyle(el);
      out.push({ t: 'shape', ...R(el), fill: hex(st.backgroundColor), line: parseFloat(st.borderTopWidth) > 0 ? hex(st.borderTopColor) : null,
        lw: parseFloat(st.borderTopWidth), dash: st.borderTopStyle === 'dashed', radius: parseFloat(st.borderTopLeftRadius) || 0, ...extra });
    };
    out.push({ t: 'bg', color: hex(getComputedStyle(document.body).backgroundColor) || 'FFFFFF' });
    // 背景色塊
    box(document.querySelector('header'));
    box(document.querySelector('.badge'), { oval: true });
    box(document.querySelector('.lab'));
    document.querySelectorAll('.box, .sub').forEach((el) => box(el));
    document.querySelectorAll('.goal .l div').forEach((el) => {
      box(el);
      const r = R(el); out.push({ t: 'shape', x: r.x, y: r.y, w: parseFloat(getComputedStyle(el).borderLeftWidth), h: r.h, fill: '0E2A4F', line: null });
    });
    box(document.querySelector('.tgt'));
    document.querySelectorAll('.flow div').forEach((el, i) => {
      box(el);
      if ((i + 1) % 3) { const r = R(el); out.push({ t: 'text', x: r.x + r.w, y: r.y, w: 34, h: r.h, runs: [{ text: '→', size: 32, color: hex(getComputedStyle(el.parentElement).color) || '111111' }], align: 'center', valign: 'middle', size: 32, lh: 36 }); }
    });
    document.querySelectorAll('.legend i').forEach((el) => box(el));
    document.querySelectorAll('.tab').forEach((el) => { box(el); txt(el, { valign: 'middle' }); });
    document.querySelectorAll('[data-shape]').forEach((el) => box(el));
    // 圖片
    document.querySelectorAll('img').forEach((el) => out.push({ t: 'img', src: el.getAttribute('src'), ...R(el) }));
    // 文字
    document.querySelectorAll('h1, .en, .who span, main p, .refs, figcaption, .eq, .legend, .goal .l div, .tgt h3, .tgt .g div').forEach((el) => {
      const isEq = el.classList.contains('eq');
      if (isEq) {
        const sp = el.querySelector('span'); const r = R(el);
        const rr = runs(el).filter((x) => !(x.text && /^\(\d\)$/.test(x.text.trim())));
        out.push({ t: 'text', ...r, runs: rr, align: 'center', size: 28, lh: 36, eq: true });
        out.push({ t: 'text', x: r.x + r.w - 60, y: r.y, w: 60, h: r.h, runs: [{ text: sp.textContent, size: 28 }], align: 'right', size: 28, lh: 36 });
        return;
      }
      txt(el, { valign: el.closest('.flow, .tgt .g') ? 'middle' : 'top' });
    });
    document.querySelectorAll('.flow div').forEach((el) => txt(el, { valign: 'middle' }));
    document.querySelectorAll('[data-text]').forEach((el) => txt(el, { valign: 'middle' }));
    document.querySelectorAll('ol.c').forEach((ol) => {
      [...ol.children].forEach((li, i) => { const st = getComputedStyle(li); const r = R(li);
        out.push({ t: 'text', x: r.x - 34, y: r.y, w: r.w + 34, h: r.h, runs: [{ text: `${i + 1}. `, size: parseFloat(st.fontSize) }, ...runs(li)], align: 'left', lh: parseFloat(st.lineHeight), size: parseFloat(st.fontSize), hanging: 34 }); });
    });
    // 表格
    document.querySelectorAll('table').forEach((tb) => {
      const rows = [...tb.rows];
      out.push({ t: 'table', ...R(tb), colW: [...rows[0].cells].map((c) => R(c).w), rowH: rows.map((r) => R(r).h),
        rows: rows.map((r, ri) => [...r.cells].map((c) => { const cs = getComputedStyle(c); const bd = (w, s, col) => (parseFloat(w) > 0 && s !== 'none' ? { w: parseFloat(w), c: hex(col) } : null); return { runs: runs(c), size: parseFloat(cs.fontSize), fill: hex(cs.backgroundColor), bt: bd(cs.borderTopWidth, cs.borderTopStyle, cs.borderTopColor), bb: bd(cs.borderBottomWidth, cs.borderBottomStyle, cs.borderBottomColor) }; })) });
    });
    return out;
  });
  await b.close();

  const pres = new pptxgen();
  pres.defineLayout({ name: 'A1P', width: 2245 / PX, height: 3179 / PX });
  pres.layout = 'A1P';
  pres.title = '承重七公斤之工業搬運用下肢外骨骼 專題海報';
  const s = pres.addSlide();
  s.background = { color: 'FFFFFF' };
  const I = (v) => v / PX;
  const pt = (px) => Math.round(px * 0.75 * 10) / 10;
  const toRuns = (rs, base) => {
    const outR = [];
    rs.forEach((r) => {
      if (r.br) { if (outR.length) outR[outR.length - 1].options.breakLine = true; return; }
      outR.push({ text: r.text, options: { fontFace: base.eq ? 'Cambria Math' : (r.sans ? 'Microsoft JhengHei' : FONT), fontSize: (() => { const v = r.size || base.size; return v >= 40 ? pt(v) : Math.round(pt(v) * 0.955 * 10) / 10; })(), bold: !!r.bold, italic: !!r.italic || !!base.eq,
        color: r.color || '111111', subscript: r.sub, superscript: r.sup } });
    });
    return outR;
  };
  const bgIt = items.find((x) => x.t === 'bg'); if (bgIt) s.background = { color: bgIt.color };
  const order = { bg: -1, shape: 0, img: 1, table: 2, text: 3 };
  items.sort((a, c) => order[a.t] - order[c.t]);
  for (const it of items) {
    if (it.t === 'bg') continue;
    if (it.t === 'shape') {
      const opt = { x: I(it.x), y: I(it.y), w: I(it.w), h: I(it.h) };
      opt.fill = it.fill ? { color: it.fill } : { type: 'none' };
      opt.line = it.line ? { color: it.line, width: it.lw * 0.75, dashType: it.dash ? 'dash' : 'solid' } : { type: 'none' };
      let shape = pres.shapes.RECTANGLE;
      if (it.oval) shape = pres.shapes.OVAL;
      else if (it.radius > 0) { shape = pres.shapes.ROUNDED_RECTANGLE; opt.rectRadius = Math.min(0.5, it.radius / Math.min(it.w, it.h)); }
      s.addShape(shape, opt);
    } else if (it.t === 'img') {
      s.addImage({ path: path.join(__dirname, it.src), x: I(it.x), y: I(it.y), w: I(it.w), h: I(it.h) });
    } else if (it.t === 'text') {
      if (!it.runs.length) continue;
      const rs = toRuns(it.runs, it);
      if (it.indent && rs.length) rs[0].text = '　　' + rs[0].text;
      const align = it.align === 'justify' ? 'justify' : (it.align === 'center' ? 'center' : (it.align === 'right' ? 'right' : 'left'));
      s.addText(rs, { x: I(it.x), y: I(it.y), w: I(it.w) + 0.04, h: I(it.h), margin: 0, align, valign: it.valign || 'top',
        lineSpacing: it.lh ? pt(it.lh) : undefined, fit: 'none', wrap: true, ...(it.hanging ? { indent: 0 } : {}) });
    } else if (it.t === 'table') {
      const none = { type: 'none' }; const B = (x) => (x && x.c ? { type: 'solid', pt: Math.max(0.5, x.w * 0.75), color: x.c } : none);
      const rows = it.rows.map((r) => r.map((c) => ({ text: toRuns(c.runs.length ? c.runs : [{ text: ' ' }], { size: c.size }), options: {
        align: 'center', valign: 'middle', margin: [0.02, 0.05, 0.02, 0.05],
        border: [B(c.bt), none, B(c.bb), none], ...(c.fill ? { fill: { color: c.fill } } : {}) } })));
      s.addTable(rows, { x: I(it.x), y: I(it.y), w: I(it.w), colW: it.colW.map(I), rowH: it.rowH.map(I), fontFace: FONT });
    }
  }
  await pres.writeFile({ fileName: OUT });
  const JSZip = require(path.join(__dirname, '../deck/node_modules/jszip'));
  const fs = require('fs');
  const zip = await JSZip.loadAsync(fs.readFileSync(OUT));
  for (const f of Object.keys(zip.files).filter((f) => /ppt\/slides\/slide\d+\.xml$/.test(f))) {
    let x = await zip.file(f).async('string');
    x = x.replace(/<a:latin typeface="DFKai-SB"[^>]*\/>/g, '<a:latin typeface="Times New Roman"/>').replace(/<a:ea typeface="DFKai-SB"[^>]*\/>/g, '<a:ea typeface="標楷體"/>').replace(/<a:latin typeface="Microsoft JhengHei"[^>]*\/>/g, '<a:latin typeface="Arial"/>');
    zip.file(f, x);
  }
  fs.writeFileSync(OUT, await zip.generateAsync({ type: 'nodebuffer', compression: 'DEFLATE' }));
  console.log('wrote', OUT, items.length, 'items');
})();
