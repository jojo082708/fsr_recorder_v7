const pptxgen = require("pptxgenjs");
const path = require("path");
const S = process.argv[2], OUT = process.argv[3];
const SK = "/root/.claude/skills/synced/f77b1f71-efd5-4d39-827c-b57319ddcd45_0fa3e5e9-e585-4878-981f-67fe0bc54b40/pptx";
const { applyTheme } = require(SK + "/scripts/apply_theme.js");
const SZ = require(S + "/imgsizes.json");
const IMG = n => path.join(S, "ppt_img", n + ".png"), TPL = n => path.join(S, "tpl", n + ".png");
const DATE = "2026/11/12";
const THEME = { name: "GDAM Lab", headFontFace: "DFKai-SB", bodyFontFace: "Microsoft JhengHei",
  colors: { dk1: "1F1F1F", lt1: "FFFFFF", dk2: "3D4B63", lt2: "F2F4F7", accent1: "1F6E8C", accent2: "4472C4",
            accent3: "FFC000", accent4: "C00000", accent5: "1E2A4A", accent6: "A9D2CF", hlink: "4472C4", folHlink: "7F7F7F" } };
const pres = new pptxgen(); pres.layout = "LAYOUT_16x9"; pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "電控組報告：外穿式 FSR 雙點足底力量量測平台"; pres.author = "林均澤";
const C = pres.SchemeColor;
const footer = [
  { image: { path: TPL("logo_t"), x: 0.17, y: 4.83, w: 2.0 * 677 / 224 * 0.36 / 0.6 * 0.6 / 1.0 > 0 ? 2.09 : 2.09, h: 0.69 } },
  { image: { path: TPL("screw_t"), x: 3.0, y: 5.18, w: 1.38, h: 0.295 } },
  { rect: { x: 4.62, y: 5.27, w: 0.6, h: 0.19, fill: { color: "4472C4" } } },
  { image: { path: TPL("screw_t"), x: 5.47, y: 5.18, w: 1.38, h: 0.295 } },
  { rect: { x: 7.05, y: 5.27, w: 0.58, h: 0.19, fill: { color: "4472C4" } } },
  { text: { text: DATE, options: { x: 7.75, y: 5.17, w: 1.55, h: 0.36, fontFace: "Times New Roman", fontSize: 16, color: "000000", align: "center", margin: 0 } } },
  { image: { path: TPL("gear_clean"), x: 9.37, y: 5.08, w: 0.52, h: 0.51 } },
];
const SN = { x: 9.37, y: 5.08, w: 0.52, h: 0.51, fontFace: "Arial", fontSize: 10, color: "000000", align: "center", valign: "middle" };
pres.defineSlideMaster({ title: "TITLE", background: { color: "FFFFFF" }, objects: footer.slice(), slideNumber: SN });
pres.defineSlideMaster({ title: "CONTENT", background: { color: "FFFFFF" },
  objects: [...footer, { line: { x: 0.3, y: 0.83, w: 9.4, h: 0, line: { color: "222222", width: 1 } } },
    { placeholder: { options: { name: "title", type: "title", x: 0.3, y: 0.22, w: 9.4, h: 0.55, fontFace: "DFKai-SB", fontSize: 26, bold: true, color: "3D4B63", align: "left", valign: "middle", margin: 0 }, text: "" } }],
  slideNumber: SN });

function fit(name, x, y, w, h, extra = {}) {   // contain-fit, centered
  const [iw, ih] = SZ[name]; const r = Math.min(w / iw, h / ih); const W = iw * r, H = ih * r;
  return { path: IMG(name), x: x + (w - W) / 2, y: y + (h - H) / 2, w: W, h: H, ...extra };
}
const red = t => ({ text: t, options: { color: "C00000", bold: true } });
const plain = t => ({ text: t });
function content(title, sec) { const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: sec }); s.addText(title, { placeholder: "title" }); return s; }
function tbl(s, rows, x, y, w, colW, opts = {}) {
  const head = rows[0].map((t, i) => ({ text: t, options: { bold: true, color: i === 0 ? "1F1F1F" : "FFFFFF", fill: { color: i === 0 ? "A9D2CF" : "1E2A4A" }, align: "center" } }));
  const body = rows.slice(1).map((r, ri) => r.map((t, i) => ({ text: t, options: { fill: { color: i === 0 ? "B7D9D6" : (ri % 2 ? "EAF2F8" : "FFFFFF") }, align: "center", bold: i === 0 } })));
  s.addTable([head, ...body], { x, y, w, colW, fontFace: "Microsoft JhengHei", fontSize: opts.fs || 12, color: "1F1F1F", border: { type: "solid", pt: 0.5, color: "DCE3EA" }, rowH: opts.rowH || 0.36, valign: "middle" });
}
function bullets(s, items, x, y, w, h, fs = 15) {
  s.addText(items.map((it, i) => ({ text: "", options: {} }) && ({ text: Array.isArray(it) ? "" : it, options: { bullet: false, breakLine: i < items.length - 1 } })), { x, y, w, h, isTextBox: true });
}
function numbered(s, items, x, y, w, h, fs = 16) {
  const runs = [];
  items.forEach((it, i) => { const parts = Array.isArray(it) ? it : [plain(it)];
    parts.forEach((p, j) => runs.push({ text: (j === 0 ? `${i + 1}.` : "") + p.text, options: { ...(p.options || {}), breakLine: j === parts.length - 1 && i < items.length - 1 } })); });
  s.addText(runs, { x, y, w, h, fontFace: "Microsoft JhengHei", fontSize: fs, color: "1F1F1F", bold: true, valign: "top", paraSpaceAfter: 8, isTextBox: true, margin: 0 });
}

// 1 封面
pres.addSection({ title: "封面" });
let s = pres.addSlide({ masterName: "TITLE", sectionTitle: "封面" });
s.addText("電控組報告", { x: 1, y: 1.15, w: 8, h: 0.9, fontFace: "DFKai-SB", fontSize: 48, bold: true, color: "3D4B63", align: "center", charSpacing: 6, isTextBox: true });
s.addText("外穿式 FSR 雙點足底力量量測平台設計", { x: 1, y: 2.15, w: 8, h: 0.5, fontFace: "DFKai-SB", fontSize: 22, bold: true, color: "2F5597", align: "center", isTextBox: true });
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 3.5, y: 2.78, w: 3.0, h: 0.56, fill: { color: "4472C4" }, line: { color: "8FAADC", width: 1.5 }, rectRadius: 0.12 });
s.addText(DATE, { x: 3.5, y: 2.78, w: 3.0, h: 0.56, fontFace: "Times New Roman", fontSize: 22, color: "FFFFFF", align: "center", valign: "middle", isTextBox: true });
s.addText([{ text: "報告人：林均澤　｜　國立聯合大學 機械工程學系 電控組", options: { breakLine: true } }, { text: "組員：蔡朝欽、林均澤、周瑋澤、楊翔安" }],
  { x: 1, y: 3.55, w: 8, h: 0.6, fontFace: "Microsoft JhengHei", fontSize: 12, bold: true, color: "595959", align: "center", isTextBox: true });

// 2 大綱
pres.addSection({ title: "大綱" });
s = content("大綱", "大綱");
const toc = [["設計目標與需求", "P3"], ["腳印量測與感測位置", "P4"], ["鋼珠式 FSR 感測匣", "P5"], ["修改前後對照（v15 → v17）", "P6"],
             ["模組化可拆卸設計", "P7-8"], ["穿鞋 / 赤腳兩種用法", "P9"], ["走線與電控整合", "P10"], ["待確認事項與後續進度", "P11"]];
const cn = ["一", "二", "三", "四", "五", "六", "七", "八"];
toc.forEach(([t, p], i) => { const y = 1.0 + i * 0.47;
  s.addShape(pres.shapes.OVAL, { x: 0.7, y: y, w: 0.36, h: 0.36, fill: { color: "1F6E8C" }, line: { color: "1F6E8C" } });
  s.addText(cn[i], { x: 0.7, y: y, w: 0.36, h: 0.36, fontSize: 11, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true });
  s.addText(t, { x: 1.3, y: y, w: 6.5, h: 0.36, fontFace: "DFKai-SB", fontSize: 16, bold: true, color: "1E2A4A", valign: "middle", charSpacing: 2, margin: 0, isTextBox: true });
  s.addText(p, { x: 8.6, y: y, w: 0.9, h: 0.36, fontFace: "Times New Roman", fontSize: 14, bold: true, color: "1F6E8C", valign: "middle", margin: 0, isTextBox: true });
  s.addShape(pres.shapes.LINE, { x: 0.7, y: y + 0.42, w: 8.6, h: 0, line: { color: "D9DEE5", width: 0.75 } }); });

// 3 設計目標
pres.addSection({ title: "設計" });
s = content("一、設計目標與需求", "設計");
numbered(s, [[plain("外穿式："), red("不拆解、不開孔、不修改"), plain("原有布鞋")],
             [plain("雙點量測："), red("大拇趾球 S1、腳跟 S2"), plain(" 各一顆 FSR 402")],
             [plain("保留已列印的 v15 "), red("小腿件"), plain("（背面放麵包板）")],
             [plain("外形維持 "), red("AFO 托盤"), plain("造型，依鞋 / 腳尺寸調整")],
             [plain("配合 300×300×350 印表機："), red("分件 + 螺絲鎖合"), plain("、可拆換")]], 0.5, 1.1, 5.0, 3.4, 15);
s.addImage(fit("shoe_iso", 5.7, 0.95, 4.0, 4.05, { altText: "布鞋放入 AFO v17 平台的等角圖" }));

// 4 腳印與感測位置
s = content("二、腳印量測與感測位置", "設計");
s.addImage(fit("overlay_shoe", 0.35, 0.95, 5.9, 2.95, { altText: "腳印、布鞋輪廓與托盤重合俯視圖" }));
tbl(s, [["感測點", "腳印量測", "托盤座標 (X, Y)"], ["S1 大拇趾球", "距腳跟 177 / 距外側 72", "(197.3, −25)"], ["S2 腳跟", "距腳跟 25* / 距外側 35", "(45.3, +12)"]], 6.45, 1.15, 3.25, [0.95, 1.3, 1.0], { fs: 10, rowH: 0.42 });
s.addText([{ text: "腳印比例：6.25 px/mm（長 249、寬 94）", options: { breakLine: true } },
           { text: "X = 套筒內面 8.3 + 腳跟→鞋底 12* + 量測值", options: { breakLine: true } },
           { text: "* 待確認（S2 圖上標 21、比例量 25）", options: { color: "C00000" } }],
  { x: 6.45, y: 2.6, w: 3.25, h: 1.2, fontFace: "Microsoft JhengHei", fontSize: 11, color: "1F1F1F", valign: "top", paraSpaceAfter: 4, isTextBox: true, margin: 0 });
tbl(s, [["項目", "鞋底（量測）", "腳掌（量測）"], ["長 × 寬", "310 × 110", "254 × 100"]], 0.6, 4.05, 5.4, [1.4, 2.0, 2.0], { fs: 11, rowH: 0.32 });

// 5 感測匣
s = content("三、鋼珠式 FSR 感測匣", "設計");
s.addImage(fit("section_clean", 0.3, 0.95, 5.9, 2.4, { altText: "S1 感測匣剖面：TPU 導槽、鋼珠、FSR、支撐座" }));
s.addText("受力路徑：鞋底 → TPU 導槽 → Ø5 鋼珠 → 保護片 → FSR 402 → 支撐座 → 底板", { x: 0.3, y: 3.45, w: 5.9, h: 0.35, fontSize: 11, bold: true, color: "1E2A4A", align: "center", isTextBox: true, margin: 0 });
const leg = [["A9D2CF", "TPU 95A 導槽（Ø21 傳力面）"], ["CFE8C6", "感測匣殼 PETG（Ø42 凸環 +3 mm）"], ["E0E3E8", "Ø5 鋼珠 SUJ2"], ["222222", "FSR 402 + Ø10 保護片"], ["B5BCC6", "腳底件底板"]];
leg.forEach(([c, t], i) => { const x = 0.45 + (i % 3) * 1.95, y = 3.9 + Math.floor(i / 3) * 0.32;
  s.addShape(pres.shapes.RECTANGLE, { x, y: y + 0.06, w: 0.18, h: 0.18, fill: { color: c }, line: { color: "555555", width: 0.5 } });
  s.addText(t, { x: x + 0.24, y, w: 1.7, h: 0.3, fontSize: 9, color: "1F1F1F", valign: "middle", isTextBox: true, margin: 0 }); });
tbl(s, [["項目", "設計"], ["鋼珠限位", "Ø5.15 導槽孔只能上下\n下方 Ø4.5 防脫唇"], ["過載保護", "下沉 > 1 mm 由止擋分擔\nFSR 最大約 69 N（估）"], ["位置", "固定（不可移動）\n3 × M2.5 鎖附"], ["更換", "整匣由上方取出"]], 6.45, 1.0, 3.25, [0.95, 2.3], { fs: 10, rowH: 0.55 });

// 6 前後對照
s = content("四、修改前後對照（v15 → v17）", "設計");
s.addImage(fit("v15_v17", 0.3, 0.92, 4.4, 3.95, { altText: "cadgen 輸出：v17（藍）與 v15（紅）並排" }));
s.addText("text-to-cad（cadgen）建模：左 v17、右 v15", { x: 0.3, y: 4.6, w: 4.4, h: 0.25, fontSize: 9, color: "595959", align: "center", isTextBox: true, margin: 0 });
tbl(s, [["項目", "v15 修改前", "v17 修改後"], ["腳底件", "288 × 118", "349 × 134（穿鞋）"], ["FSR", "舊溝槽式", "鋼珠式 × 2"], ["感測匣", "—", "Ø42 凸環 +3 mm"], ["過載保護", "無", "止擋，約 69 N"],
         ["走線", "溝槽外露", "槽 + 齊平蓋板"], ["列印", "一件", "共用後段 + 前段"], ["小腿件", "原設計", "不變"]], 4.95, 1.0, 4.75, [1.25, 1.5, 2.0], { fs: 11, rowH: 0.43 });

// 7 模組化
pres.addSection({ title: "模組化" });
s = content("五、模組化可拆卸設計", "模組化");
s.addImage(fit("modular_iso", 0.3, 0.92, 5.6, 4.0, { altText: "共用後段可接穿鞋前段或赤腳前段的爆炸圖" }));
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.1, y: 1.0, w: 3.6, h: 1.75, fill: { color: "E6F0EE" }, line: { color: "E6F0EE" }, rectRadius: 0.08 });
s.addText([{ text: "共用後段（只印一次）", options: { bold: true, color: "1E6B5C", fontSize: 13, breakLine: true } },
           { text: "後跟杯、小腿件介面", options: { bullet: true, breakLine: true } }, { text: "S2 腳跟感測匣、走線出口", options: { bullet: true, breakLine: true } },
           { text: "放大從 x = 140 之後才開始 → 所有尺寸後段相同", options: { bullet: true } }],
  { x: 6.25, y: 1.08, w: 3.35, h: 1.6, fontSize: 11, color: "1F1F1F", valign: "top", paraSpaceAfter: 3, isTextBox: true, margin: 0 });
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.1, y: 2.9, w: 3.6, h: 1.95, fill: { color: "FDF0DE" }, line: { color: "FDF0DE" }, rectRadius: 0.08 });
s.addText([{ text: "可換前段（依尺寸）", options: { bold: true, color: "B26A00", fontSize: 13, breakLine: true } },
           { text: "穿鞋 310×110：v15 造型擋塊", options: { bullet: true, breakLine: true } }, { text: "赤腳 254×100：客製擋塊 + 12 mm 腳跟墊塊", options: { bullet: true, breakLine: true } },
           { text: "任意尺寸：export_kit.py shoe:長x寬", options: { bullet: true } }],
  { x: 6.25, y: 2.98, w: 3.35, h: 1.8, fontSize: 11, color: "1F1F1F", valign: "top", paraSpaceAfter: 3, isTextBox: true, margin: 0 });

// 8 分件
s = content("六、分件與螺絲接合", "模組化");
s.addImage(fit("split_iso", 0.3, 0.92, 4.9, 2.95, { altText: "後段與前段分件爆炸圖" }));
s.addImage(fit("split_section", 5.35, 0.95, 4.35, 2.4, { altText: "搭接處剖面：M4 螺絲與熱熔螺母" }));
s.addImage(fit("split_bed", 0.5, 3.9, 1.3, 1.05, { altText: "兩件同盤列印排版" }));
s.addText("兩件同盤列印\n300 × 300", { x: 1.85, y: 4.1, w: 1.4, h: 0.65, fontSize: 10, color: "595959", isTextBox: true, margin: 0 });
tbl(s, [["項目", "規格"], ["接合位置", "x = 120（兩感測匣之間）"], ["搭接", "底板 30 mm，間隙 0.15"], ["鎖固", "6 × M4×12 平頭 + 熱熔螺母"], ["換前段", "鬆 6 支螺絲即可"]], 5.35, 3.4, 4.35, [1.2, 3.15], { fs: 10, rowH: 0.3 });

// 9 兩種用法
s = content("七、穿鞋 / 赤腳兩種用法", "模組化");
s.addImage(fit("shoe_iso", 0.3, 0.92, 2.8, 3.1, { altText: "穿鞋組合" }));
s.addImage(fit("bare_iso", 3.15, 0.92, 2.8, 3.1, { altText: "赤腳組合" }));
s.addText("穿鞋組合", { x: 0.3, y: 4.0, w: 2.8, h: 0.3, fontSize: 12, bold: true, color: "2F5597", align: "center", isTextBox: true, margin: 0 });
s.addText("赤腳組合", { x: 3.15, y: 4.0, w: 2.8, h: 0.3, fontSize: 12, bold: true, color: "2F5597", align: "center", isTextBox: true, margin: 0 });
tbl(s, [["項目", "穿鞋", "赤腳"], ["依據", "鞋底 310×110", "腳掌 254×100"], ["整體", "349 × 134", "299 × 122"], ["前段", "240 × 134", "190 × 122"], ["擋塊", "v15 放大", "依腳型客製"],
         ["腳跟定位", "鞋跟頂套筒", "12 mm 墊塊"], ["S1 / S2", "相同", "相同"]], 6.15, 1.0, 3.55, [1.05, 1.25, 1.25], { fs: 10.5, rowH: 0.42 });
s.addText([red("腳跟墊塊"), plain(" 讓赤腳時腳跟位置與穿鞋相同 → 感測器不用移動")], { x: 6.15, y: 4.05, w: 3.55, h: 0.6, fontSize: 11, color: "1F1F1F", isTextBox: true, margin: 0 });

// 10 走線
pres.addSection({ title: "整合與進度" });
s = content("八、走線與電控整合", "整合與進度");
s.addImage(fit("wire_iso", 0.3, 0.92, 3.6, 4.0, { altText: "走線路徑與小腿件背面的麵包板、ESP32" }));
numbered(s, [[plain("FSR 尾線走"), red("底板走線槽"), plain("，上蓋齊平蓋板")],
             [plain("從後跟杯背面 "), red("Ø5 出線孔"), plain(" 拉出")],
             [plain("沿小腿件背面接到"), red("麵包板"), plain("（2 × JST-XH）")],
             [plain("FSR 串 10 kΩ 分壓 → ESP32 "), red("ADC1"), plain("（GPIO34 / 35）")],
             [plain("電線"), red("不經過鞋底摩擦面"), plain("，電子件不承受體重")]], 4.2, 1.15, 5.5, 3.5, 15);

// 11 待確認與進度
s = content("九、待確認事項與後續進度", "整合與進度");
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.45, y: 1.05, w: 4.4, h: 3.7, fill: { color: "FDF0DE" }, line: { color: "FDF0DE" }, rectRadius: 0.08 });
s.addShape(pres.shapes.OVAL, { x: 0.65, y: 1.2, w: 0.38, h: 0.38, fill: { color: "D98A00" }, line: { color: "D98A00" } });
s.addText("!", { x: 0.65, y: 1.2, w: 0.38, h: 0.38, fontSize: 16, bold: true, color: "FFFFFF", align: "center", valign: "middle", isTextBox: true, margin: 0 });
s.addText("尚待確認", { x: 1.15, y: 1.2, w: 3.5, h: 0.38, fontFace: "DFKai-SB", fontSize: 17, bold: true, color: "B26A00", valign: "middle", isTextBox: true, margin: 0 });
s.addText(["鞋跟寬是否 ≤ 66 mm（套筒內寬）", "腳跟 → 鞋底後緣距離（暫定 12）", "S2 距腳跟 21 或 25 mm", "電源方式（行動電源 / 18650）"].map((t, i, a) => ({ text: t, options: { bullet: true, breakLine: i < a.length - 1 } })),
  { x: 0.75, y: 1.75, w: 3.95, h: 2.8, fontSize: 14, bold: true, color: "1F1F1F", valign: "top", paraSpaceAfter: 10, isTextBox: true, margin: 0 });
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 5.15, y: 1.05, w: 4.4, h: 3.7, fill: { color: "E6F0EE" }, line: { color: "E6F0EE" }, rectRadius: 0.08 });
s.addShape(pres.shapes.OVAL, { x: 5.35, y: 1.2, w: 0.38, h: 0.38, fill: { color: "1E6B5C" }, line: { color: "1E6B5C" } });
s.addText("→", { x: 5.35, y: 1.2, w: 0.38, h: 0.38, fontSize: 14, bold: true, color: "FFFFFF", align: "center", valign: "middle", isTextBox: true, margin: 0 });
s.addText("下禮拜進度", { x: 5.85, y: 1.2, w: 3.5, h: 0.38, fontFace: "DFKai-SB", fontSize: 17, bold: true, color: "1E6B5C", valign: "middle", isTextBox: true, margin: 0 });
s.addText(["列印共用後段 + 穿鞋前段，試組裝", "感測匣靜態校正（0–40 kg 分階）", "FSR + IMU 同步量測", "穿戴步行測試、檢查潛變"].map((t, i, a) => ({ text: t, options: { bullet: true, breakLine: i < a.length - 1 } })),
  { x: 5.45, y: 1.75, w: 3.95, h: 2.8, fontSize: 14, bold: true, color: "1F1F1F", valign: "top", paraSpaceAfter: 10, isTextBox: true, margin: 0 });

(async () => { await pres.writeFile({ fileName: OUT }); await applyTheme(OUT, THEME); console.log("wrote", OUT); })();
