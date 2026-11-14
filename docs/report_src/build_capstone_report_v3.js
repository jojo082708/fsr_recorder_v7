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
  new Paragraph({ children: [t('承重七公斤之工業搬運用下肢外骨骼：導納控制架構設計與關節致動器鑑別', { size: 32, bold: true })], alignment: AlignmentType.CENTER, spacing: { after: 240 } }),
  new Paragraph({ children: runs('指導老師：王紹宇老師【待確認：指導老師是否正確、是否有共同指導老師】', { size: 22 }), alignment: AlignmentType.CENTER, spacing: { after: 160 } }),
  new Paragraph({ children: [t('組員：蔡朝欽、林均澤、周瑋澤、楊翔安', { size: 22 })], alignment: AlignmentType.CENTER, spacing: { after: 240 } }),
];

const C = [];
C.push(sec('摘要'));
C.push(body('工業現場中重複搬運物品容易造成作業人員下肢與腰部之肌肉疲勞與職業傷害。本專題之目標為開發一套可協助穿戴者承載7 kg搬運物之下肢外骨骼，於髖、膝關節配置主動馬達，以降低穿戴者在搬運過程中之肌肉負擔。控制策略參考尤凱融[12]所提出之導納控制架構：以基於模型之外擾估測器(DOB)估測穿戴者施加之關節力矩作為運動意圖，扣除負載與上半身重量造成之額外力矩後，經導納函數轉換為關節角速度命令，再由馬達之速度迴路執行。本專題由電控組負責控制架構與感測、致動子系統，機構組負責外骨骼結構，目前機構仍在設計中。電控組已完成：(1)每腳兩點FSR加IMU之感測配置與足底量測平台設計，BNO055角速度經修正後誤差小於±0.4%；(2)DOB所需之關節致動器參數鑑別，AK70-9之等效力矩常數為1.24 N·m/A（規格值1.0621 N·m/A），AK60-39為1.98 N·m/A（規格值3.4616 N·m/A），證實規格書參數不能直接用於力矩估測；(3)導納控制架構與感測需求之對照分析，並指出現有感測配置在地面反作用力與軀幹傾角量測上之不足。'));
C.push(new Paragraph({ children: [t('關鍵字：', { bold: true, italics: true }), t('下肢外骨骼、導納控制、外擾估測器、系統鑑別、工業搬運')], alignment: AlignmentType.BOTH, spacing: { before: 60, after: 60 } }));

C.push(sec('1. 前言'));
C.push(body('在物流與製造業中，作業人員經常需要反覆搬運物品並在行走、上下樓梯與蹲站之間轉換，長時間負重容易導致下肢與腰部之肌肉疲勞與職業傷害。下肢外骨骼可將部分負載經由機構傳遞至地面，並以關節馬達提供輔助力矩，被視為改善此問題之可行方案。依用途可分為醫療復健型與工業增強型：醫療復健型著重步態分析，常以多點FSR與多顆IMU完整量測下肢運動[1]；工業增強型則以負荷轉移與輔助出力為目標，例如BLEEX透過感測穿戴者與機構之交互作用達成負重行走[5]。'));
C.push(body('要讓外骨骼與穿戴者同步，必須同時解決「意圖偵測」與「順應性控制」兩個問題[12]。意圖偵測可分為生理訊號（如肌電訊號EMG）與物理訊號（如關節角度、交互力矩）兩類；生理訊號與意圖相關性高，但電極貼附繁瑣且易受干擾，不利於工業現場每日穿脫使用，因此本專題採用物理訊號。尤凱融[12]以基於模型之外擾估測器估測穿戴者關節力矩，並以導納控制將其轉換為關節角速度命令，在前掛20 kg負載下，相較未穿戴外骨骼，平地行走、爬升階梯與蹲站姿態轉換之生理成本指標(PCI)分別降低14.29%、8.82%與50%，驗證了此架構於荷重情境之可行性。'));
C.push(body('本專題以承載7 kg搬運物為目標，參考上述導納控制架構設計下肢外骨骼之控制系統。由於導納控制仰賴準確之動態模型與致動器模型，本報告由電控組撰寫，內容包含：(1)控制架構與感測需求分析；(2)感測元件之配置與準確度驗證；(3)關節致動器之系統鑑別。機構組之外骨骼結構（參考文獻[4]之人機整合設計）尚在設計中，因此與機構幾何及質量相關之參數於本報告中保留待補充，整機承重測試列為後續工作。'));

C.push(sec('2. 研究目標'));
C.push(body('本專題之性能目標與目前狀態如表1所示，功能目標如表2所示。'));
C.push(...table('表1 性能目標與目前狀態', ['項目', '目標', '目前狀態'], [
  ['承載重量', '7 kg搬運物【待確認：前抱、背負或手提】', '機構設計中'],
  ['運動情境', '平地行走、上下樓梯、蹲站轉換【待確認】', '—'],
  ['輔助效果', 'PCI較未穿戴降低【待補充：目標值】', '尚未測試'],
  ['主動關節', '髖、膝各1顆（雙腳共4顆）', '馬達已選定'],
  ['IMU角速度誤差', '< 1%', '±0.4%（同組資料）'],
  ['力矩估測誤差', '【待補充：例如 < 10%】', 'AK70-9 RMSE 5.4–5.8%'],
], [1, 1.6, 1.1]));
C.push(...table('表2 功能目標', ['功能', '說明', '狀態'], [
  ['意圖偵測', '以DOB估測穿戴者關節力矩', '架構完成'],
  ['順應性控制', '以導納函數將力矩轉為角速度命令', '架構完成'],
  ['負載力矩補償', '補償7 kg負載與上半身造成之髖關節力矩', '規劃中'],
  ['步態相位判斷', '以足底FSR判斷著地、離地', '資料蒐集中'],
  ['致動器模型', '以系統鑑別求K_{t}與摩擦參數', '定速部分完成'],
  ['多馬達通訊', '以CAN匯流排控制四顆馬達', '單顆測試完成'],
], [1, 2, 1]));

C.push(sec('3. 承重需求分析'));
C.push(body('依參考文獻[12]之物理模型，將髖關節視為支點，負載與穿戴者上半身合稱為上半身系統，其重量對髖關節造成之額外力矩如式(1)。其中m_{UP}為上半身系統質量（含7 kg負載），q_{B}為軀幹傾角，l_{UPC,h}與l_{UPC,w}為上半身系統質心沿軀幹方向及垂直軀幹方向至髖關節之距離；雙腳視為獨立系統，故每腳承擔一半。'));
C.push(eq('τ_{b,H} = (m_{UP}g/2)[−l_{UPC,h} sin q_{B} + l_{UPC,w} cos q_{B}]', 1));
C.push(body('前抱搬運物時，負載使上半身質心前移，即使穿戴者保持直立（q_{B} = 0），l_{UPC,w}亦不為零，會在髖關節產生持續之額外力矩，且負載愈重影響愈顯著[12]。因此承重7 kg時，此力矩必須在力矩估測中扣除，否則會被誤判為穿戴者之運動意圖。上半身系統質心位置可由穿戴者在數種靜止姿態下之踝關節力矩平衡，以最小平方法估測[12]，此方法需要地面反作用力與壓力中心(CoP)之量測。'));
C.push(body('關節力矩需求須由機構組依外骨骼幾何、質量與步態資料計算。【待補充：外骨骼大腿、小腿長度與質量；7 kg負載之攜帶方式與距髖關節之水平距離；平地行走、上樓梯與蹲站時髖、膝關節之峰值與均方根力矩】先前機構組初估之關節力矩峰值為84.37 N·m【待確認：此值對應之關節、動作與是否含7 kg負載】，高於AK70-9（峰值29.2 N·m）與AK60-39（峰值72 N·m）之能力，需於機構定案後重新檢核馬達選型。'));

C.push(sec('4. 元件選用'));
C.push(sub('4.1 關節馬達'));
C.push(body('導納控制之輸出為關節角速度命令，由馬達內建之速度迴路執行[12]，因此致動器需具備速度控制模式與電流回授以計算馬達負載力矩。CubeMars AK系列整合馬達、行星減速器與驅動器，支援伺服模式（含速度控制）與MIT控制模式，並可經CAN匯流排回傳角度、轉速與q軸電流[6][7][11]，符合上述需求。評估之型號如表3所示。'));
C.push(...table('表3 關節馬達規格比較（規格書值）', ['型號', '減速比', '額定/峰值|力矩 (N·m)', '重量', '額定|電流'], [
  ['AK45-36', '36:1', '8 / 24', '349 g', '2 A'],
  ['AK70-9', '9:1', '8.5 / 29.2', '540 g', '6.25 A'],
  ['AK60-39', '39:1', '24 / 72', '750 g', '4.5 A'],
], [1.1, 0.8, 1.2, 0.8, 0.8]));
C.push(body('髖關節選用AK70-9，其9:1低減速比之回驅力矩約0.8 N·m，有利於穿戴者帶動外骨骼時之順應性；膝關節於蹲站與上樓梯時需較大力矩，故選用峰值72 N·m之AK60-39。此選型以實驗室既有馬達進行控制架構驗證為主，承重7 kg之適用性需待第3節之力矩需求確定後檢核；若不足，以AK80-64（峰值120 N·m）為升級方案。'));
C.push(sub('4.2 感測元件'));
C.push(body('姿態感測選用Bosch BNO055九軸IMU[8]，其內建感測融合可直接輸出姿態角；足底感測選用Interlink FSR 402[9]（外徑18.3 mm、感測區Ø12.7 mm），以串聯10 kΩ之分壓電路接至ESP32之ADC。FSR配置於腳跟與第一蹠骨頭兩點，分別偵測腳跟著地與腳尖離地[1][3]；小腿IMU則於步態事件偵測與角度追蹤上具抗干擾能力[2]。ESP32作為感測控制器，經USB將資料傳至主控制器。參考文獻[12]所使用之感測器與本專題之對照如表4所示。'));
C.push(...table('表4 參考架構[12]與本專題之感測配置對照', ['用途', '參考文獻[12]', '本專題', '差異'], [
  ['軀幹傾角q_{B}', '背部MPU-6050|＋二階互補濾波', 'BNO055|【待確認：是否配置於軀幹】', '目前規劃置於小腿'],
  ['地面反作用力F_{GR}與CoP', '144點壓力感測鞋墊', '每腳2點FSR 402', '無法量測F_{GR}大小與CoP'],
  ['關節角度、電流', 'Maxon馬達編碼器', 'AK馬達編碼器與i_{q}', '相當'],
  ['感測控制器', 'Teensy 4.0', 'ESP32', '相當'],
], [1, 1.3, 1.3, 1.2]));
C.push(body('由表4可知，兩項感測需求尚未滿足。第一，DOB需扣除地面反作用力造成之關節力矩J^{T}F_{GR}，且上半身質心估測需要CoP，但本專題之兩點FSR經止擋限制（見5.3節）後只能判斷觸地狀態，無法提供F_{GR}之大小與作用點。第二，負載力矩補償需要軀幹傾角，現有IMU規劃置於小腿。【待確認：足底感測改用壓力鞋墊或於足底平台加入荷重元；IMU2是否改置於背部】'));
C.push(sub('4.3 控制平台'));
C.push(body('為確認AK馬達之通訊方式，比較四種控制平台如表5所示。PC經R-Link轉接器以Python控制最為穩定，故規劃以Raspberry Pi 4搭配R-Link作為主控制器。【待補充：ESP32搭配MCP2515無法接收回傳之原因】'));
C.push(...table('表5 控制平台架構比較', ['方案', '系統架構', '結果'], [
  ['一', 'PC (Python) + R-Link', '已完成，作為測試平台'],
  ['二', 'Arduino Uno + MCP2515', '已完成，適合快速測試'],
  ['三', 'ESP32 + MCP2515', '失敗，無法接收回傳'],
  ['四', 'Raspberry Pi 4 + R-Link', '規劃中'],
], [0.6, 2, 2]));
C.push(sub('4.4 電源配置'));
C.push(body('馬達端與控制端採電源分離：四顆關節馬達由48 V供電，Raspberry Pi、ESP32與感測器由5 V供電。以規格額定電流估算，馬達端上限約為AK70-9兩顆12.5 A加AK60-39兩顆9.0 A，共21.5 A；此為四顆同時以額定電流運轉之上限，實際值需於承重步行時實測。【待補充：電源型式、電池容量、5 V端耗電與預估續航時間】'));

C.push(sec('5. 控制架構設計'));
C.push(sub('5.1 系統硬體架構'));
C.push(body('系統硬體架構如圖1所示，分為感測系統、主控制端與致動系統。感測系統之IMU以I²C、FSR以ADC連接至ESP32，經USB將資料傳至Raspberry Pi 4；主控制端執行力矩估測與導納控制，經四組R-Link以CAN匯流排對各馬達下達速度命令並接收角度、轉速與電流回授。目前已完成PC經R-Link控制單顆AK馬達。【待補充：CAN鮑率、控制迴圈頻率與通訊延遲】'));
C.push(...fig('f01.png', '圖1 系統硬體架構圖（規劃）'));
C.push(sub('5.2 人體與外骨骼耦合系統模型'));
C.push(body('穿戴者與外骨骼以綁帶緊密結合，可視為一個人體與外骨骼耦合系統(HES)[12]。以髖關節為支點、踝關節為被動關節，單腳之動態方程式如式(2)，其中q = [q_{BH}, q_{K}]^{T}為髖、膝關節角度（q_{BH}含軀幹傾角），M、C、G、B分別為慣量、科氏力、重力與摩擦項，τ_{l}為馬達負載力矩、τ_{h}為穿戴者關節力矩、τ_{b}為上半身系統（含負載）造成之額外力矩，J^{T}F_{GR}為地面反作用力之等效關節力矩。'));
C.push(eq('Mq̈ + Cq̇ + G + B = τ_{l} + τ_{h} + τ_{b} + J^{T}F_{GR}', 2));
C.push(body('式(2)左側可線性參數化為φ(q,q̇,q̈)θ，在外骨骼懸吊且無人穿戴時（τ_{h} = τ_{b} = 0、F_{GR} = 0），以最小平方法求得系統參數向量θ[12]。此步驟需要外骨骼實體，待機構完成後進行。【待補充：外骨骼懸吊鑑別之系統參數表】'));
C.push(sub('5.3 穿戴者關節力矩估測（外擾估測器）'));
C.push(body('將鑑別後之模型代入式(2)左側，得HES總關節力矩之估測值τ̂_{e}，再扣除馬達負載力矩、上半身系統力矩與地面反作用力項，即得穿戴者關節力矩之估測值，如式(3)[12]。估測過程含數值微分，故以低通濾波器Q(s)濾除高頻雜訊後得τ̂_{h,Q}，作為穿戴者之運動意圖。'));
C.push(eq('τ̂_{h} = τ̂_{e} − τ_{l} − τ̂_{b} − J^{T}F_{GR}', 3));
C.push(body('其中馬達負載力矩τ_{l}由q軸電流換算，τ_{l} = K_{t}i_{q}（K_{t}為輸出軸等效力矩常數）。由式(3)可知，K_{t}之誤差會一比一地轉為穿戴者力矩之估測誤差：若AK60-39沿用規格值3.4616 N·m/A而非實測之1.98 N·m/A，τ_{l}將被高估約75%，並被誤判為穿戴者之反向施力。此即本專題先進行致動器系統鑑別（第6.2、6.3節）之原因。'));
C.push(sub('5.4 導納控制'));
C.push(body('導納為力矩與角速度之關係，導納控制將穿戴者力矩映射為關節角速度命令，如式(4)，其中P_{d} = (J_{d}s + B_{d})^{−1}，J_{d}、B_{d}為期望慣量與期望阻尼係數矩陣，τ_{g} = P_{g}(q)為重力項[12]。B_{d}愈小則導納之直流增益1/B_{d}愈大，穿戴者以較小施力即可得到相同角速度，愈省力；B_{d}/J_{d}為一階導納之極點，影響運動速度。'));
C.push(eq('q̇_{c} = P_{d}(τ̂_{h,Q} − τ_{g})', 4));
C.push(body('平地行走與上樓梯時，僅使用一階導納會使大腿擺盪角度過大（文獻[12]中最高約70°），故加入式(5)之重力項，相當於在大腿與小腿加上虛擬重量；抬腿時重力項與穿戴者力矩反向以抑制過大擺盪（降至約40°），放腿時則同向以協助穿戴者[12]。G_{1}、G_{2}為可調之期望重力項係數。'));
C.push(eq('τ_{g} = [G_{1}sin q_{BH} + G_{2}sin(q_{BH}+q_{K}),  G_{2}sin(q_{BH}+q_{K})]^{T}', 5));
C.push(body('角速度命令乘上減速比後送至AK馬達之速度迴路執行，整體架構如圖2所示。參考文獻[12]於平地行走實驗使用之參數為1/B_{d} = 3.333×10^{−4} 1/(mN·m·s)、B_{d}/J_{d} = 1 s^{−1}、G_{1} = 30000 mN·m、G_{2} = 10000 mN·m，可作為初始值；但本專題之外骨骼質量、馬達與速度迴路特性不同，參數須重新調整。文獻[12]歸納之調參順序為：依省力需求調B_{d}、依速度需求調J_{d}，再依小腿與大腿擺盪範圍調G_{2}與G_{1}。'));
C.push(...fig('f_adm.png', '圖2 導納控制架構方塊圖（依參考文獻[12]，以本專題硬體繪製）'));
C.push(body('【待補充：情境切換（行走、上樓梯、蹲站）之判斷方式，可結合足底FSR與IMU】【待補充：安全機制，包含關節角度軟體限位、角速度與電流上限、緊急停止開關及通訊中斷時之處理】'));

C.push(sub('5.5 足底量測平台'));
C.push(body('為在不修改鞋子之前提下量測足底觸地狀態，設計外穿式雙點足底量測平台如圖3所示。感測點S1位於第一蹠骨頭、S2位於腳跟，剖面如圖4所示，受力路徑為鞋底→TPU 95A導槽→Ø5鋼珠→保護傳力片→FSR 402→支撐座→底板。TPU下沉超過1.0 mm時由止擋分擔負載，FSR最大受力依TPU壓縮模型估算約69 N【待確認：需以砝碼或荷重元校正】。由於承重7 kg時單腳負載遠大於69 N，止擋作用後FSR僅量測總負載之一部分，故此平台適用於判斷著地、離地與步態相位，不能提供式(3)所需之F_{GR}大小。目前平台為設計階段，尚未列印與實測。'));
C.push(...fig('f02.png', '圖3 FSR與IMU整合式足部量測平台'));
C.push(...fig('f_sec.png', '圖4 S1感測匣A-A剖面圖（節錄自工程圖FSR-09，單位：mm）', 230));

C.push(sec('6. 實驗結果與討論'));
C.push(sub('6.1 IMU量測準確度驗證'));
C.push(body('BNO055靜態測試中，三軸雜訊RMS皆小於0.017 m/s²、分段漂移小於0.04 m/s²。四面靜態重力測試中，NDOF模式倒放之量值誤差為−3.12%、側放(2)為−2.29%，超過±2%之合格標準，正放與倒放之配對偏值為0.145 m/s²；改用IMUPLUS模式後倒放誤差為−2.70%，仍未合格。由於軀幹傾角之靜態估測仰賴加速度計[12]，此偏移需先校正。滑車實驗中，運動方向加速度為離軸分量之25倍以上，試次間變異係數在1.2%以內，證實座標鎖定正常。'));
C.push(body('角速度實驗如圖5所示，將IMU固定於3D列印連桿上，以AK馬達分別於5、10、20、30 rpm各量測三次，並以馬達回傳轉速為參考值，結果如表6所示。IMU原始值固定偏大約3.1%，試次間變異係數僅0.05～0.35%，屬比例誤差；以線性回歸得修正式(6)後，誤差降至±0.4%以內。此修正式由同一組資料求得並驗證，尚需以獨立資料確認【待補充：獨立驗證資料】【待確認：10/08報告之修正式為(ω_{IMU} − 0.098)/1.0310，10/29報告為ω_{IMU}/1.0310，請確認最終版本】。'));
C.push(eq('ω_{true} = (ω_{IMU} − 0.098) / 1.0310', 6));
C.push(...fig('f03.png', '圖5 IMU角速度實驗流程與架設'));
C.push(...table('表6 IMU角速度量測結果 (deg/s)', ['設定轉速', '馬達', 'IMU原始', '誤差', '修正後誤差'], [
  ['5 rpm', '29.989', '30.900', '+3.04%', '−0.38%'],
  ['10 rpm', '59.982', '61.895', '+3.19%', '−0.07%'],
  ['20 rpm', '119.985', '124.179', '+3.50%', '+0.31%'],
  ['30 rpm', '179.987', '185.444', '+3.03%', '−0.12%'],
], [1, 1, 1, 0.9, 1.1]));
C.push(body('角加速度實驗設定馬達以1 rpm/s（6.000 deg/s²）加速至30 rpm，IMU微分值與馬達回傳值之三次平均分別為5.963與5.944 deg/s²，誤差約0.3%。步態中關節角加速度遠大於此值，結果僅代表低加速度條件【待補充：高角加速度驗證】。'));

C.push(sub('6.2 AK70-9系統鑑別'));
C.push(body('鑑別模型如式(7)，定速旋轉時θ̈ ≈ 0且單一轉向下摩擦為常數，可簡化為式(8)，τ_{g} = mgL為重力力矩幅值、τ_{f}為摩擦力矩、φ為零點偏移。擷取穩態資料以式(9)進行最小平方擬合[10]，再由τ_{g} = K_{t}√(a^{2}+b^{2})、τ_{f} = K_{t}c_{0}換算；已知τ_{g} = mgL時可反求K_{t}。'));
C.push(eq('K_{t}i_{q} = Jθ̈ + Bθ̇ + τ_{c} + mgL sinθ', 7));
C.push(eq('K_{t}i_{q} ≈ τ_{f} + τ_{g} sin(θ + φ)', 8));
C.push(eq('i_{q} = c_{0} + a sinθ + b cosθ', 9));
C.push(body('實驗配置如圖6所示，以300 mm力臂分別懸掛1.5 kg與3 kg鋼片，於3～10 rpm每1 rpm一組共16組定速測試，以VESC Tool約32 Hz記錄角度、轉速與q軸電流；θ = 190°～230°區段因鋼片滑動而剔除【待補充：實驗台照片】。3 kg之力矩響應如圖7所示，結果整理於表7。'));
C.push(...fig('f04.png', '圖6 AK70-9實驗配置示意圖', 150));
C.push(...fig('f05.png', '圖7 AK70-9負載響應（3 kg，以規格K_t換算）'));
C.push(...table('表7 AK70-9重力力矩鑑別結果 (N·m)', ['負載', '理論τ_{g}', '實測平均*', '實測/理論', 'R^{2}'], [
  ['1.5 kg', '4.41', '3.87', '87.6%', '0.993'],
  ['3 kg', '8.83', '7.64', '86.5%', '0.992'],
], [1, 1, 1, 1, 0.9]));
C.push(plain('*以規格力矩常數1.0621 N·m/A換算', { size: 16, align: AlignmentType.CENTER }));
C.push(body('兩種負載之實測力矩皆約為理論值之87%，屬比例誤差，表示規格力矩常數偏低；回歸得等效力矩常數1.24 N·m/A，較規格值高約17%。摩擦力矩以庫倫摩擦為主，負載加倍時由約0.29增加至0.51 N·m，故DOB中之摩擦項應考慮負載相依性。3～10 rpm內重力力矩隨轉速變化小於1.5%，但瞬間轉速波動約±10%（3 kg、3 rpm時達+39%）。模型與實測比較如圖8，R^{2} = 0.992、RMSE為τ_{g}之5.4～5.8%；R^{2}僅代表正弦重力模型能描述力矩隨角度之變化，K_{t}之絕對準確度仍需外部力矩量測驗證【待補充：荷重元或扭力計驗證】。此外，步態轉速約30～60 rpm且含加減速，慣量J與高轉速下之摩擦尚未鑑別【待補充】。'));
C.push(...fig('f06.png', '圖8 AK70-9模型與實測數據比較（3 kg、3 rpm）'));

C.push(sub('6.3 AK60-39系統鑑別'));
C.push(body('AK60-39以相同方法進行定速3 rpm測試，另以力臂水平抬升與下放兩位置之平均電流估算重力電流幅值G = (i_{90} − i_{270})/2，使固定偏移互相抵消【待確認：最終採用之力臂長度與負載組合（10/22報告為0.35 m、1.1與2.4 kg；11/12報告圖示為0.3 m、1.5、3與4.5 kg）】。以規格力矩常數3.4616 N·m/A換算時，實測力矩明顯大於mgL；多次實驗後求得等效力矩常數為1.98 N·m/A，代回後與重力模型吻合，如圖9所示【待補充：1.98 N·m/A之求得方式、各負載估計值、標準差與R^{2}】。'));
C.push(...fig('f07.png', '圖9 AK60-39重力力矩與實測比較（K_t = 1.98 N·m/A）'));
C.push(body('差異之可能原因包括驅動器i_{q}回報尺度（伺服與MIT模式之換算、等幅值與等功率座標轉換）、規格力矩常數之定義條件，以及馬達減磁或電流限制，皆屬尚待驗證之假設【待補充：以電流勾表量測相電流，並比較兩種模式下之i_{q}回報值】。對導納控制而言，重點在於以實測K_{t}計算τ_{l}，以避免式(3)之系統性誤差。'));

C.push(sub('6.4 FSR特性與多情境量測'));
C.push(body('以固定重物施壓評估FSR之潛變與重複性，潛變率(%) = (V_{final} − V_{initial})/V_{initial} × 100，結果如圖10與表8。現有三組資料未呈現一致之負載趨勢，且測試負載（約0.6～1.0 N）遠小於承重步行之足底負載，故僅供參考【待補充：以足底平台於0～40 kg（承重7 kg時需涵蓋穿戴者體重加負載之單腳負荷）進行校正】。'));
C.push(...fig('f09.png', '圖10 FSR固定重物施壓量測（57.4 g）'));
C.push(...table('表8 FSR固定重物施壓量測結果', ['負載', '潛變率', '穩定時間', '重複性'], [
  ['57.4 g', '14.68%', '115 s', '—'],
  ['77.0 g', '16.15% / 12.8%', '40 s / 20 s', '2.4%'],
  ['106.8 g', '6.86% / 3.55%', '40 s / 10 s', '1.6%'],
], [0.9, 1.3, 1.2, 0.8]));
C.push(body('多情境量測於站立、行走、上樓梯與下樓梯下記錄腳跟FSR之電壓變化率，如圖11【待補充：受測者人數、感測器固定方式與取樣頻率】。站立時訊號於0附近微幅震盪；行走時出現頻率最高、正負對稱之尖波；上樓梯時頻率變慢、前足波形變寬；下樓梯時腳跟出現較密集之尖波。上述差異顯示兩點FSR可作為情境切換與步態相位判斷之依據，但需以定量特徵與辨識準確率驗證。'));
C.push(...fig('f10.png', '圖11 多情境腳跟FSR電壓變化率'));

C.push(sec('7. 後續工作規劃'));
C.push(body('依與機構組之相依性，後續工作分為兩階段。第一階段不需外骨骼實體：(1)以荷重元驗證兩款馬達之K_{t}，並鑑別慣量與30～60 rpm之摩擦；(2)於AK70-9單關節實驗台實作導納控制，以手推力臂驗證DOB估測力矩與角速度命令之關係，並以文獻[12]參數為初始值調整J_{d}、B_{d}；(3)決定足底F_{GR}量測方案與軀幹IMU配置，完成足底平台列印與校正；(4)完成Raspberry Pi與四顆馬達之CAN同步控制與安全機制。第二階段待機構完成後：(5)懸吊鑑別HES系統參數；(6)上半身系統質心估測與負載力矩補償；(7)穿戴者前掛7 kg負載進行平地行走、上樓梯與蹲站實驗，並參考文獻[12]以心率計算PCI，比較穿戴與未穿戴之耗能差異。'));

C.push(sec('8. 結論'));
C.push(body('本專題以承載7 kg之工業搬運用下肢外骨骼為目標，參考文獻[12]建立「外擾估測器＋導納控制」之控制架構，並完成電控組可先行之驗證工作。主要結果如下：(1)BNO055角速度存在約+3.1%之比例誤差，修正後於同組資料中小於±0.4%，加速度計存在零點偏移需先校正；(2)AK70-9等效力矩常數為1.24 N·m/A、AK60-39為1.98 N·m/A，與規格值差異顯著，由於K_{t}誤差會直接轉為穿戴者力矩之估測誤差，系統鑑別為導納控制之必要前置步驟；(3)比對參考架構後，指出現有兩點FSR無法提供地面反作用力大小與壓力中心、IMU未配置於軀幹，為承重控制尚待解決之感測缺口。機構完成前，將先於單關節實驗台驗證導納控制，以縮短整機整合之時程。'));

C.push(sec('9. 誌謝'));
C.push(body('感謝王紹宇老師在馬達系統鑑別、控制理論與實驗規劃上之指導。感謝機構組同學在外骨骼結構設計上之合作，以及實驗室學長姐在硬體採購與實驗操作上之協助。感謝國立聯合大學機械工程學系提供實驗場地與設備資源。'));

C.push(sec('10. 參考文獻'));
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
  'Ljung, L. (1999). System identification: Theory for the user (2nd ed.). Prentice Hall.',
  'Katz, B., Di Carlo, J., & Kim, S. (2019). Mini Cheetah: A platform for pushing the limits of dynamic quadruped control. In Proc. IEEE International Conference on Robotics and Automation (pp. 6295–6301).',
  '尤凱融（2023）。《應用於多種運動情境之下肢外骨骼導納控制策略設計》（碩士論文）。國立陽明交通大學電控工程研究所，新竹市。',
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
