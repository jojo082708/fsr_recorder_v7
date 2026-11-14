// 下肢外骨骼專題進度規劃（每週甘特圖）— 實驗室簡報範本風格
const pptxgen = require('pptxgenjs');
const path = require('path');
const OUT = process.argv[2];
const TPL = (n) => path.join(__dirname, 'gantt_tpl', n + '.png');
const DATE = '2026/11/14';
const HF = 'DFKai-SB', BF = 'Microsoft JhengHei';

const pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.title = '下肢外骨骼專題進度規劃（每週甘特圖）';
pres.author = '電控組';

const footer = [
  { image: { path: TPL('logo'), x: 0.0, y: 4.88, w: 2.66, h: 0.70 } },
  { image: { path: TPL('screw'), x: 3.0, y: 5.20, w: 1.40, h: 0.30 } },
  { rect: { x: 4.62, y: 5.25, w: 0.60, h: 0.19, fill: { color: '4472C4' } } },
  { image: { path: TPL('screw'), x: 5.47, y: 5.20, w: 1.40, h: 0.30 } },
  { rect: { x: 7.05, y: 5.25, w: 0.58, h: 0.19, fill: { color: '4472C4' } } },
  { text: { text: DATE, options: { x: 7.75, y: 5.17, w: 1.55, h: 0.36, fontFace: 'Times New Roman', fontSize: 16, color: '000000', align: 'center', margin: 0 } } },
  { image: { path: TPL('gear'), x: 9.36, y: 5.07, w: 0.55, h: 0.54 } },
];
const SN = { x: 9.36, y: 5.07, w: 0.55, h: 0.54, fontFace: 'Arial', fontSize: 10, color: '000000', align: 'center', valign: 'middle' };
pres.defineSlideMaster({ title: 'TITLE', background: { color: 'FFFFFF' }, objects: footer.slice(), slideNumber: SN });
pres.defineSlideMaster({
  title: 'CONTENT', background: { color: 'FFFFFF' },
  objects: [...footer, { line: { x: 0.3, y: 0.83, w: 9.4, h: 0, line: { color: '222222', width: 1 } } }],
  slideNumber: SN,
});
function content(title) {
  const s = pres.addSlide({ masterName: 'CONTENT' });
  s.addText(title, { x: 0.3, y: 0.22, w: 9.4, h: 0.55, fontFace: HF, fontSize: 24, bold: true, color: '3D4B63', valign: 'middle', margin: 0 });
  return s;
}

// ---------------- 資料 ----------------
const WEEKS = [
  ['W1', '11/16', '11/22'], ['W2', '11/23', '11/29'], ['W3', '11/30', '12/06'], ['W4', '12/07', '12/13'],
  ['W5', '12/14', '12/20'], ['W6', '12/21', '12/27'], ['W7', '12/28', '01/03'], ['W8', '01/04', '01/10'],
  ['W9', '01/11', '01/17'], ['W10', '01/18', '01/24'], ['W11', '01/25', '01/31'], ['W12', '02/01', '02/05'],
];
const WNOTE = { 7: '元旦', 8: '期末考?', 9: '期末考?', 12: '春節前' };
const CAT = {
  plan: { c: '4472C4', n: '規劃' }, dev: { c: '1F6E8C', n: '開發' }, test: { c: 'ED7D31', n: '測試驗證' },
  out: { c: '7030A0', n: '成果' }, dep: { c: 'A6A6A6', n: '機構組相依' },
};
// [群組, 工作項目, 負責人, 類別, 起週, 迄週]
const TASKS = [
  ['一、控制設計', '導納控制論文精讀與公式整理', '周瑋澤', 'plan', 1, 2],
  ['一、控制設計', '單關節 DOB＋導納控制模擬', '周瑋澤', 'dev', 2, 4],
  ['二、致動器鑑別', 'K_t 荷重元驗證（AK70-9、AK60-39）', '蔡＋林', 'test', 1, 2],
  ['二、致動器鑑別', 'AK60-39 條件統一重測、模式比較', '蔡＋林', 'test', 2, 3],
  ['二、致動器鑑別', '慣量 J 與 30–60 rpm 摩擦鑑別', '蔡＋林', 'test', 3, 4],
  ['三、平台與通訊', 'Raspberry Pi＋R-Link 環境建置', '林均澤', 'dev', 1, 2],
  ['三、平台與通訊', 'AK 速度模式響應測試', '林均澤', 'test', 3, 3],
  ['三、平台與通訊', '四馬達 CAN 同步控制', '蔡＋林', 'dev', 4, 5],
  ['三、平台與通訊', '安全機制（限位、電流上限、急停）', '蔡朝欽', 'dev', 5, 6],
  ['四、感測系統', '足底 F_GR 方案與軀幹 IMU 定案', '楊翔安', 'plan', 1, 1],
  ['四、感測系統', '足底平台列印與組裝', '楊翔安', 'dev', 2, 3],
  ['四、感測系統', '足底平台 0–40 kg 靜態校正', '楊翔安', 'test', 3, 4],
  ['四、感測系統', 'FSR＋IMU 同步與步態相位判斷', '蔡＋楊', 'dev', 5, 6],
  ['四、感測系統', '軀幹 IMU 互補濾波傾角估測', '楊翔安', 'dev', 5, 6],
  ['五、單關節導納', 'DOB 力矩估測實作（AK70-9 台架）', '周＋蔡', 'dev', 4, 5],
  ['五、單關節導納', '導納控制手推測試與調參', '電控組', 'test', 5, 7],
  ['六、機構組相依', '機構設計定案', '機構組', 'dep', 1, 4],
  ['六、機構組相依', '外骨骼列印、組裝與交付', '機構組', 'dep', 5, 7],
  ['七、整機整合', '懸吊鑑別 HES 系統參數', '蔡＋林', 'test', 8, 8],
  ['七、整機整合', '雙腳導納控制穿戴（無負重）', '全體', 'test', 9, 10],
  ['七、整機整合', '上半身質心估測與 7 kg 負載補償', '周＋楊', 'dev', 10, 10],
  ['七、整機整合', '7 kg 承重測試（平地、樓梯、蹲站）', '全體', 'test', 11, 11],
  ['七、整機整合', '參數優化與成果報告', '全體', 'out', 11, 12],
];
// [週, 名稱]
const MS = [
  [2, 'M1 控制理論與 K_t 驗證完成'], [4, 'M2 機構定案、四馬達同步'], [6, 'M3 單關節導納控制 Demo'],
  [8, 'M4 外骨骼交付、首次穿戴'], [10, 'M5 雙腳無負重導納步行'], [12, 'M6 7 kg 承重測試、成果發表'],
];

// ---------------- 甘特圖繪製 ----------------
function gantt(s, rows, o) {
  const x0 = o.x, y0 = o.y, nameW = o.nameW || 3.0, ownW = o.ownW || 0.7, W = o.w, rowH = o.rowH;
  const gx = x0 + nameW + ownW, gw = W - nameW - ownW, cw = gw / 12;
  const hh = 0.42;
  // 表頭
  s.addShape(pres.shapes.RECTANGLE, { x: x0, y: y0, w: nameW + ownW, h: hh, fill: { color: '1E2A4A' }, line: { color: '1E2A4A' } });
  s.addText('工作項目', { x: x0, y: y0, w: nameW, h: hh, fontFace: BF, fontSize: 10, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle', margin: 0 });
  s.addText('負責人', { x: x0 + nameW, y: y0, w: ownW, h: hh, fontFace: BF, fontSize: 10, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle', margin: 0 });
  WEEKS.forEach(([w, a], i) => {
    const hi = o.hl === i + 1;
    s.addShape(pres.shapes.RECTANGLE, { x: gx + i * cw, y: y0, w: cw, h: hh, fill: { color: hi ? 'C00000' : (i % 2 ? '2F3D5E' : '1E2A4A') }, line: { color: 'FFFFFF', width: 0.5 } });
    s.addText([{ text: w, options: { bold: true, breakLine: true } }, { text: a, options: { fontSize: 7 } }],
      { x: gx + i * cw, y: y0, w: cw, h: hh, fontFace: 'Arial', fontSize: 8, color: 'FFFFFF', align: 'center', valign: 'middle', margin: 0 });
  });
  let y = y0 + hh;
  rows.forEach((r, ri) => {
    const bg = r.group ? 'B7D9D6' : (ri % 2 ? 'F4F7FA' : 'FFFFFF');
    s.addShape(pres.shapes.RECTANGLE, { x: x0, y, w: W, h: rowH, fill: { color: bg }, line: { color: 'DCE3EA', width: 0.5 } });
    if (r.group) {
      s.addText(r.group, { x: x0 + 0.06, y, w: nameW + ownW, h: rowH, fontFace: HF, fontSize: o.fs || 9, bold: true, color: '1E2A4A', valign: 'middle', margin: 0 });
    } else {
      const active = o.hl && r.s <= o.hl && o.hl <= r.e;
      s.addText(r.name, { x: x0 + 0.12, y, w: nameW - 0.12, h: rowH, fontFace: BF, fontSize: o.fs || 9, bold: !!active, color: active ? 'C00000' : '1F1F1F', valign: 'middle', margin: 0 });
      s.addText(r.own, { x: x0 + nameW, y, w: ownW, h: rowH, fontFace: BF, fontSize: (o.fs || 9) - 0.5, color: '404040', align: 'center', valign: 'middle', margin: 0 });
      const c = CAT[r.cat].c;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: gx + (r.s - 1) * cw + 0.03, y: y + rowH * 0.2, w: (r.e - r.s + 1) * cw - 0.06, h: rowH * 0.6,
        fill: { color: c, transparency: o.hl && !active ? 55 : 0 }, line: { color: c, width: 0.5 }, rectRadius: 0.04,
      });
    }
    y += rowH;
  });
  // 週格線與本週標示
  for (let i = 0; i <= 12; i++) s.addShape(pres.shapes.LINE, { x: gx + i * cw, y: y0 + hh, w: 0, h: y - y0 - hh, line: { color: 'DCE3EA', width: 0.5 } });
  if (o.hl) {
    s.addShape(pres.shapes.RECTANGLE, { x: gx + (o.hl - 1) * cw, y: y0 + hh, w: cw, h: y - y0 - hh, fill: { color: 'C00000', transparency: 88 }, line: { color: 'C00000', width: 1, dashType: 'dash' } });
  }
  // 里程碑列
  if (o.ms !== false) {
    s.addShape(pres.shapes.RECTANGLE, { x: x0, y, w: W, h: rowH, fill: { color: 'FFF4E5' }, line: { color: 'DCE3EA', width: 0.5 } });
    s.addText('里程碑', { x: x0 + 0.06, y, w: nameW, h: rowH, fontFace: HF, fontSize: o.fs || 9, bold: true, color: 'C00000', valign: 'middle', margin: 0 });
    MS.forEach(([w, n]) => {
      const cx = gx + w * cw - 0.12;
      s.addShape(pres.shapes.DIAMOND, { x: cx - rowH * 0.32, y: y + rowH * 0.18, w: rowH * 0.64, h: rowH * 0.64, fill: { color: 'C00000' }, line: { color: 'FFFFFF', width: 0.5 } });
      s.addText(n.split(' ')[0], { x: cx - 0.45, y, w: 0.4, h: rowH, fontFace: 'Arial', fontSize: 7, bold: true, color: 'C00000', align: 'right', valign: 'middle', margin: 0 });
    });
    y += rowH;
  }
  return y;
}
function legend(s, x, y) {
  Object.values(CAT).forEach((v, i) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + i * 1.25, y: y + 0.05, w: 0.32, h: 0.14, fill: { color: v.c }, line: { color: v.c }, rectRadius: 0.03 });
    s.addText(v.n, { x: x + i * 1.25 + 0.38, y, w: 0.9, h: 0.24, fontFace: BF, fontSize: 9, color: '404040', valign: 'middle', margin: 0 });
  });
  s.addShape(pres.shapes.DIAMOND, { x: x + 6.3, y: y + 0.03, w: 0.18, h: 0.18, fill: { color: 'C00000' }, line: { color: 'C00000' } });
  s.addText('里程碑', { x: x + 6.52, y, w: 0.8, h: 0.24, fontFace: BF, fontSize: 9, color: '404040', valign: 'middle', margin: 0 });
}
function rowsOf(tasks) {
  const out = []; let g = null;
  tasks.forEach(([grp, name, own, cat, st, en]) => { if (grp !== g) { out.push({ group: grp }); g = grp; } out.push({ name, own, cat, s: st, e: en }); });
  return out;
}

function tbl(s, rows, x, y, w, colW, o = {}) {
  const head = rows[0].map((t) => ({ text: t, options: { bold: true, color: 'FFFFFF', fill: { color: '1E2A4A' }, align: 'center' } }));
  const body = rows.slice(1).map((r, ri) => r.map((t, i) => ({ text: t, options: { fill: { color: i === 0 && o.firstCol !== false ? 'B7D9D6' : (ri % 2 ? 'EAF2F8' : 'FFFFFF') }, align: i === 0 || o.left === false ? 'center' : (o.alignAll || 'left'), bold: i === 0 && o.firstCol !== false } })));
  s.addTable([head, ...body], { x, y, w, colW, fontFace: BF, fontSize: o.fs || 10, color: '1F1F1F', border: { type: 'solid', pt: 0.5, color: 'DCE3EA' }, rowH: o.rowH || 0.3, valign: 'middle', margin: 0.04 });
}
function box(s, x, y, w, h, title, lines, color = '1F6E8C', fill = 'E6F0EE', fs = 10) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill }, rectRadius: 0.06 });
  const runs = [{ text: title, options: { bold: true, color, fontSize: fs + 2, breakLine: true } }];
  lines.forEach((l, i) => runs.push({ text: l, options: { bullet: true, breakLine: i < lines.length - 1, color: l.startsWith('【') ? 'C00000' : '1F1F1F' } }));
  s.addText(runs, { x: x + 0.12, y: y + 0.06, w: w - 0.24, h: h - 0.12, fontFace: BF, fontSize: fs, valign: 'top', paraSpaceAfter: 3, margin: 0 });
}

// ================= 1 封面 =================
let s = pres.addSlide({ masterName: 'TITLE' });
s.addText('電控組報告', { x: 1, y: 0.95, w: 8, h: 0.9, fontFace: HF, fontSize: 46, bold: true, color: '3D4B63', align: 'center', charSpacing: 6 });
s.addText('承重 7 kg 下肢外骨骼專題進度規劃（每週甘特圖）', { x: 0.5, y: 1.95, w: 9, h: 0.5, fontFace: HF, fontSize: 22, bold: true, color: '2F5597', align: 'center' });
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 2.75, y: 2.62, w: 4.5, h: 0.56, fill: { color: '4472C4' }, line: { color: '8FAADC', width: 1.5 }, rectRadius: 0.12 });
s.addText('2026/11/16 – 2027/02/05', { x: 2.75, y: 2.62, w: 4.5, h: 0.56, fontFace: 'Times New Roman', fontSize: 22, color: 'FFFFFF', align: 'center', valign: 'middle' });
s.addText([{ text: '國立聯合大學 機械工程學系 電控組', options: { breakLine: true } }, { text: '組員：蔡朝欽、林均澤、周瑋澤、楊翔安' }],
  { x: 1, y: 3.4, w: 8, h: 0.6, fontFace: BF, fontSize: 12, bold: true, color: '595959', align: 'center' });

// ================= 2 大綱 =================
s = content('大綱');
const toc = [['專題目標與完成定義', 'P3'], ['目前進度（截至 11/14）', 'P4'], ['總覽甘特圖', 'P5'], ['詳細甘特圖', 'P6–8'],
  ['里程碑與驗收標準', 'P9'], ['分工與人力配置', 'P10'], ['每週工作計畫 W1–W12', 'P11–22'], ['相依性與風險因應', 'P23']];
const cn = ['一', '二', '三', '四', '五', '六', '七', '八'];
toc.forEach(([t, p], i) => {
  const y = 1.0 + i * 0.46;
  s.addShape(pres.shapes.OVAL, { x: 0.7, y, w: 0.36, h: 0.36, fill: { color: '1F6E8C' }, line: { color: '1F6E8C' } });
  s.addText(cn[i], { x: 0.7, y, w: 0.36, h: 0.36, fontSize: 11, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle', margin: 0 });
  s.addText(t, { x: 1.3, y, w: 6.5, h: 0.36, fontFace: HF, fontSize: 16, bold: true, color: '1E2A4A', valign: 'middle', charSpacing: 2, margin: 0 });
  s.addText(p, { x: 8.4, y, w: 1.1, h: 0.36, fontFace: 'Times New Roman', fontSize: 14, bold: true, color: '1F6E8C', valign: 'middle', margin: 0 });
  s.addShape(pres.shapes.LINE, { x: 0.7, y: y + 0.42, w: 8.6, h: 0, line: { color: 'D9DEE5', width: 0.75 } });
});

// ================= 3 目標 =================
s = content('一、專題目標與完成定義');
box(s, 0.35, 1.0, 4.55, 1.85, '專題目標', [
  '工業搬運用下肢外骨骼，協助穿戴者承載 7 kg 搬運物',
  '髖、膝主動關節（AK70-9、AK60-39，雙腳共 4 顆）',
  '控制策略：外擾估測器（DOB）＋導納控制（參考尤凱融，2023）',
  '完成期限：2027/02/05（春節前）',
]);
box(s, 0.35, 2.98, 4.55, 1.8, '運動情境', [
  '平地行走、上下樓梯、蹲站轉換（搬起與放下）',
  '【待確認：7 kg 攜帶方式（前抱／背負／手提）】',
  '【待確認：期末考週次（暫列 W8–W9）】',
], 'B26A00', 'FDF0DE');
tbl(s, [['完成定義（2/05 驗收）', '量化標準'],
  ['承重', '穿戴者攜帶 7 kg 完成三種情境'],
  ['省力效果', 'PCI 低於未穿戴【待補充：目標%】'],
  ['力矩估測', 'DOB 誤差 < 10%（荷重元比對）'],
  ['即時性', '控制迴圈【待補充：目標 Hz】'],
  ['安全', '限位、電流上限、急停皆實測通過'],
  ['成果', '成果報告、簡報、實測影片'],
], 5.1, 1.0, 4.6, [1.55, 3.05], { fs: 10, rowH: 0.5 });

// ================= 4 目前進度 =================
s = content('二、目前進度（截至 2026/11/14）');
tbl(s, [['工作項目', '負責人', '完成度', '已完成內容'],
  ['需求分析與文獻探討', '周瑋澤', '50%', 'FSR／IMU 配置文獻、導納控制論文取得'],
  ['致動器選型與採購', '林均澤', '100%', '髖 AK70-9、膝 AK60-39'],
  ['FSR＋IMU 感測整合', '蔡＋楊', '50%', 'IMU 靜態／角速度驗證、足底平台設計 v17'],
  ['AK 馬達操作', '蔡＋林', '50%', 'AK70-9 K_t = 1.24、AK60-39 K_t = 1.98 N·m/A'],
  ['控制器與 CAN 通訊', '蔡＋林', '50%', 'PC＋R-Link、Arduino＋MCP2515 可控制'],
  ['單關節控制測試', '—', '0%', '—'],
  ['整機整合與穿戴測試', '—', '0%', '等待機構組'],
  ['安全評估與參數優化', '—', '0%', '—'],
  ['成果報告與展示', '全體', '20%', '成果報告 v3 初稿（含待補充）'],
], 0.35, 1.0, 9.3, [2.2, 0.9, 0.8, 5.4], { fs: 10, rowH: 0.33 });
s.addText('整體完成度約 21%（11/12 甘特圖）；未完成的關鍵：單關節導納控制、足底 F_GR 量測、軀幹 IMU、機構實體。', { x: 0.35, y: 4.42, w: 9.3, h: 0.3, fontFace: BF, fontSize: 11, bold: true, color: 'C00000', margin: 0 });

// ================= 5 總覽甘特圖 =================
s = content('三、總覽甘特圖（2026/11/16 – 2027/02/05）');
const groups = [];
TASKS.forEach(([g, , , cat, st, en]) => { const k = groups.find((x) => x.name === g); if (k) { k.s = Math.min(k.s, st); k.e = Math.max(k.e, en); } else groups.push({ name: g, own: '', cat, s: st, e: en }); });
const own = { '一、控制設計': '周瑋澤', '二、致動器鑑別': '蔡＋林', '三、平台與通訊': '蔡＋林', '四、感測系統': '楊＋蔡', '五、單關節導納': '電控組', '六、機構組相依': '機構組', '七、整機整合': '全體' };
const gcat = { '一、控制設計': 'plan', '二、致動器鑑別': 'test', '三、平台與通訊': 'dev', '四、感測系統': 'dev', '五、單關節導納': 'test', '六、機構組相依': 'dep', '七、整機整合': 'out' };
gantt(s, groups.map((g) => ({ name: g.name, own: own[g.name], cat: gcat[g.name], s: g.s, e: g.e })), { x: 0.3, y: 0.95, w: 9.4, rowH: 0.36, nameW: 2.2, ownW: 0.8, fs: 11 });
legend(s, 0.4, 4.55);
s.addText('12 週，每週四報告；W8–W9 若遇期末考，工作量減半。', { x: 0.4, y: 4.3, w: 9.2, h: 0.22, fontFace: BF, fontSize: 9, color: '595959', margin: 0 });

// ================= 6–7 詳細甘特圖 =================
const R = rowsOf(TASKS);
const c1 = R.findIndex((r) => r.group === '四、感測系統'), c2 = R.findIndex((r) => r.group === '六、機構組相依');
[[0, c1, false], [c1, c2, false], [c2, R.length, true]].forEach(([a, b, m], i) => {
  s = content(`四、詳細甘特圖（${i + 1}/3）`);
  gantt(s, R.slice(a, b), { x: 0.3, y: 0.95, w: 9.4, rowH: 0.25, fs: 9, ms: m });
  legend(s, 0.4, 4.55);
});

// ================= 8 里程碑 =================
s = content('五、里程碑與驗收標準');
tbl(s, [['里程碑', '日期', '內容', '驗收標準'],
  ['M1', '11/29（W2）', '控制理論與 K_t 驗證', '公式整理完成；兩顆馬達 K_t 與荷重元誤差 < 5%'],
  ['M2', '12/13（W4）', '機構定案、四馬達同步', '機構組交出尺寸與質量；Pi 同時控制 4 顆馬達'],
  ['M3', '12/27（W6）', '單關節導納控制 Demo', '手推力臂可順從；DOB 誤差 < 10%；急停有效'],
  ['M4', '01/10（W8）', '外骨骼交付、首次穿戴', '馬達裝機、懸吊鑑別完成；低增益穿戴無異常'],
  ['M5', '01/24（W10）', '雙腳無負重導納步行', '平地、樓梯、蹲站各完成 10 次'],
  ['M6', '02/05（W12）', '7 kg 承重測試、成果發表', '三情境 PCI 比較；報告與影片完成'],
], 0.35, 1.0, 9.3, [0.7, 1.2, 2.2, 5.2], { fs: 10, rowH: 0.5 });
s.addText('驗收數值為建議值，請依老師要求調整。', { x: 0.35, y: 4.55, w: 9.3, h: 0.25, fontFace: BF, fontSize: 9, color: 'C00000', margin: 0 });

// ================= 9 分工 =================
s = content('六、分工與人力配置');
const ppl = [
  ['周瑋澤', '控制理論、DOB／導納模擬、負載補償', [1, 2, 3, 4, 5, 7, 10, 12]],
  ['蔡朝欽', '馬達鑑別、DOB 實作、安全機制、CAN', [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12]],
  ['林均澤', 'Raspberry Pi、R-Link、速度模式、CAN 同步', [1, 2, 3, 4, 5, 8, 9, 11, 12]],
  ['楊翔安', '足底平台、F_GR 量測、IMU、步態相位', [1, 2, 3, 4, 5, 6, 10, 11, 12]],
  ['機構組', '機構定案、列印組裝、交付', [1, 2, 3, 4, 5, 6, 7, 8]],
];
const px = 2.9, pcw = 6.8 / 12;
WEEKS.forEach(([w], i) => s.addText(w, { x: px + i * pcw, y: 0.98, w: pcw, h: 0.28, fontFace: 'Arial', fontSize: 9, bold: true, color: 'FFFFFF', fill: { color: '1E2A4A' }, align: 'center', valign: 'middle', margin: 0 }));
ppl.forEach(([n, d, ws], i) => {
  const y = 1.32 + i * 0.6;
  s.addText([{ text: n, options: { bold: true, fontSize: 12, breakLine: true } }, { text: d, options: { fontSize: 8.5, color: '595959' } }], { x: 0.35, y, w: 2.5, h: 0.55, fontFace: BF, valign: 'middle', margin: 0 });
  for (let k = 1; k <= 12; k++) {
    const on = ws.includes(k);
    s.addShape(pres.shapes.RECTANGLE, { x: px + (k - 1) * pcw + 0.02, y: y + 0.1, w: pcw - 0.04, h: 0.35, fill: { color: on ? (n === '機構組' ? 'A6A6A6' : '1F6E8C') : 'F2F4F7' }, line: { color: 'FFFFFF' } });
  }
});
s.addText('深色＝該週主要工作週；各人每週工作內容見 W1–W12 頁。', { x: 0.35, y: 4.4, w: 9.3, h: 0.3, fontFace: BF, fontSize: 10, color: '595959', margin: 0 });

// ================= 10–21 每週計畫 =================
const PLAN = {
  1: { goal: '確認需求、建立開發環境', items: [
      ['導納控制論文第 3、4 章精讀，整理 DOB 與導納公式、符號表', '周瑋澤', '公式筆記'],
      ['AK70-9 荷重元驗證 K_t（靜態保持力矩 vs i_q）', '蔡＋林', 'K_t 驗證數據'],
      ['Raspberry Pi 安裝系統、Python 與 R-Link 驅動', '林均澤', 'Pi 讀取馬達回授'],
      ['足底 F_GR 方案（壓力鞋墊／荷重元）與軀幹 IMU 位置定案', '楊翔安', '方案比較表、採購單'],
      ['與機構組確認 7 kg 攜帶方式、腿長、關節力矩需求', '全體', '需求確認紀錄']],
    check: ['Pi 可讀取 AK 回授', 'F_GR 方案與採購單送出'], dep: ['機構組提供初步尺寸與力矩估算'] },
  2: { goal: '完成理論準備與 K_t 驗證（M1）', items: [
      ['論文第 6 章實驗與參數整理；建立單關節模擬架構', '周瑋澤', '模擬程式 v0'],
      ['AK60-39 荷重元驗證；伺服與 MIT 模式 i_q 比較', '蔡＋林', 'K_t 比較表'],
      ['R-Link＋Python 控制單顆馬達（位置、速度模式）', '林均澤', 'Pi 控制程式'],
      ['列印足底平台共用後段＋穿鞋前段', '楊翔安', '平台零件']],
    check: ['M1：兩顆馬達 K_t 與荷重元誤差 < 5%', '公式整理完成並報告'], dep: [] },
  3: { goal: '致動器動態鑑別、速度迴路特性', items: [
      ['單關節 DOB＋導納 Python 模擬（含 J_d、B_d 掃描）', '周瑋澤', '模擬結果圖'],
      ['AK60-39 統一條件重測；慣量 J 步階測試', '蔡＋林', 'J 估計值'],
      ['AK 速度模式步階響應（上升時間、頻寬）', '林均澤', '響應曲線'],
      ['平台組裝感測匣；開始 0–40 kg 分階靜態校正', '楊翔安', '校正數據']],
    check: ['速度迴路頻寬足以追隨步態命令', '平台組裝完成'], dep: [] },
  4: { goal: '模型參數定版、四馬達同步（M2）', items: [
      ['模擬完成，決定 J_d、B_d、Q(s) 初始值', '周瑋澤', '參數建議表'],
      ['30–60 rpm 摩擦鑑別；致動器參數表定版', '蔡＋林', '參數表 v1'],
      ['四馬達 CAN 同步控制開發', '蔡＋林', '同步控制程式'],
      ['足底平台負載－電壓校正曲線（含遲滯）', '楊翔安', '校正曲線'],
      ['AK70-9 台架 DOB 力矩估測實作開始', '周＋蔡', 'DOB 程式 v0']],
    check: ['M2：機構組交出尺寸與質量', 'Pi 同時控制 4 顆馬達'], dep: ['機構設計定案（關鍵相依）'] },
  5: { goal: '單關節 DOB 實作、感測同步', items: [
      ['DOB 估測力矩與荷重元比對', '周＋蔡', '估測誤差分析'],
      ['CAN 同步完成；量測控制頻率與延遲', '林均澤', '時序量測'],
      ['安全機制：軟體限位、電流上限、急停按鈕', '蔡朝欽', '安全程式'],
      ['FSR＋IMU 同步量測；軀幹 IMU 互補濾波', '楊＋蔡', '同步資料'],
      ['導納控制手推測試開始', '電控組', '測試影片']],
    check: ['DOB 誤差 < 10%', '控制迴圈頻率實測值'], dep: ['機構組開始列印'] },
  6: { goal: '單關節導納控制 Demo（M3）', items: [
      ['導納手推測試：調整 B_d（省力）與 J_d（速度）', '電控組', '力矩－角速度曲線'],
      ['安全機制實測：限位、過流、急停', '蔡朝欽', '安全測試紀錄'],
      ['步態相位判斷門檻；傾角估測驗證', '楊翔安', '門檻值與準確率'],
      ['週報＋Demo 影片', '全體', 'Demo 影片']],
    check: ['M3：手推力臂可順從', '急停 100% 有效'], dep: [] },
  7: { goal: '重力項導納與等效負載（元旦週）', items: [
      ['導納加入重力項 G_1、G_2；擺盪抑制測試', '周＋蔡', 'G 參數測試'],
      ['AK70-9 台架掛 3 kg、7 kg 等效負載之導納測試', '電控組', '負載測試數據'],
      ['成果報告 v4 更新（M1–M3 結果）', '全體', '報告 v4'],
      ['準備裝機：走線、配電、背架盒', '林＋楊', '線材與配電']],
    check: ['台架承受 7 kg 等效負載時導納穩定'], dep: ['機構組完成列印與組裝'] },
  8: { goal: '外骨骼交付、懸吊鑑別（M4）', items: [
      ['外骨骼裝馬達、感測器與走線', '全體＋機構組', '整機'],
      ['懸吊鑑別 HES 系統參數（φθ = τ_l）', '蔡＋林', '系統參數表'],
      ['首次穿戴：無動力／低增益安全檢查', '全體', '穿戴檢查表']],
    check: ['M4：懸吊鑑別完成、低增益穿戴無異常'], dep: ['【待確認：期末考週，工作量減半】'] },
  9: { goal: '單腳→雙腳導納穿戴', items: [
      ['單腳導納控制穿戴測試（低增益）', '蔡＋周', '單腳測試紀錄'],
      ['雙腳整合，四馬達同時導納控制', '蔡＋林', '雙腳程式'],
      ['情境切換判斷整合（FSR＋IMU）', '楊翔安', '情境判斷程式']],
    check: ['雙腳可穩定平地行走'], dep: ['【待確認：期末考週】'] },
  10: { goal: '無負重三情境、負載補償（M5）', items: [
      ['雙腳無負重：平地、上樓梯、蹲站', '全體', '三情境數據'],
      ['上半身質心估測（最小平方法）', '周＋楊', 'l_UPC 估計值'],
      ['7 kg 負載力矩補償實作', '周＋蔡', '補償程式']],
    check: ['M5：三情境各 10 次無異常'], dep: [] },
  11: { goal: '7 kg 承重測試', items: [
      ['7 kg 承重：平地、上樓梯、蹲站', '全體', '承重測試數據'],
      ['穿戴 vs 未穿戴心率量測，計算 PCI', '楊＋周', 'PCI 比較圖'],
      ['數據分析與參數微調', '蔡＋林', '分析報告']],
    check: ['三情境 PCI 皆低於未穿戴'], dep: ['需購買心率帶【待確認】'] },
  12: { goal: '優化與成果發表（M6）', items: [
      ['參數優化、補測不足數據', '電控組', '最終參數'],
      ['成果報告 v5、成果簡報、實測影片', '全體', '報告、簡報、影片'],
      ['02/05 成果發表', '全體', '發表']],
    check: ['M6：報告、簡報、影片完成'], dep: ['02/06 起春節'] },
};
for (let w = 1; w <= 12; w++) {
  const P = PLAN[w], [wn, a, b] = WEEKS[w - 1];
  s = content(`七、每週計畫 ${wn}（${a}–${b}${WNOTE[w] ? '，' + WNOTE[w] : ''}）`);
  // 週時間軸
  const tx = 0.35, tw = 9.3, tcw = tw / 12;
  WEEKS.forEach(([n], i) => {
    const cur = i + 1 === w, past = i + 1 < w;
    s.addShape(pres.shapes.RECTANGLE, { x: tx + i * tcw + 0.01, y: 0.95, w: tcw - 0.02, h: 0.28, fill: { color: cur ? 'C00000' : (past ? '7F8FA6' : 'DCE3EA') }, line: { color: 'FFFFFF' } });
    s.addText(n, { x: tx + i * tcw, y: 0.95, w: tcw, h: 0.28, fontFace: 'Arial', fontSize: 9, bold: true, color: cur || past ? 'FFFFFF' : '404040', align: 'center', valign: 'middle', margin: 0 });
    const m = MS.find(([mw]) => mw === i + 1);
    if (m) {
      s.addShape(pres.shapes.DIAMOND, { x: tx + (i + 1) * tcw - 0.13, y: 1.25, w: 0.16, h: 0.16, fill: { color: 'C00000' }, line: { color: 'C00000' } });
      s.addText(m[1].split(' ')[0], { x: tx + (i + 1) * tcw - 0.52, y: 1.22, w: 0.38, h: 0.2, fontFace: 'Arial', fontSize: 7, bold: true, color: 'C00000', align: 'right', margin: 0 });
    }
  });
  s.addText([{ text: '本週目標：', options: { bold: true, color: 'C00000' } }, { text: P.goal, options: { bold: true, color: '1E2A4A' } }],
    { x: 0.35, y: 1.45, w: 9.3, h: 0.34, fontFace: HF, fontSize: 15, valign: 'middle', margin: 0 });
  const rows = [['工作項目', '負責人', '交付物'], ...P.items];
  const rh = P.items.length > 4 ? 0.48 : 0.56;
  tbl(s, rows, 0.35, 1.85, 6.35, [3.85, 1.0, 1.5], { fs: 10, rowH: rh, firstCol: false });
  box(s, 6.85, 1.85, 2.8, 1.45, '驗收標準', P.check, '1E6B5C', 'E6F0EE', 10);
  box(s, 6.85, 3.4, 2.8, 1.35, '相依／備註', P.dep.length ? P.dep : ['無'], 'B26A00', 'FDF0DE', 10);
}

// ================= 22 風險 =================
s = content('八、相依性與風險因應');
tbl(s, [['風險', '影響', '因應方案', '決策時點'],
  ['機構設計延遲', '整機整合（W8 起）順延', '先以 AK70-9 台架完成 7 kg 等效負載之單關節導納展示', 'W4（12/13）'],
  ['馬達力矩不足', '無法承重 7 kg 上樓梯、蹲站', '依機構組力矩需求檢核；不足時限縮情境或升級 AK80-64【待確認交期】', 'W4'],
  ['足底 F_GR 量測不足', 'DOB 估測失準', '採購壓力鞋墊，或於平台加入荷重元', 'W1'],
  ['期末考', 'W8–W9 進度減半', 'W7 先完成懸吊鑑別與雙腳程式', 'W6'],
  ['穿戴安全', '人員受傷', '安全機制（W6）通過前不進行穿戴；首穿採低增益', 'W6'],
  ['控制頻率不足', '導納追隨延遲', 'W5 量測；不足時將 DOB 移至 ESP32 或縮減通訊', 'W5'],
], 0.35, 1.0, 9.3, [1.5, 2.0, 4.6, 1.2], { fs: 10, rowH: 0.52 });

// ================= 23 結尾 =================
s = pres.addSlide({ masterName: 'TITLE' });
s.addText('THANK YOU!', { x: 1, y: 1.3, w: 8, h: 1.0, fontFace: 'Times New Roman', fontSize: 48, bold: true, color: '3D4B63', align: 'center' });
s.addText('Q & A', { x: 1, y: 2.3, w: 8, h: 0.6, fontFace: 'Times New Roman', fontSize: 28, bold: true, color: '2F5597', align: 'center' });
s.addText('國立聯合大學　機械工程學系　電控組', { x: 1, y: 3.1, w: 8, h: 0.4, fontFace: BF, fontSize: 14, bold: true, color: '595959', align: 'center' });

pres.writeFile({ fileName: OUT }).then(() => console.log('wrote', OUT));
