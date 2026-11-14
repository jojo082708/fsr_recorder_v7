// 國立聯合大學機械工程學系 專題製作成果報告（下肢外骨骼電控組）
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, Header,
  AlignmentType, WidthType, BorderStyle, TabStopType, SectionType, VerticalAlign,
} = require('docx');

const FIG = process.argv[2];
const OUT = process.argv[3];

const F = { ascii: 'Times New Roman', hAnsi: 'Times New Roman', eastAsia: '標楷體', cs: 'Times New Roman' };
const COL = 4663;           // 單欄寬 (DXA)
const TBL = 4600;           // 表格寬
const t = (text, o = {}) => new TextRun({ text, font: o.font || F, size: o.size || 20, bold: o.bold, italics: o.italics, color: o.color, underline: o.underline, superScript: o.sup, subScript: o.sub });

// 段落文字支援 _下標_ 與 ^上標^ 的簡單標記
function runs(text, o = {}) {
  if (/【[^】]*】/.test(text) && !o._r) {
    return text.split(/(【[^】]*】)/).filter(Boolean).flatMap((p) => p.startsWith('【') ? runs(p, { ...o, _r: 1, color: 'C00000' }) : runs(p, { ...o, _r: 1 }));
  }
  const out = [];
  const re = /(_\{[^}]+\}|\^\{[^}]+\})/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(t(text.slice(last, m.index), o));
    const inner = m[0].slice(2, -1);
    out.push(t(inner, { ...o, sub: m[0][0] === '_', sup: m[0][0] === '^' }));
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push(t(text.slice(last), o));
  return out;
}

const body = (text) => new Paragraph({ children: runs(text), alignment: AlignmentType.BOTH, indent: { firstLine: 400 }, spacing: { line: 250, after: 0 } });
const plain = (text, o = {}) => new Paragraph({ children: runs(text, o), alignment: o.align || AlignmentType.BOTH, spacing: { line: 250, after: 0 }, indent: o.indent });
const sec = (text) => new Paragraph({ children: [t(text, { size: 24, bold: true })], alignment: AlignmentType.CENTER, spacing: { before: 200, after: 100 }, keepNext: true });
const sub = (text) => new Paragraph({ children: [t(text, { size: 20, bold: true })], spacing: { before: 100, after: 20 }, keepNext: true });
const gap = () => new Paragraph({ children: [t('', { size: 8 })], spacing: { after: 0 } });

const figs = [];
function fig(file, caption, widthPx = 300) {
  const data = fs.readFileSync(path.join(FIG, file));
  const w = data.readUInt32BE(16), h = data.readUInt32BE(20);
  const height = Math.round(widthPx * h / w);
  return [
    new Paragraph({ children: [new ImageRun({ type: 'png', data, transformation: { width: widthPx, height } })], alignment: AlignmentType.CENTER, spacing: { before: 80, after: 20 }, keepNext: true }),
    new Paragraph({ children: [t(caption, { size: 18 })], alignment: AlignmentType.CENTER, spacing: { after: 100 } }),
  ];
}

const border = { style: BorderStyle.SINGLE, size: 4, color: '000000' };
const borders = { top: border, bottom: border, left: border, right: border };
function table(caption, header, rows, widths) {
  const sum = widths.reduce((a, b) => a + b, 0);
  widths = widths.map((w) => Math.round(w * TBL / sum));
  widths[widths.length - 1] += TBL - widths.reduce((a, b) => a + b, 0);
  const cell = (txt, w, bold) => new TableCell({
    borders, width: { size: w, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
    margins: { top: 30, bottom: 30, left: 60, right: 60 },
    children: String(txt).split('|').map((line) => new Paragraph({ children: runs(line, { size: 17, bold }), alignment: AlignmentType.CENTER, spacing: { line: 220 } })),
  });
  return [
    new Paragraph({ children: [t(caption, { size: 18 })], alignment: AlignmentType.CENTER, spacing: { before: 100, after: 40 }, keepNext: true }),
    new Table({
      width: { size: TBL, type: WidthType.DXA }, columnWidths: widths, alignment: AlignmentType.CENTER,
      rows: [
        new TableRow({ tableHeader: true, children: header.map((h, i) => cell(h, widths[i], true)) }),
        ...rows.map((r) => new TableRow({ cantSplit: true, children: r.map((c, i) => cell(c, widths[i], false)) })),
      ],
    }),
    new Paragraph({ children: [t('', { size: 10 })], spacing: { after: 60 } }),
  ];
}

const MF = { ascii: 'Cambria Math', hAnsi: 'Cambria Math', eastAsia: '標楷體', cs: 'Cambria Math' };
function eq(text, n) {
  return new Paragraph({
    tabStops: [{ type: TabStopType.CENTER, position: Math.round(COL / 2) }, { type: TabStopType.RIGHT, position: COL - 20 }],
    spacing: { before: 60, after: 60 }, keepLines: true,
    children: [t('\t'), ...runs(text, { font: MF, size: 20, italics: true }), t(`\t(${n})`)],
  });
}

// ---------------- 頁首 ----------------
const nob = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const header = new Header({
  children: [
    new Table({
      width: { size: 9752, type: WidthType.DXA }, columnWidths: [6600, 3152],
      borders: { top: nob, bottom: nob, left: nob, right: nob, insideHorizontal: nob, insideVertical: nob },
      rows: [new TableRow({ children: [
        new TableCell({ borders: { top: nob, bottom: nob, left: nob, right: nob }, width: { size: 6600, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({ children: [t('國立聯合大學機械工程學系 '), t('  115  ', { underline: {} }), t(' 學年度專題製作成果報告')] })] }),
        new TableCell({ borders, width: { size: 3152, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER, margins: { top: 40, bottom: 40, left: 80, right: 80 },
          children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [t('組別: '), t('■', { color: 'FF0000' }), t('實作組'), t('□'), t('設計組')] })] }),
      ] })],
    }),
    new Paragraph({ children: [t('', { size: 10 })] }),
  ],
});

// ---------------- 標題區（單欄） ----------------
const titleBlock = [
  new Paragraph({ children: [t('', { size: 20 })] }),
  new Paragraph({ children: [t('下肢外骨骼之FSR與IMU步態感測驗證及關節馬達系統鑑別', { size: 32, bold: true })], alignment: AlignmentType.CENTER, spacing: { after: 240 } }),
  new Paragraph({ children: runs('指導老師：王紹宇老師【待確認：指導老師是否正確、是否有共同指導老師】', { size: 22 }), alignment: AlignmentType.CENTER, spacing: { after: 160 } }),
  new Paragraph({ children: [t('組員：蔡朝欽、林均澤、周瑋澤、楊翔安', { size: 22 })], alignment: AlignmentType.CENTER, spacing: { after: 240 } }),
];

const C = [];
C.push(sec('摘要'));
C.push(body('下肢外骨骼之重力補償與順從控制，取決於感測訊號之可信度與關節致動器模型之準確度。本專題由電控組負責感測與致動子系統之驗證，規劃以Raspberry Pi 4為主控制器、ESP32為感測控制器，經R-Link以CAN匯流排驅動髖關節AK70-9與膝關節AK60-39之分散式架構。感測方面，提出每腳兩點FSR 402（腳跟與第一蹠骨頭）加小腿一顆BNO055之精簡配置，並設計外穿式鋼珠傳力FSR足底量測平台。IMU角速度於5～30 rpm範圍內原始誤差約+3.1%，以線性回歸修正後於同組資料中誤差小於±0.4%；角加速度於6 deg/s²條件下誤差約0.3%。致動方面，以定速旋轉實驗配合最小平方法鑑別關節馬達參數：AK70-9於1.5 kg與3 kg負載下，以規格力矩常數換算之重力力矩僅為理論值之約87%，回歸所得等效力矩常數為1.24 N·m/A（規格值1.0621 N·m/A）；AK60-39之等效力矩常數為1.98 N·m/A（規格值3.4616 N·m/A）。結果顯示規格書力矩常數不能直接用於力矩估測，系統鑑別為後續重力補償與阻抗控制之必要步驟。'));
C.push(new Paragraph({ children: [t('關鍵字：', { bold: true, italics: true }), t('下肢外骨骼、系統鑑別、力矩常數、力感測電阻(FSR)、慣性量測單元(IMU)')], alignment: AlignmentType.BOTH, spacing: { before: 60, after: 60 } }));

C.push(sec('1. 前言'));
C.push(body('下肢外骨骼依用途可分為醫療復健型與工業增強型。醫療復健型著重步態分析與異常診斷，文獻建議於足底配置7點FSR、於雙腳、小腿、大腿與骨盆配置4顆IMU，以重建完整之足底壓力分佈與下肢運動學[1]；然而多點感測使線路與校正負擔增加、耐用度降低。工業增強型外骨骼以負荷轉移與輔助出力為目標，例如BLEEX透過感測穿戴者與機構之交互作用達成負重行走[5]，其感測系統需兼顧耐用性、低運算負擔與快速響應。'));
C.push(body('外骨骼之重力補償、摩擦補償與阻抗控制，皆建立在「q軸電流與輸出力矩之對應關係」之上。若直接採用規格書之力矩常數，而未考慮減速機效率、摩擦與驅動器電流回報尺度，輸出力矩將產生系統性偏差，進而影響人機互動之安全性。同樣地，低成本之FSR與MEMS IMU具有潛變、偏值與比例誤差，須經實驗驗證後方能作為控制回授訊號。'));
C.push(body('本專題由電控組與機構組分工進行，機構組負責外骨骼結構設計與關節力矩需求分析[4]，電控組之工作範圍為：(1)規劃每腳2 FSR + 1 IMU之感測配置，設計足底量測平台並驗證IMU量測準確度；(2)以系統鑑別求得髖、膝關節馬達之等效力矩常數與摩擦力矩；(3)規劃CAN匯流排多馬達控制架構與阻抗控制方法。本報告呈現目前已完成之驗證結果，並明確區分已完成與規劃中之項目。'));

C.push(sec('2. 研究目標'));
C.push(body('本專題之性能目標與目前達成狀態如表1所示，功能目標如表2所示。關節活動範圍與適用腿長為機構組之設計規格，列出以作為電控系統之設計邊界。'));
C.push(...table('表1 性能目標與達成狀態', ['項目', '目標', '目前狀態'], [
  ['髖關節活動範圍', '−25°～100°', '設計值'], ['膝關節活動範圍', '0°～105°', '設計值'],
  ['適用腿長', '大腿390–470 mm|小腿370–450 mm', '設計值'],
  ['IMU角速度誤差', '< 1%', '±0.4%（同組資料）'],
  ['關節力矩估測誤差', '【待補充：請訂定目標，例如 < 10%】', 'AK70-9 RMSE為τ_{g}之5.4–5.8%'],
  ['控制迴圈週期', '【待補充】', '尚未實測'],
], [1.1, 1.3, 1.3]));
C.push(...table('表2 功能目標', ['功能', '說明', '狀態'], [
  ['動作意圖辨識', '以2 FSR + 1 IMU判斷站立、行走、上下樓梯', '資料蒐集中'],
  ['關節力矩估測', '以系統鑑別建立K_{t}、摩擦與重力模型', '定速部分完成'],
  ['順從控制', '以阻抗模型依外力修正目標角度', '規劃中'],
  ['多馬達通訊', '以CAN匯流排控制四顆關節馬達', '單顆測試完成'],
], [1, 2, 1]));

C.push(sec('3. 元件選用'));
C.push(sub('3.1 感測元件選用'));
C.push(body('足底壓力感測選用Interlink FSR 402[9]（外徑18.3 mm、感測區Ø12.7 mm），其厚度薄且價格低，適合嵌入足底平台；以串聯10 kΩ電阻之分壓電路接至ESP32之ADC1（GPIO34/35）。姿態感測選用Bosch BNO055九軸IMU[8]，其內建感測融合可直接輸出姿態角，用以取代先前使用之MPU6050，降低主控制器之運算負擔。ESP32作為感測控制器，負責FSR類比訊號擷取與IMU之I²C通訊，並以USB將資料傳送至主控制器。'));
C.push(sub('3.2 關節馬達扭力評估與選用'));
C.push(body('依機構組之步態動力學分析，關節力矩峰值約為84.37 N·m【待補充：此值為髖或膝關節、對應之動作（起立、行走或上樓梯）、穿戴者體重與負重條件，以及關節力矩對步態週期之曲線】。考量成本與實驗室現有資源，評估CubeMars三款整合式關節模組如表3所示，三者皆整合馬達、行星減速器與驅動器，並支援伺服模式與MIT控制模式[6][7][12]。'));
C.push(...table('表3 關節馬達規格比較（規格書值）', ['型號', '減速比', '額定/峰值|力矩 (N·m)', '重量', '額定|電流'], [
  ['AK45-36', '36:1', '8 / 24', '349 g', '2 A'],
  ['AK70-9', '9:1', '8.5 / 29.2', '540 g', '6.25 A'],
  ['AK60-39', '39:1', '24 / 72', '750 g', '4.5 A'],
], [1.1, 0.8, 1.2, 0.8, 0.8]));
C.push(body('髖關節選用AK70-9，其9:1低減速比之回驅力矩約0.8 N·m，有利於擺盪期之順應性；膝關節選用兩級行星減速、峰值72 N·m之AK60-39；AK45-36峰值僅24 N·m且實驗室無現貨，故未採用。須注意的是，兩款馬達之峰值力矩皆低於84.37 N·m，且峰值力矩僅能短時間輸出，連續步行應以額定力矩評估。因此現階段之選型以實驗室既有馬達進行感測與鑑別驗證為主，整機穿戴時須以限制負載情境或升級AK80-64（峰值120 N·m）因應【待確認：與機構組確認各關節之峰值與均方根力矩需求後，重新檢核選型】。'));
C.push(sub('3.3 控制平台選用'));
C.push(body('為確認AK馬達之通訊方式，比較四種控制平台如表4所示。ESP32搭配MCP2515時無法接收馬達回傳狀態【待補充：失敗原因，例如CAN鮑率、終端電阻或程式設定】；PC經R-Link轉接器以Python控制最為穩定，故規劃以Raspberry Pi 4搭配R-Link作為主控制器。'));
C.push(...table('表4 控制平台架構比較', ['方案', '系統架構', '結果'], [
  ['一', 'PC (Python) + R-Link', '已完成，作為測試平台'],
  ['二', 'Arduino Uno + MCP2515', '已完成，適合快速測試'],
  ['三', 'ESP32 + MCP2515', '失敗，無法接收回傳'],
  ['四', 'Raspberry Pi 4 + R-Link', '規劃中'],
], [0.6, 2, 2]));
C.push(sub('3.4 電源配置與耗電評估'));
C.push(body('馬達端與控制端採電源分離：四顆關節馬達由48 V供電，Raspberry Pi、ESP32與感測器由5 V供電，避免馬達瞬間大電流造成控制器重置或感測訊號失真。以規格書額定電流估算之馬達端耗電如表5所示；此為四顆馬達同時以額定電流運轉之上限估計，實際步行時之平均電流需以實測決定。'));
C.push(...table('表5 馬達端耗電估算（規格額定值，48 V）', ['項目', '數量', '額定電流', '小計'], [
  ['AK70-9（髖）', '2', '6.25 A', '12.5 A'],
  ['AK60-39（膝）', '2', '4.5 A', '9.0 A'],
  ['合計', '4', '—', '21.5 A'],
], [1.6, 0.7, 1, 1]));
C.push(body('【待補充：5 V端（Raspberry Pi 4、ESP32、IMU、FSR）之耗電、電源型式（電源供應器或電池）、電池容量與預估續航時間】'));

C.push(sec('4. 控制架構設計'));
C.push(sub('4.1 系統架構'));
C.push(body('系統架構如圖1所示，分為感測系統、主控制端與致動系統。感測系統之兩顆IMU以I²C、四顆FSR以ADC連接至ESP32，經USB將感測資料傳至Raspberry Pi 4；主控制端以Python執行控制程式，經四組R-Link轉接器以CAN匯流排對各馬達下達指令並接收回授。目前已完成PC經R-Link控制單顆AK馬達，Raspberry Pi之系統建置與四顆馬達同步控制尚在進行中【待補充：CAN鮑率、控制命令更新頻率與通訊延遲】。'));
C.push(...fig('f01.png', '圖1 系統架構圖（規劃）'));
C.push(sub('4.2 感測配置與濾波器設計'));
C.push(body('相較於醫療步態分析之7點FSR配置[1]，工業外骨骼僅需辨識動作意圖與步態事件，故本專題採每腳2 FSR + 1 IMU之配置。腳跟FSR用以偵測腳跟著地（Heel Strike）；第一蹠骨頭（大拇趾球）FSR位於步態末期推進之主要受力點，其訊號歸零可判斷腳尖離地（Toe Off）[3]。小腿IMU於步態事件偵測與連續角度追蹤上具抗干擾能力[2]，可提供角速度、俯仰角與垂直加速度，用以區分上、下樓梯。'));
C.push(body('規劃之判斷邏輯為：雙腳FSR皆持續受壓且電壓變化率小時判定為站立；兩腳FSR交替受壓且出現週期性尖波時判定為行走；尖波週期較長並配合小腿IMU垂直加速度方向判定為上、下樓梯。【待補充：各狀態之判斷門檻值（電壓變化率、頻率或週期）及其決定方式】【待補充：辨識準確率實驗，建議以至少3名受測者、每情境10次以上之混淆矩陣呈現】'));
C.push(body('濾波方面，FSR採硬體RC低通濾波，於ADC取樣前濾除高頻雜訊並兼具抗混疊功能【待補充：R、C元件值與截止頻率f_{c} = 1/(2πRC)，以及ADC取樣頻率】；IMU先以中值濾波剔除單點突波，再以二階Butterworth低通濾波器平滑訊號，在通帶平坦度與相位延遲之間取得平衡【待確認：截止頻率於5～8 Hz中之最終選定值，以及濾波前後之相位延遲實測】。'));
C.push(sub('4.3 外穿式FSR足底量測平台'));
C.push(body('為在不修改原有布鞋之前提下量測足底壓力，設計外穿式雙點足底量測平台如圖2所示。感測點S1位於第一蹠骨頭、S2位於腳跟，剖面如圖3所示，受力路徑為鞋底→TPU 95A導槽→Ø5鋼珠→保護傳力片→FSR 402→支撐座→底板，使足底分佈力集中傳遞至FSR感測區。TPU下沉超過止擋間隙（1.0 mm）時，外環坐上止擋肩分擔負載，FSR最大受力依TPU 95A壓縮模型估算約為69 N【待確認：此值為估算，需以標準砝碼或荷重元校正】。'));
C.push(body('由於步行時單腳承受之體重遠大於69 N，止擋作用後FSR僅量測總負載之一部分，因此FSR輸出代表「觸地與否及負載變化趨勢」，而非絕對足底力；若需換算為力量，須建立平台整體之負載—電壓校正曲線【待補充：0～40 kg分階靜態校正結果】。平台採共用後段與可換前段之模組化設計，以6支M4螺絲鎖合；穿鞋版外形為349×134 mm、赤腳版為299×122 mm，赤腳時加入12 mm腳跟墊塊使兩種用法之感測位置相同。目前平台為設計階段，尚未列印與實測。'));
C.push(...fig('f02.png', '圖2 FSR與IMU整合式足部量測平台'));
C.push(...fig('f_sec.png', '圖3 S1感測匣A-A剖面圖（節錄自工程圖FSR-09，單位：mm）', 230));

C.push(sec('5. 系統鑑別與控制方法'));
C.push(sub('5.1 關節馬達模型'));
C.push(body('以力臂末端懸掛負載之單關節模型描述馬達輸出力矩，如式(1)。其中K_{t}為換算至輸出軸之等效力矩常數（已包含減速比與減速機效率）、i_{q}為驅動器回報之q軸電流、J為等效轉動慣量、B為黏滯阻尼係數、τ_{c}為庫倫摩擦力矩，θ = 0°定義為力臂垂直向下；負載視為質點，力臂自身質量【待確認：力臂質量與重心位置，若不可忽略需加入重力項】。'));
C.push(eq('τ = K_{t}i_{q} = Jθ̈ + Bθ̇ + τ_{c} + mgL sinθ', 1));
C.push(body('定速旋轉時θ̈ ≈ 0，且單一轉向下摩擦力矩為常數，模型可簡化為式(2)，其中τ_{g} = mgL為重力力矩幅值、τ_{f} = τ_{c} + Bθ̇為摩擦力矩、φ為編碼器零點偏移與量測延遲造成之相位。'));
C.push(eq('τ ≈ τ_{f} + τ_{g} sin(θ + φ)', 2));
C.push(sub('5.2 最小平方法參數估測'));
C.push(body('擷取穩態區間（去除啟動後2 s與停止前0.5 s）之角度與電流資料，以式(3)進行線性最小平方擬合[11]，再由式(4)換算重力力矩與摩擦力矩。每一圈各擬合一次，統計平均值與最大、最小值；θ = 190°～230°區段因負載鋼片越過最高點後滑動而剔除。'));
C.push(eq('i_{q} = c_{0} + a sinθ + b cosθ', 3));
C.push(eq('τ_{g} = K_{t}√(a^{2}+b^{2}),  τ_{f} = K_{t}c_{0}', 4));
C.push(body('若已知τ_{g} = mgL，則等效力矩常數可由K_{t} = mgL / √(a^{2}+b^{2})求得。AK60-39另以力臂水平抬升（φ = 90°）與水平下放（φ = 270°）兩位置之平均電流估算重力電流幅值，如式(5)，兩位置共有之固定偏移（摩擦）可互相抵消。'));
C.push(eq('G = (i_{90} − i_{270}) / 2', 5));
C.push(sub('5.3 阻抗控制方法（規劃）'));
C.push(body('為使外骨骼對穿戴者施力具順從性，規劃採用位置基礎之阻抗控制[10]，架構如圖4所示。外迴路以虛擬質量M_{v}、虛擬阻尼B_{v}與虛擬剛性K_{v}構成之阻抗模型，依估測外力修正目標軌跡，如式(6)，其中θ_{e} = θ_{cmd} − θ_{d}，穩態時θ_{cmd} = θ_{d} + τ̂_{ext}/K_{v}。內迴路以PD控制器追蹤修正後之目標角度，如式(7)；外力則由馬達電流扣除慣性、摩擦與重力項估測，如式(8)，其中K_{t}、τ̂_{c}與τ̂_{g}採用第6.2、6.3節之鑑別結果。'));
C.push(eq('M_{v}θ̈_{e} + B_{v}θ̇_{e} + K_{v}θ_{e} = τ̂_{ext}', 6));
C.push(eq('i_{q,cmd} = K_{p}(θ_{cmd} − θ) − K_{D}ω', 7));
C.push(eq('τ̂_{ext} = K_{t}i_{q} − (Ĵα + B̂ω + τ̂_{c} + τ̂_{g})', 8));
C.push(...fig('f_block.png', '圖4 阻抗控制方塊圖（規劃）'));
C.push(body('【待補充：阻抗參數M_{v}、B_{v}、K_{v}與PD增益之設定值與選定依據，以及單關節阻抗控制實驗結果】【待補充：安全機制，包含關節角度軟體限位、力矩/電流上限、緊急停止開關與通訊中斷時之處理方式】'));

C.push(sec('6. 實驗結果與討論'));
C.push(sub('6.1 IMU量測準確度驗證'));
C.push(body('首先進行BNO055靜態測試，將IMU以正放、側放與立放各靜置5分鐘，三軸雜訊RMS皆小於0.017 m/s²、分段漂移皆小於0.04 m/s²。四面靜態重力測試中，NDOF模式倒放之重力量值誤差為−3.12%、側放(2)為−2.29%，超過±2%之合格標準，正放與倒放之配對偏值為0.145 m/s²；改用IMUPLUS模式後倒放誤差降為−2.70%，仍未合格，顯示加速度計存在零點偏移，以加速度二次積分求位移時需先行校正。滑車實驗中，運動方向之加速度為離軸分量之25倍以上，試次間變異係數在1.2%以內，證實座標鎖定功能正常；但二次積分位移受起始時間判定影響，誤差介於−2.67%～+6.67%。'));
C.push(body('角速度實驗如圖5所示，將IMU固定於3D列印連桿上，以AK馬達分別於5、10、20、30 rpm各量測三次，並以CubeMars介面回傳之轉速為參考值。結果如表6所示，IMU原始值固定偏大約3.1%，試次間變異係數僅0.05～0.35%，屬比例誤差而非隨機誤差；以線性回歸得修正式(9)後，誤差降至±0.4%以內。須注意此修正式係由同一組資料求得並驗證，尚需以獨立資料（不同轉速或另一次量測）確認其泛化能力【待補充：獨立驗證資料】【待確認：修正式於10/08報告為(ω_{IMU} − 0.098)/1.0310，10/29報告為ω_{IMU}/1.0310，請確認最終採用之版本】。'));
C.push(eq('ω_{true} = (ω_{IMU} − 0.098) / 1.0310', 9));
C.push(...fig('f03.png', '圖5 IMU角速度實驗流程與架設'));
C.push(...table('表6 IMU角速度量測結果 (deg/s)', ['設定轉速', '馬達', 'IMU原始', '誤差', '修正後誤差'], [
  ['5 rpm', '29.989', '30.900', '+3.04%', '−0.38%'],
  ['10 rpm', '59.982', '61.895', '+3.19%', '−0.07%'],
  ['20 rpm', '119.985', '124.179', '+3.50%', '+0.31%'],
  ['30 rpm', '179.987', '185.444', '+3.03%', '−0.12%'],
], [1, 1, 1, 0.9, 1.1]));
C.push(body('角加速度實驗設定馬達以1 rpm/s（6.000 deg/s²）加速至30 rpm，將IMU角速度微分後與馬達回傳值比較，三次平均分別為5.963與5.944 deg/s²，誤差約0.3%。然而步態中關節角加速度可達數百deg/s²以上，本實驗之加速度範圍遠低於實際應用，結果僅能證明低加速度下之準確度【待補充：較高角加速度（例如步階或正弦掃頻）之驗證】。'));

C.push(sub('6.2 AK70-9系統鑑別'));
C.push(body('實驗配置如圖6所示，以300 mm力臂分別懸掛1.5 kg與3 kg鋼片，於3～10 rpm每1 rpm一組共16組定速測試，以VESC Tool約32 Hz記錄角度、轉速與q軸電流【待補充：實驗台實體照片】。3 kg負載之力矩響應如圖7所示，曲線形狀與正弦重力模型一致，27圈之最大、最小值差異小，重複性高。'));
C.push(...fig('f04.png', '圖6 AK70-9實驗配置示意圖', 150));
C.push(...fig('f05.png', '圖7 AK70-9負載響應（3 kg，以規格K_t換算）'));
C.push(...table('表7 AK70-9重力力矩鑑別結果 (N·m)', ['負載', '理論τ_{g}', '實測平均*', '實測/理論', 'R^{2}'], [
  ['1.5 kg', '4.41', '3.87', '87.6%', '0.993'],
  ['3 kg', '8.83', '7.64', '86.5%', '0.992'],
], [1, 1, 1, 1, 0.9]));
C.push(plain('*以規格力矩常數1.0621 N·m/A換算', { size: 16, align: AlignmentType.CENTER }));
C.push(body('由表7可知，兩種負載之實測力矩皆約為理論值之87%，比例一致，屬比例誤差而非固定偏移，表示以電流換算力矩時所用之力矩常數偏低；以兩種負載回歸得等效力矩常數1.24 N·m/A，較規格值高約17%。摩擦力矩與轉速之關係不明顯，以庫倫摩擦為主，但負載加倍時由約0.29增加至0.51 N·m，顯示摩擦隨負載增加，摩擦補償應考慮負載相依性。3～10 rpm內重力力矩隨轉速之變化小於1.5%，平均轉速皆達設定值之99.5%以上，但瞬間轉速波動約±10%，在3 kg、3 rpm時達+39%。'));
C.push(body('模型與實測之比較如圖8所示，平均決定係數R^{2} = 0.992，RMSE分別為0.24與0.51 N·m（約為τ_{g}之5.4%與5.8%）。須說明的是，R^{2}係將擬合參數代回同一組資料計算，僅表示正弦重力模型能描述力矩隨角度之變化形狀，並不代表力矩常數之絕對準確度；力矩常數之準確度仍需以外部力矩量測（如荷重元或扭力計）驗證【待補充：外部力矩量測驗證】。'));
C.push(...fig('f06.png', '圖8 AK70-9模型與實測數據比較（3 kg、3 rpm）'));

C.push(sub('6.3 AK60-39系統鑑別'));
C.push(body('AK60-39以相同方法進行定速3 rpm測試【待確認：最終採用之力臂長度（10/22報告為0.35 m、1.1與2.4 kg；11/12報告圖示為0.3 m、1.5、3與4.5 kg），以及各條件之重複次數】。以說明書力矩常數3.4616 N·m/A換算時，實測力矩明顯大於純重量重力力矩mgL；多次實驗後求得等效力矩常數為1.98 N·m/A，代回後三種負載之實測曲線與重力模型吻合，如圖9所示【待補充：1.98 N·m/A之求得方式（回歸或平均）、各負載之估計值、標準差與R^{2}】。'));
C.push(...fig('f07.png', '圖9 AK60-39重力力矩與實測比較（K_t = 1.98 N·m/A）'));
C.push(body('造成差異之可能原因包括：(1)驅動器之i_{q}回報尺度與規格書定義不同，例如伺服模式與MIT模式之換算路徑不同，或電流以等幅值與等功率座標轉換表示時相差固定比例；(2)規格力矩常數之定義條件（馬達端或輸出端、是否含減速機效率）與本實驗不同；(3)馬達減磁或供電電流限制。規格值與實測值之比約為1.75，與√3（約1.732）接近，屬於值得驗證之線索；但AK70-9之比值約為0.86，兩款馬達之差異方向相反，因此目前無法以單一尺度因子解釋，上述原因皆屬尚待驗證之假設【待補充：以電流勾表或示波器量測相電流，並比較伺服與MIT兩種模式下之i_{q}回報值】。'));

C.push(sub('6.4 FSR特性與多情境足底壓力量測'));
C.push(body('為評估FSR作為步態判斷依據之可靠度，以固定重物施壓並定義潛變率(%) = (V_{final} − V_{initial})/V_{initial} × 100；穩定時間為電壓變化率連續三次介於±0.01 V/s所需之時間，取樣間隔為5 s【待確認：電壓變化率之單位與取樣間隔】；重複性為兩次量測之末端電壓差除以5 V滿刻度。57.4 g施壓之結果如圖10所示，各重量之結果整理於表8。'));
C.push(...fig('f09.png', '圖10 FSR固定重物施壓量測（57.4 g）'));
C.push(...table('表8 FSR固定重物施壓量測結果', ['負載', '潛變率', '穩定時間', '重複性'], [
  ['57.4 g', '14.68%', '115 s', '—'],
  ['77.0 g', '16.15% / 12.8%', '40 s / 20 s', '2.4%'],
  ['106.8 g', '6.86% / 3.55%', '40 s / 10 s', '1.6%'],
], [0.9, 1.3, 1.2, 0.8]));
C.push(body('77.0 g與106.8 g兩組之第二次量測潛變率皆低於第一次，106.8 g之潛變率明顯低於前兩組，但57.4 g與77.0 g之間並無一致趨勢，現有三組資料不足以建立潛變率與負載之關係；且測試負載（約0.6～1.0 N）遠小於步行時之足底負載。【待補充：以足底平台在實際負載範圍（0～40 kg）進行靜態校正與長時間潛變測試，每負載至少重複3次】'));
C.push(body('多情境量測於站立、行走、上樓梯與下樓梯四種情境下記錄FSR電壓變化率，腳跟FSR之結果如圖11所示【待補充：受測者人數、感測器固定方式（膠帶黏貼或足底平台）、取樣頻率與每情境量測時間】。定性觀察顯示：站立時訊號於0附近微幅震盪（約±0.05）；行走時出現頻率最高、正負對稱之尖波，分別對應腳底踩下與抬起；上樓梯時頻率變慢，第一蹠骨頭FSR波形變寬，反映前足長時間支撐推進；下樓梯時腳跟FSR出現較密集之尖波。上述差異顯示兩點FSR具有區分動作情境之潛力，但仍需以定量特徵（尖波頻率、峰值、觸地時間比例）與辨識準確率加以驗證。'));
C.push(...fig('f10.png', '圖11 多情境腳跟FSR電壓變化率'));

C.push(sub('6.5 3D列印下肢外骨骼整合規劃'));
C.push(body('參考文獻[4]之人機整合設計，本專題與機構組完成3D列印下肢外骨骼之設計，髖關節配置AK70-9、膝關節配置AK60-39，大腿長度可調390～470 mm、小腿370～450 mm，活動範圍為髖關節−25°～100°、膝關節0°～105°。歸零時將腿部伸直並插入Ø6歸零銷，再將馬達角度設為零，使四顆馬達具有一致之角度基準。各姿態之運動模擬如圖12所示，實體列印與組裝尚在進行中。'));
C.push(...fig('f11.png', '圖12 3D列印下肢外骨骼各姿態模擬'));

C.push(sec('7. 結論'));
C.push(body('本專題完成下肢外骨骼感測與致動子系統之初步驗證，主要結果如下：(1)BNO055角速度於5～30 rpm範圍內存在約+3.1%之比例誤差，經線性修正後於同組資料中誤差小於±0.4%；加速度計存在零點偏移，四面重力測試部分姿態未達±2%標準。(2)AK70-9於1.5 kg與3 kg、3～10 rpm定速條件下，正弦重力模型可描述力矩隨角度之變化（R^{2} = 0.992），等效力矩常數為1.24 N·m/A，較規格值高約17%；摩擦以庫倫摩擦為主並隨負載增加。(3)AK60-39之等效力矩常數為1.98 N·m/A，與規格值3.4616 N·m/A差異顯著。上述結果顯示，以規格書力矩常數直接換算力矩將產生明顯誤差，系統鑑別為重力補償與阻抗控制之必要步驟。'));
C.push(body('目前尚未完成之項目包括：力矩常數之外部力矩驗證與i_{q}尺度差異之原因確認、轉動慣量J與步態轉速範圍（30～60 rpm）之鑑別、足底平台之列印與負載校正、動作辨識門檻與準確率實驗、Raspberry Pi多馬達整合、單關節阻抗控制實驗與安全機制，以及整機穿戴測試。'));

C.push(sec('8. 誌謝'));
C.push(body('感謝王紹宇老師在馬達系統鑑別、控制理論與實驗規劃上之指導。感謝機構組同學提供關節力矩需求與外骨骼結構設計，以及實驗室學長姐在硬體採購與實驗操作上之協助。感謝國立聯合大學機械工程學系提供實驗場地與設備資源。'));

C.push(sec('9. 參考文獻'));
const refs = [
  'Manna, S. K., et al. (2023). Optimal locations and computational frameworks of FSR and IMU sensors for measuring gait abnormalities. Heliyon, 9(4), e15210. https://doi.org/10.1016/j.heliyon.2023.e15210',
  'Sánchez Manchola, M. D., et al. (2019). Gait phase detection for lower-limb exoskeletons using foot motion data from a single inertial measurement unit in hemiparetic individuals. Sensors, 19(13), 2988.',
  '【待補充：作者與年份】Bluetooth-enabled FSR-equipped insole prototype for gait asymmetry correction. California State University ScholarWorks. https://scholarworks.calstate.edu/downloads/nv935c35z',
  'Zhao, C., et al. (2025). Mechanical structure design and motion simulation analysis of a lower limb exoskeleton rehabilitation robot based on human–machine integration. Sensors, 25(5), 1611.',
  'Kazerooni, H., Racine, J.-L., Huang, L., & Steger, R. (2005). On the control of the Berkeley Lower Extremity Exoskeleton (BLEEX). In Proc. IEEE International Conference on Robotics and Automation (pp. 4353–4360).',
  'CubeMars. (n.d.). AK70-9 KV60 robotic actuator [Product page]. Retrieved 【待補充：查閱日期】, from https://www.cubemars.com/',
  'CubeMars. (n.d.). AK60-39 V3.0 KV80 robotic actuator [Product page]. Retrieved 【待補充：查閱日期】, from https://www.cubemars.com/',
  'Bosch Sensortec. (n.d.). BNO055 intelligent 9-axis absolute orientation sensor [Datasheet].',
  'Interlink Electronics. (n.d.). FSR 400 series force sensing resistor integration guide [Datasheet].',
  'Hogan, N. (1985). Impedance control: An approach to manipulation: Part I—Theory. Journal of Dynamic Systems, Measurement, and Control, 107(1), 1–7.',
  'Ljung, L. (1999). System identification: Theory for the user (2nd ed.). Prentice Hall.',
  'Katz, B., Di Carlo, J., & Kim, S. (2019). Mini Cheetah: A platform for pushing the limits of dynamic quadruped control. In Proc. IEEE International Conference on Robotics and Automation (pp. 6295–6301).',
];
refs.forEach((r, i) => C.push(new Paragraph({ children: runs(`[${i + 1}] ${r}`, { size: 18 }), alignment: AlignmentType.LEFT, indent: { left: 360, hanging: 360 }, spacing: { line: 230, after: 20 } })));
const margin = { top: 1134, bottom: 1134, left: 1077, right: 1077, header: 567, footer: 567 };
const doc = new Document({
  styles: { default: { document: { run: { font: F, size: 20 } } } },
  sections: [
    { properties: { page: { margin } }, headers: { default: header }, children: titleBlock },
    { properties: { type: SectionType.CONTINUOUS, page: { margin }, column: { count: 2, space: 425, equalWidth: true } }, headers: { default: header }, children: C },
  ],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(OUT, b); console.log('wrote', OUT); });
