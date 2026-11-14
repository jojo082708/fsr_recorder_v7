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
  new Paragraph({ children: [t('整合FSR與IMU步態感測之下肢外骨骼電控系統開發與關節馬達系統鑑別', { size: 32, bold: true })], alignment: AlignmentType.CENTER, spacing: { after: 240 } }),
  new Paragraph({ children: [t('指導老師：王紹宇老師', { size: 22 })], alignment: AlignmentType.CENTER, spacing: { after: 160 } }),
  new Paragraph({ children: [t('組員：蔡朝欽、林均澤、周瑋澤、楊翔安', { size: 22 })], alignment: AlignmentType.CENTER, spacing: { after: 240 } }),
];

// ---------------- 內文（雙欄） ----------------
const C = [];
C.push(sec('摘要'));
C.push(body('隨著工業搬運與高齡照護需求增加，下肢外骨骼被視為降低穿戴者肌肉負荷的重要輔具，而其控制效果取決於感測訊號的可信度與致動器模型的準確度。本專題聚焦於下肢外骨骼之電控系統，建置以Raspberry Pi為主控制器、ESP32為感測控制器，並經R-Link以CAN匯流排驅動四顆CubeMars關節馬達（髖關節AK70-9、膝關節AK60-39）之分散式架構。感測方面，提出「2 FSR + 1 IMU」動作辨識配置，以腳跟與大拇趾球兩點FSR 402偵測著地與離地，並以小腿BNO055量測角速度與姿態，同時設計外穿式鋼珠式FSR足底量測平台。致動方面，以定速旋轉實驗配合最小平方法進行馬達系統鑑別，AK70-9之重力力矩模型平均決定係數R^{2}達0.992，等效力矩常數為1.24 N·m/A，較規格值高約17%；AK60-39實測力矩常數修正為1.98 N·m/A。IMU角速度經回歸修正後誤差由3.1%降至±0.4%以內，角加速度誤差約0.3%。此外以QUBE-Servo 3完成M-B-K阻抗控制之閉迴路驗證，並建立FSR潛變率、穩定時間與重複性之評估指標，作為後續重力補償、單關節阻抗控制與整機步態控制之基礎。'));
C.push(new Paragraph({ children: [t('關鍵字：', { bold: true, italics: true }), t('下肢外骨骼、系統鑑別、阻抗控制、力感測電阻(FSR)、慣性量測單元(IMU)')], alignment: AlignmentType.BOTH, spacing: { before: 60, after: 60 } }));

C.push(sec('1. 前言'));
C.push(body('經產業調查與文獻回顧後發現，目前的下肢外骨骼依用途可分為醫療復健型與工業增強型兩類。醫療復健型著重步態分析與異常診斷，文獻建議於足底配置7點FSR並於雙腳、小腿、大腿與骨盆配置4顆IMU，以完整重建足底壓力分佈與下肢運動學[1]；然而多點感測帶來線路複雜、校正繁瑣與耐用度低等問題。工業增強型外骨骼則以負荷轉移與輔助出力為主要目標，例如BLEEX即透過感測穿戴者與機構間的交互作用來達成負重行走[5]，其需求為耐用、低運算負擔與快速響應。'));
C.push(body('在控制層面，外骨骼的重力補償、摩擦補償與阻抗控制皆需依賴「下多少電流、出多少力矩」的致動器模型。若直接採用規格書所列之力矩常數，忽略實際摩擦與量測誤差，將使輸出力矩產生系統性偏差，進而影響人機互動的安全性與舒適度。同樣地，低成本感測器（如FSR與MEMS IMU）具有潛變、偏值與比例誤差，必須經過實驗驗證才能作為控制器的回授訊號。'));
C.push(body('本專題由電控組負責下肢外骨骼之感測、致動與控制架構，與機構組分工合作。機構組依步態分析提供關節力矩需求與3D列印外骨骼結構[4]，電控組則完成以下工作：(1)建立「2 FSR + 1 IMU」動作辨識配置與足底量測平台，並驗證IMU量測之準確度；(2)以系統鑑別求得髖、膝關節馬達之實際力矩常數與摩擦力矩；(3)規劃CAN匯流排多馬達控制架構，並以QUBE-Servo 3驗證阻抗控制演算法，作為後續整機控制之基礎。'));

C.push(sec('2. 研究目標'));
C.push(body('本專題預計達成之性能以關節活動範圍、適用腿長與量測及模型準確度訂定目標如表1所示；功能方面預計建置動作意圖辨識、關節力矩估測、順從控制與多馬達通訊如表2所示。'));
C.push(...table('表1 性能目標', ['性能', '目標'], [
  ['髖關節活動範圍', '−25°～100°'], ['膝關節活動範圍', '0°～105°'], ['適用腿長', '大腿 390–470 mm|小腿 370–450 mm'],
  ['IMU角速度量測誤差', '< 1%'], ['關節力矩模型擬合度', 'R^{2} > 0.95'], ['阻抗控制迴圈週期', '2 ms'],
], [1, 1.2]));
C.push(...table('表2 功能目標', ['功能', '說明'], [
  ['動作意圖辨識', '以2 FSR + 1 IMU判斷站立、行走與上下樓梯'],
  ['關節力矩估測', '以系統鑑別建立τ = K_{t}·i_{q}與重力、摩擦模型'],
  ['順從控制', '以M-B-K阻抗模型依外力修正目標角度'],
  ['多馬達通訊', '以CAN匯流排同步控制四顆關節馬達'],
], [1, 2]));

C.push(sec('3. 元件選用'));
C.push(sub('3.1 感測元件選用'));
C.push(body('足底壓力感測選用Interlink FSR 402[9]，具厚度薄、價格低且易於嵌入足底的優點，以串聯10 kΩ電阻之分壓電路接至ESP32之ADC1（GPIO34/35）。姿態感測選用Bosch BNO055九軸IMU[8]，其內建感測融合引擎可直接輸出姿態角，取代原先使用之MPU6050，以降低主控制器之運算負擔與積分漂移。感測控制器選用ESP32，同時負責FSR類比訊號擷取與IMU之I²C通訊，再以USB將感測資料傳送至主控制器。'));
C.push(sub('3.2 關節馬達扭力評估與選用'));
C.push(body('依機構組之步態動力學分析，下肢關節力矩峰值約為84.37 N·m。考量成本與實驗室現有資源，評估CubeMars三款整合式關節模組如表3所示，三者皆整合馬達、行星減速器與驅動器，並支援伺服模式與MIT阻抗控制模式[6][7][13]。'));
C.push(...table('表3 關節馬達規格比較', ['型號', '減速比', '額定/峰值|力矩 (N·m)', '重量', '額定|電流'], [
  ['AK45-36', '36:1', '8 / 24', '349 g', '2 A'],
  ['AK70-9', '9:1', '8.5 / 29.2', '540 g', '6.25 A'],
  ['AK60-39', '39:1', '24 / 72', '750 g', '4.5 A'],
], [1.1, 0.8, 1.2, 0.8, 0.8]));
C.push(body('髖關節選用AK70-9，其9:1低減速比之回驅扭矩僅0.8 N·m，順應性佳，有利於擺盪期的人機協調；膝關節需在起立與承重時輸出較大力矩，故選用兩級行星減速、峰值72 N·m之AK60-39。雙腿共需四顆馬達（AK70-9與AK60-39各兩顆）。由於AK60-39峰值仍低於84.37 N·m之估算峰值，後續將以限制負載情境或升級AK80-64（峰值120 N·m）作為備案。'));
C.push(sub('3.3 控制平台選用'));
C.push(body('為確認AK馬達之通訊方式，本專題比較四種控制平台如表4所示。其中ESP32搭配MCP2515時馬達無法回傳狀態，而PC經R-Link轉接器以Python控制最為穩定，故最終規劃以Raspberry Pi 4搭配R-Link作為嵌入式主控制器。'));
C.push(...table('表4 控制平台架構比較', ['方案', '系統架構', '結果'], [
  ['一', 'PC (Python) + R-Link', '已完成，作為測試平台'],
  ['二', 'Arduino Uno + MCP2515', '已完成，適合快速測試'],
  ['三', 'ESP32 + MCP2515', '測試失敗，馬達無法回傳'],
  ['四', 'Raspberry Pi 4 + R-Link', '規劃中，最終主控制器'],
], [0.6, 2, 2]));
C.push(sub('3.4 電源配置與耗電評估'));
C.push(body('馬達端與控制端採電源分離設計：四顆關節馬達由48 V電源供電，Raspberry Pi、ESP32與各感測器則由5 V電源供電，避免馬達瞬間大電流造成控制器重置或感測訊號失真。依規格書額定電流估算之馬達耗電量如表5所示。'));
C.push(...table('表5 馬達耗電量表（規格額定值）', ['項目', '數量', '額定電流', '小計'], [
  ['AK70-9（髖）', '2', '6.25 A', '12.5 A'],
  ['AK60-39（膝）', '2', '4.5 A', '9.0 A'],
  ['總計（48 V）', '4', '—', '21.5 A'],
], [1.6, 0.7, 1, 1]));

C.push(sec('4. 控制架構設計與研製'));
C.push(sub('4.1 系統架構'));
C.push(body('系統架構如圖1所示，分為感測系統、主控制端與致動系統三部分。感測系統之兩顆IMU以I²C、四顆FSR以ADC連接至ESP32感測控制器，經USB將感測資料傳至Raspberry Pi 4；主控制端以Python執行控制程式，再透過四組R-Link轉接器以CAN匯流排對每顆馬達進行指令下達與狀態回授，形成完整的閉迴路系統。'));
C.push(...fig('f01.png', '圖1 系統架構圖'));
C.push(sub('4.2 感測配置與濾波器設計'));
C.push(body('相較於醫療步態分析之7點FSR配置[1]，工業外骨骼僅需辨識使用者之動作意圖，故本專題提出每腳「2 FSR + 1 IMU」之精簡配置。腳跟為步行時最先著地的部位，可捕捉腳跟著地（Heel Strike）之衝擊訊號；大拇趾球則為步態末期推進的主要受力點，其數值歸零可判斷腳尖離地（Toe Off）。小腿IMU在步態事件偵測與連續角度追蹤上具有抗干擾能力[2]，可提供角速度、俯仰角與垂直加速度，用以區分上、下樓梯。動作辨識邏輯為：雙腳FSR受壓且斜率小為站立[3]；斜率大且頻率高為行走；斜率大但頻率較低為上下樓梯。'));
C.push(body('濾波方面，FSR採硬體RC低通濾波，於ADC取樣前濾除鞋內摩擦與衝擊之高頻雜訊，兼具抗混疊功能且不消耗微控制器運算資源；IMU則先以中值濾波剔除單點突波，再以截止頻率5～8 Hz之二階Butterworth低通濾波器平滑訊號，在通帶平坦與相位延遲之間取得平衡，以滿足馬達即時響應之需求。'));
C.push(sub('4.3 外穿式FSR足底量測平台'));
C.push(body('為在不拆解、不開孔、不修改原有布鞋的前提下量測足底壓力，本專題設計外穿式雙點足底量測平台如圖2所示。感測點S1位於大拇趾球、S2位於腳跟，受力路徑為鞋底→TPU 95A導槽→Ø5鋼珠→保護片→FSR 402→支撐座→底板，使集中力準確傳遞至感測區；當下沉超過1 mm時由止擋分擔負載，將FSR受力限制於約69 N以下作為過載保護。平台採模組化設計，共用後段與可換前段以6支M4螺絲鎖合，穿鞋版尺寸為349×134 mm、赤腳版為299×122 mm，赤腳時加入12 mm腳跟墊塊，使兩種用法之感測器位置相同。FSR走線經底板走線槽與後跟杯出線孔引出，電子元件不承受體重。'));
C.push(...fig('f02.png', '圖2 FSR與IMU整合式足部量測模型'));

C.push(sec('5. 系統鑑別與控制方法'));
C.push(sub('5.1 關節馬達動態模型'));
C.push(body('以力臂固定負載之單關節模型描述馬達輸出力矩，其動態方程式如式(1)，其中K_{t}為力矩常數、i_{q}為q軸電流、J為等效轉動慣量、B為黏滯阻尼係數、τ_{c}為庫倫摩擦，θ = 0°定義為力臂垂直向下。'));
C.push(eq('τ = K_{t}i_{q} = Jθ̈ + Bθ̇ + τ_{c} + mgL sinθ', 1));
C.push(body('於定速旋轉條件下θ̈ ≈ 0，慣性項消失，模型可簡化為式(2)，其中τ_{g} = mgL為重力力矩幅值、τ_{f}為摩擦力矩、φ為編碼器零點偏移與量測延遲所造成之相位。'));
C.push(eq('τ ≈ τ_{f} + τ_{g} sin(θ + φ)', 2));
C.push(sub('5.2 最小平方法參數估測'));
C.push(body('擷取穩態區間（去除啟動後2秒與停止前0.5秒）之角度與電流資料，以式(3)進行最小平方擬合，再由式(4)換算重力力矩[12]、摩擦力矩與相位。每一圈各擬合一次並統計平均值與最大、最小值；θ = 190°～230°區段因負載鋼片越過最高點後偏移而剔除。'));
C.push(eq('i_{q} = c_{0} + a sinθ + b cosθ', 3));
C.push(eq('τ_{g} = K_{t}√(a^{2}+b^{2}),  τ_{f} = K_{t}c_{0}', 4));
C.push(body('AK60-39另以力臂水平抬升（φ = 90°）與水平下放（φ = 270°）兩點之平均電流求得重力力矩，如式(5)，兩點共有之固定偏移可互相抵消。'));
C.push(eq('G = (i_{90} − i_{270}) / 2', 5));
C.push(sub('5.3 阻抗控制'));
C.push(body('為使外骨骼對穿戴者施力具順從性，採用位置基礎之阻抗控制[10][11]。外迴路以虛擬質量M、阻尼B與剛性K構成之阻抗模型，依外力τ_{ext}修正目標軌跡θ_{cmd}，如式(6)；穩態時θ_{cmd} = θ_{d} + τ_{ext}/K。內迴路以PD控制器追蹤修正後之目標並輸出電壓，如式(7)，輸出電壓限制於±10 V以內；外力則由馬達電流扣除自身慣量與摩擦消耗估測而得，如式(8)，並回授至阻抗模型形成閉迴路。'));
C.push(eq('Mθ̈_{cmd} + Bθ̇_{cmd} + K(θ_{cmd} − θ_{d}) = τ_{ext}', 6));
C.push(eq('V = K_{p}(θ_{cmd} − θ) − K_{d}ω', 7));
C.push(eq('τ_{ext} = K_{t}I − (Jα + Bω)', 8));

C.push(sec('6. 實驗結果與討論'));
C.push(sub('6.1 IMU量測準確度驗證'));
C.push(body('首先進行BNO055靜態測試，將IMU以正放、側放與立放各靜置5分鐘，三軸雜訊RMS皆小於0.017 m/s²、分段漂移皆小於0.04 m/s²，均符合合格標準。滑車實驗中，運動方向之加速度為離軸分量的25倍以上，且試次間變異係數皆在1.2%以內，證實NDOF模式之座標鎖定功能正常。'));
C.push(body('角速度實驗如圖3所示，將IMU固定於3D列印連桿上，以AK馬達分別在5、10、20、30 RPM下各量測三次，並與CubeMars介面回傳之轉速比較。結果如表6所示，IMU原始值固定偏大約3.1%，試次間變異係數僅0.05～0.35%，顯示屬比例誤差而非隨機誤差；經回歸得修正式(9)後，誤差降至±0.4%以內。'));
C.push(eq('ω_{true} = (ω_{IMU} − 0.098) / 1.0310', 9));
C.push(...fig('f03.png', '圖3 IMU角速度實驗流程與架設'));
C.push(...table('表6 IMU角速度量測結果 (deg/s)', ['設定轉速', '馬達', 'IMU原始', '誤差', '修正後誤差'], [
  ['5 RPM', '29.989', '30.900', '+3.04%', '−0.38%'],
  ['10 RPM', '59.982', '61.895', '+3.19%', '−0.07%'],
  ['20 RPM', '119.985', '124.179', '+3.50%', '+0.31%'],
  ['30 RPM', '179.987', '185.444', '+3.03%', '−0.12%'],
], [1, 1, 1, 0.9, 1.1]));
C.push(body('角加速度實驗設定馬達以1 RPM/s（6.000 deg/s²）加速至30 RPM，將IMU角速度微分後與馬達回傳值比較，三次平均分別為5.963與5.944 deg/s²，誤差約0.3%，試次間變異係數約0.1%，可提供機構組作為動力學分析之輸入數據。'));

C.push(sub('6.2 AK70-9系統鑑別'));
C.push(body('實驗配置如圖4所示，以300 mm力臂分別懸掛1.5 kg與3 kg鋼片，在3～10 RPM每1 RPM一組共16組定速測試，以VESC Tool約32 Hz記錄角度、轉速與q軸電流。3 kg負載之力矩響應如圖5所示，曲線形狀與理論正弦一致，27圈之最大、最小值差距極小，重複性高。'));
C.push(...fig('f04.png', '圖4 AK70-9實驗配置示意圖', 150));
C.push(...fig('f05.png', '圖5 AK70-9負載響應（3 kg）'));
C.push(...table('表7 AK70-9重力力矩鑑別結果 (N·m)', ['負載', '理論τ_{g}', '實測平均', '實測/理論', 'R^{2}'], [
  ['1.5 kg', '4.41', '3.87', '87.6%', '0.993'],
  ['3 kg', '8.83', '7.64', '86.5%', '0.992'],
], [1, 1, 1, 1, 0.9]));
C.push(body('由表7可知，兩種負載之實測力矩皆約為理論值之87%，屬固定比例誤差而非偏移，顯示規格力矩常數1.0621 N·m/A需要修正；以兩種負載回歸得等效力矩常數1.24 N·m/A，較規格值高約17%。摩擦力矩與轉速關係不明顯，以庫倫摩擦為主，但負載加倍時由約0.29增加至0.51 N·m；3～10 RPM內重力力矩隨轉速之變化小於1.5%，平均轉速皆達設定值之99.5%以上。以鑑別參數建立之模型與實測比較如圖6所示，兩者幾乎重疊，RMSE分別為0.24與0.51 N·m，僅占理論τ_{g}之5.4%與5.8%，證實正弦重力模型可用於重力補償。'));
C.push(...fig('f06.png', '圖6 AK70-9模型模擬與實測數據比較'));

C.push(sub('6.3 AK60-39系統鑑別'));
C.push(body('AK60-39以相同方法於1.5、3與4.5 kg負載下進行定速3 RPM測試。若以說明書力矩常數3.4616 N·m/A換算，實測力矩明顯大於純重量重力矩mgL；經多次實驗後求得修正力矩常數為1.98 N·m/A，三種負載之實測曲線皆與重力模型吻合，如圖7所示，且再現性高，故後續控制以1.98 N·m/A作為計算標準。'));
C.push(...fig('f07.png', '圖7 AK60-39純重量重力矩與實測比較（K_t = 1.98 N·m/A）'));
C.push(body('造成誤差的可能原因包括：(1)馬達曾過熱或承受過大電流導致磁鐵減磁，或供電電流限制過低；(2)i_{q}回報尺度有誤，伺服模式與MIT模式之換算路徑不同，且相電流峰值採等幅值或等功率座標轉換時會相差一個比例係數。值得注意的是，規格值與修正值之比約為1.75，接近√3，推測座標轉換尺度不一致為主要原因，將於後續以外部電流量測進一步驗證。'));

C.push(sub('6.4 阻抗控制驗證'));
C.push(body('在導入AK馬達前，先以QUANSER QUBE-Servo 3驗證阻抗控制演算法，實驗現場如圖8所示。控制參數設定為K_{p} = 20 V/rad、K_{d} = 0.5 V·s/rad，阻抗模型為M = 0.05 kg·m²、B = 0.1 N·m·s/rad、K = 1.0 N·m/rad，控制週期2 ms。以手推旋臂施加約0.3 N·m外力時，阻抗模型將目標角度由0修正至穩態0.3 rad，旋臂隨外力順從讓步；外力移除後，阻尼項使旋臂緩慢歸位而不震盪，驗證三條回授路徑（角度、角速度與外力）構成之閉迴路可正常運作。'));
C.push(...fig('f08.png', '圖8 QUBE-Servo 3阻抗控制實驗'));

C.push(sub('6.5 FSR特性與多情境足底壓力量測'));
C.push(body('為評估FSR作為步態判斷依據之可靠度，以固定重物施壓並定義潛變率(%) = (V_{final} − V_{initial})/V_{initial} × 100，穩定時間則為連續三次電壓變化率介於±0.01之時間。57.4 g施壓結果如圖9所示，各重量之結果整理於表8。負載愈大潛變率愈低，106.8 g時重複性達1.6%，顯示FSR於較大負載下較為穩定，而小負載下之潛變需以濾波或模型補償處理。'));
C.push(...fig('f09.png', '圖9 FSR固定重物施壓量測（57.4 g）'));
C.push(...table('表8 FSR固定重物施壓量測結果', ['負載', '潛變率', '穩定時間', '重複性'], [
  ['57.4 g', '14.68%', '115 s', '—'],
  ['77.0 g', '16.15% / 12.8%', '40 s / 20 s', '2.4%'],
  ['106.8 g', '6.86% / 3.55%', '40 s / 10 s', '1.6%'],
], [0.9, 1.3, 1.2, 0.8]));
C.push(body('多情境量測於站立、行走、上樓梯與下樓梯四種情境下記錄FSR電壓變化率，腳跟FSR之結果如圖10所示。站立時訊號在0附近微幅震盪（約±0.05）；行走時出現頻率最高且正負對稱之尖波，分別對應腳底踩下與抬起；上樓梯時頻率變慢，大拇趾球FSR波形變寬，反映前足需長時間支撐推進；下樓梯時腳跟FSR出現多次急促尖波，反映腳跟以較大衝擊踩落。上述差異證實2 FSR配置足以區分四種動作情境。'));
C.push(...fig('f10.png', '圖10 多情境足跟FSR電壓變化率'));

C.push(sub('6.6 3D列印下肢外骨骼整合'));
C.push(body('參考文獻[4]之人機整合設計，本專題與機構組完成3D列印下肢外骨骼之設計，髖關節配置AK70-9、膝關節配置AK60-39，大腿長度可調整390～470 mm、小腿370～450 mm，活動範圍為髖關節−25°～100°、膝關節0°～105°。歸零時將腿部伸直至0°並插入Ø6歸零銷，再將馬達角度設為零，以確保四顆馬達之角度基準一致。各姿態之運動模擬如圖11所示。'));
C.push(...fig('f11.png', '圖11 3D列印下肢外骨骼各姿態模擬'));

C.push(sec('7. 結論'));
C.push(body('本專題完成下肢外骨骼電控系統之感測整合、致動器系統鑑別與控制架構規劃。感測方面，提出每腳「2 FSR + 1 IMU」之精簡配置並設計外穿式鋼珠式FSR足底量測平台，BNO055角速度經修正後誤差小於±0.4%、角加速度誤差約0.3%，多情境量測亦證實可區分站立、行走與上下樓梯。致動方面，AK70-9之重力模型R^{2}達0.992，等效力矩常數為1.24 N·m/A，較規格值高約17%；AK60-39之力矩常數修正為1.98 N·m/A，證明直接採用規格書參數會造成明顯的力矩誤差，系統鑑別為重力補償與阻抗控制不可或缺之步驟。控制方面，已以QUBE-Servo 3驗證M-B-K阻抗控制之可行性，並確立以Raspberry Pi 4搭配R-Link之CAN多馬達架構。'));
C.push(body('後續將完成轉動慣量J之步階測試與30～60 RPM步態轉速範圍之鑑別、Raspberry Pi整合與FSR、IMU同步量測，並進行單腳導納控制測試與整機穿戴步行測試，以達成降低穿戴者負荷之最終目標。'));

C.push(sec('8. 誌謝'));
C.push(body('感謝王紹宇老師在馬達系統鑑別、控制理論與實驗規劃上給予專業的指導與建議，使本專題在面臨技術瓶頸時能夠順利突破。也感謝機構組同學提供關節力矩需求與外骨骼結構設計，以及實驗室學長姐在硬體採購與實驗操作上的協助。此外，感謝國立聯合大學機械工程學系提供充足的實驗場地與設備資源，使本專題得以順利進行。'));

C.push(sec('9. 參考文獻'));
const refs = [
  'Manna, S. K., et al. (2023). Optimal locations and computational frameworks of FSR and IMU sensors for measuring gait abnormalities. Heliyon, 9(4), e15210. https://doi.org/10.1016/j.heliyon.2023.e15210',
  'Sánchez Manchola, M. D., et al. (2019). Gait phase detection for lower-limb exoskeletons using foot motion data from a single inertial measurement unit in hemiparetic individuals. Sensors, 19(13), 2988.',
  'California State University. Bluetooth-enabled FSR-equipped insole prototype for gait asymmetry correction. CSU ScholarWorks. Retrieved from https://scholarworks.calstate.edu/downloads/nv935c35z',
  'Zhao, C., et al. (2025). Mechanical structure design and motion simulation analysis of a lower limb exoskeleton rehabilitation robot based on human–machine integration. Sensors, 25(5), 1611.',
  'Kazerooni, H., Racine, J.-L., Huang, L., & Steger, R. (2005). On the control of the Berkeley Lower Extremity Exoskeleton (BLEEX). In Proc. IEEE International Conference on Robotics and Automation (pp. 4353–4360).',
  'CubeMars官方網站. AK70-9 KV60 robotic actuator. Retrieved from https://www.cubemars.com/',
  'CubeMars官方網站. AK60-39 V3.0 KV80 robotic actuator. Retrieved from https://www.cubemars.com/',
  'Bosch Sensortec. BNO055 intelligent 9-axis absolute orientation sensor datasheet.',
  'Interlink Electronics. FSR 400 series force sensing resistor integration guide.',
  'Hogan, N. (1985). Impedance control: An approach to manipulation: Part I—Theory. Journal of Dynamic Systems, Measurement, and Control, 107(1), 1–7.',
  'Quanser Inc. QUBE-Servo 3 user manual and courseware.',
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
