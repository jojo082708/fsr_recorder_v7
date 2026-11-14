import re
src=open('poster_w.html').read()
head_css=src[src.index('<style>')+7:src.index('</style>')]
body=src[src.index('<body>')+6:src.index('</body>')]
SANS='"Microsoft JhengHei","WenQuanYi Zen Hei",sans-serif'
KAI='"Times New Roman","DFKai-SB","標楷體","AR PL UKai TW",serif'

def page(title, css, b):
    return f'<!doctype html>\n<html lang="zh-Hant"><head><meta charset="utf-8">\n<title>{title}</title>\n<style>{head_css}\n/* ---- variant ---- */\n{css}</style></head>\n<body>{b}</body></html>\n'

# ---------- A：工業安全風 ----------
A_css=f'''
body {{ background:#12161c; color:#e8eaed; font-family:{SANS}; }}
header {{ background:#12161c; height:104mm; }}
h1 {{ color:#fff; font-weight:900; letter-spacing:4px; }}
.en {{ color:#f5b700; font-weight:700; font-size:30px; }}
.who {{ color:#cfd4da; }}
.stripe {{ display:block; width:100%; height:7mm; }}
main {{ padding-top:4mm; }}
.box {{ background:#1b222c; border:2px solid #2e3a4a; border-radius:2mm; }}
.tab {{ background:#f5b700; color:#111; border:none; border-radius:0; left:0; top:-7mm; padding:1mm 7mm; font-weight:900; }}
.sub {{ background:#202936; border:2px solid #3a4656; }}
.sub .tab {{ color:#111; border:none; border-radius:0; left:0; }}
.c1 .tab {{ background:#f5b700; }} .c2 .tab {{ background:#4cc9f0; }} .c3 .tab {{ background:#80ed99; }} .c4 .tab {{ background:#ff7b54; }}
.c1,.c2,.c3,.c4 {{ border-color:#3a4656; }}
p, ol.c {{ color:#e8eaed; }}
.b {{ color:#f5b700; }} .r {{ color:#ff7b54; }}
figcaption {{ color:#b8c0cc; }}
figure img {{ background:#fff; }}
table {{ color:#e8eaed; }}
th {{ border-top:2.5px solid #f5b700; border-bottom:2px solid #f5b700; color:#f5b700; }}
td {{ border-bottom:1.5px solid #3a4656; }}
tr:last-child td {{ border-bottom:2.5px solid #f5b700; }}
.eq {{ color:#fff; }}
.goal .l div {{ background:#222b36; border-left:2mm solid #f5b700; color:#e8eaed; }}
.tgt {{ background:#f5b700; color:#111; }} .tgt h3 {{ border-bottom-color:#111; }} .tgt .g div b {{ color:#111; }}
.flow {{ color:#e8eaed; }}
.flow div {{ background:#222b36; border-color:#f5b700; color:#e8eaed; }}
.flow div.go {{ background:#4a3a08; border-color:#f5b700; }}
.flow div.todo {{ background:#12161c; border-color:#8a94a3; color:#b8c0cc; }}
.legend {{ color:#b8c0cc; }}
.refs {{ color:#9aa3ad; }}
p {{ font-size:25.5px; }}
.box {{ margin-top:8mm; }}
'''
A_body=body.replace('</header>','</header>\n<img class="stripe" src="assets/stripe.png" alt="">',1)
A_body=A_body.replace('<span style="color:#5a9a5a">■</span>','<span style="color:#f5b700">■</span>').replace('<span style="color:#e0a040">■</span>','<span style="color:#b38600">■</span>').replace('<span style="color:#777">□</span>','<span style="color:#8a94a3">□</span>')

# ---------- B：學術極簡風 ----------
B_css=f'''
body {{ background:#ffffff; color:#1a1a1a; font-family:{SANS}; }}
header {{ background:#ffffff; color:#0f3d3a; height:104mm; grid-template-columns: 62mm 1fr 78mm; border-bottom:0; }}
.badge {{ background:#fff; }}
.lab {{ background:#fff; }}
h1 {{ color:#0f766e; font-weight:900; text-align:left; letter-spacing:2px; }}
.en {{ color:#334155; text-align:left; font-size:31px; }}
.who {{ color:#1f2937; text-align:left; }}
.rule {{ height:2.2mm; background:#0f766e; margin:0 12mm; }}
main {{ padding-top:2mm; }}
.box {{ background:#f3f7f6; border:none; border-radius:0; padding:5mm 6mm 4mm; margin-top:7mm; }}
.box > .tab {{ position:static; display:inline-block; background:none; border:none; border-radius:0; padding:0 0 2mm; color:#0f766e; font-size:46px; font-weight:900; }}
.sub {{ background:#ffffff; border:1.5px solid #cfdcda; border-radius:0; padding:4mm 4mm 3mm; margin-top:4mm; }}
.sub .tab {{ position:static; display:inline-block; background:none; border:none; padding:0 0 1.5mm; font-size:32px; font-weight:900; color:#0f766e; }}
.c1 .tab,.c2 .tab,.c3 .tab,.c4 .tab {{ color:#0f766e; }}
.b {{ color:#0f766e; }} .r {{ color:#b91c1c; }}
th {{ border-top:2.5px solid #0f766e; border-bottom:2px solid #0f766e; color:#0f766e; }}
tr:last-child td {{ border-bottom:2.5px solid #0f766e; }}
.goal .l div {{ background:#ffffff; border-left:2mm solid #0f766e; }}
.tgt {{ background:#0f766e; }} .tgt h3 {{ border-bottom-color:#9fd8d0; }} .tgt .g div b {{ color:#d6f5f0; }}
.flow div {{ background:#fff; border:2px solid #0f766e; color:#0f3d3a; border-radius:0; }}
.flow div.go {{ background:#0f766e; color:#fff; border-color:#0f766e; }}
.flow div.todo {{ background:#fff; border:2px dashed #94a3b8; color:#64748b; }}
p {{ font-size:23.5px; }} .sub {{ margin-top:3mm; }} .box {{ margin-top:5mm; padding:4mm 5mm 3mm; }}
header {{ height:104mm; }} h1 {{ font-size:82px; }}
'''
B_body=body.replace('</header>','</header>\n<div class="rule" data-shape></div>',1)
nums={'摘要':'01','研究動機':'02','研究目標':'03','研究方法':'04','研究結果':'05','結論':'06'}
for k,v in nums.items():
    B_body=B_body.replace(f'<div class="box"><div class="tab">{k}</div>',f'<div class="box"><div class="tab">{v}　{k}</div>')
B_body=B_body.replace('<span style="color:#5a9a5a">■</span> 已完成','<span style="color:#0f766e">□</span> 已完成').replace('<span style="color:#e0a040">■</span> 進行中','<span style="color:#0f766e">■</span> 進行中').replace('<span style="color:#777">□</span>','<span style="color:#94a3b8">□</span>')

# ---------- C：數據亮點風 ----------
C_css=f'''
body {{ background:#f6f3ee; color:#1f2937; font-family:{KAI}; }}
header {{ background:#c2410c; height:112mm; padding-bottom:6mm; }}
h1 {{ font-family:{SANS}; font-weight:900; letter-spacing:3px; }}
.en {{ color:#ffe4d1; }}
.who {{ color:#fff; }}
.kpi {{ display:grid; grid-template-columns:repeat(4,1fr); gap:6mm; padding:0 12mm; margin-top:5mm; }}
.kpi > div {{ background:#ffffff; border:2px solid #f0d9c8; border-radius:5mm; padding:3mm 4mm; text-align:center; }}
.kpi b {{ display:block; font-family:{SANS}; font-size:66px; font-weight:900; color:#c2410c; line-height:1.15; }}
.kpi span {{ display:block; font-size:26px; color:#374151; }}
main {{ padding-top:2mm; }}
.box {{ background:#ffffff; border:2px solid #eadfd3; border-radius:7mm; margin-top:10mm; }}
.tab {{ background:#1e293b; color:#fff; border:none; border-radius:10mm; padding:1mm 8mm; font-family:{SANS}; font-weight:900; }}
.sub {{ background:#fffaf5; border:2px solid #eadfd3; border-radius:5mm; }}
.sub .tab {{ color:#fff; border:none; border-radius:10mm; }}
.c1 .tab {{ background:#c2410c; }} .c2 .tab {{ background:#2563eb; }} .c3 .tab {{ background:#0f766e; }} .c4 .tab {{ background:#7c3aed; }}
.c1,.c2,.c3,.c4 {{ border-color:#eadfd3; }}
.b {{ color:#1d4ed8; }} .r {{ color:#c2410c; }}
th {{ border-top:2.5px solid #c2410c; border-bottom:2px solid #c2410c; color:#9a3412; }}
tr:last-child td {{ border-bottom:2.5px solid #c2410c; }}
.goal .l div {{ background:#fdf2e9; border-left:2mm solid #c2410c; }}
.tgt {{ background:#1e293b; }} .tgt .g div b {{ color:#fdba74; }}
.flow div {{ background:#fff; border-color:#c2410c; border-radius:10mm; }}
.flow div.go {{ background:#fed7aa; border-color:#c2410c; }}
.flow div.todo {{ background:#fff; border-color:#9ca3af; }}
p {{ font-size:24px; }}
.box {{ margin-top:8mm; }} .kpi b {{ font-size:60px; }} img[alt="AK60-39"] {{ width:84% !important; }} img[alt="外骨骼姿態模擬"] {{ width:88%; }}
header {{ height:108mm; }}
'''
kpi='''<div class="kpi">
  <div data-shape><b data-text>7 kg</b><span data-text>目標承載搬運物</span></div>
  <div data-shape><b data-text>4 顆</b><span data-text>髖、膝主動關節馬達</span></div>
  <div data-shape><b data-text>1.24 / 1.98</b><span data-text>實測 K<sub>t</sub>（N·m/A）AK70-9 / AK60-39</span></div>
  <div data-shape><b data-text>±0.4%</b><span data-text>IMU 角速度誤差（修正後）</span></div>
</div>'''
C_body=body.replace('</header>','</header>\n'+kpi,1)
C_body=C_body.replace('<span style="color:#5a9a5a">■</span>','<span style="color:#c2410c">■</span>').replace('<span style="color:#e0a040">■</span>','<span style="color:#fdba74">■</span>')

for n,css,b,t in [('A',A_css,A_body,'工業安全風'),('B',B_css,B_body,'學術極簡風'),('C',C_css,C_body,'數據亮點風')]:
    open(f'poster_{n}.html','w').write(page('下肢外骨骼專題海報－'+t,css,b))
print('ok')

# ---------- D：Canva 簡報風（實驗室投影片範本） ----------
JH='"Microsoft JhengHei","WenQuanYi Zen Hei",sans-serif'
D_css=f'''
body {{ background:#ffffff; color:#1f1f1f; font-family:{JH}; }}
header {{ background:#ffffff; color:#3D4B63; height:124mm; grid-template-columns: 62mm 1fr 78mm; }}
.badge, .lab {{ background:#fff; }}
h1 {{ color:#3D4B63; font-family:{KAI}; font-weight:900; font-size:84px; letter-spacing:5px; line-height:1.2; }}
.en {{ color:#2F5597; font-weight:700; font-size:30px; }}
.pill {{ display:block; width:150mm; margin:3mm auto 2mm; background:#4472C4; border:3px solid #8FAADC; border-radius:6mm; color:#fff; text-align:center; font-family:"Times New Roman",serif; font-size:36px; padding:1.5mm 0; }}
.who {{ color:#595959; font-weight:700; font-size:34px; }}
.hr {{ height:2px; background:#222222; margin:0 12mm; }}
main {{ padding-top:2mm; }}
.box {{ background:#ffffff; border:none; border-radius:0; padding:2mm 2mm 2mm; margin-top:5mm; }}
.box > .tab {{ position:static; display:block; background:none; border:none; border-radius:0; padding:0; color:#3D4B63; font-family:{KAI}; font-size:46px; font-weight:900; letter-spacing:3px; }}
.box > .rl {{ height:2px; background:#222222; margin:1.5mm 0 3mm; }}
.sub {{ border:none; border-radius:4mm; padding:3mm 4mm 3mm; margin-top:4mm; }}
.sub .tab {{ position:static; display:block; background:none; border:none; padding:0 0 1.5mm; font-size:32px; font-weight:900; }}
.c1 {{ background:#E6F0EE; }} .c1 .tab {{ color:#1E6B5C; }}
.c2 {{ background:#FDF0DE; }} .c2 .tab {{ color:#B26A00; }}
.c3 {{ background:#E6F0EE; }} .c3 .tab {{ color:#1E6B5C; }}
.c4 {{ background:#FDF0DE; }} .c4 .tab {{ color:#B26A00; }}
p {{ font-size:24px; font-weight:500; }}
.b {{ color:#2F5597; }} .r {{ color:#C00000; }}
table {{ background:#fff; font-size:22px; }}
th, td {{ border:1px solid #DCE3EA; }}
th {{ background:#1E2A4A; color:#fff; border-top:1px solid #DCE3EA; border-bottom:1px solid #DCE3EA; }}
th:first-child {{ background:#A9D2CF; color:#1F1F1F; }}
td:first-child {{ background:#B7D9D6; font-weight:700; }}
tr:nth-child(odd) td:not(:first-child) {{ background:#EAF2F8; }}
tr:last-child td {{ border-bottom:1px solid #DCE3EA; }}
.goal .l div {{ background:#F2F4F7; border-left:2mm solid #1F6E8C; }}
.tgt {{ background:#1E2A4A; }} .tgt h3 {{ border-bottom-color:#A9D2CF; }} .tgt .g div b {{ color:#FFC000; }}
.flow div {{ background:#1F6E8C; border-color:#1F6E8C; color:#fff; border-radius:3mm; font-weight:700; }}
.flow div.go {{ background:#FFC000; border-color:#FFC000; color:#1F1F1F; }}
.flow div.todo {{ background:#fff; border:2px dashed #1F6E8C; color:#1F6E8C; }}
.foot {{ position:absolute; left:0; right:0; bottom:0; height:30mm; }}
.foot img, .foot div {{ position:absolute; }}
.box {{ margin-top:4mm; }} p {{ font-size:23px; }} th, td {{ padding:0.8mm 1.5mm; }}
img[alt="AK60-39"] {{ width:76% !important; }} img[alt="外骨骼姿態模擬"] {{ width:74%; }} .sub {{ padding:2.5mm 4mm 2mm; }} img[alt="系統硬體架構"] {{ width:88% !important; }}
'''
footer='''<div class="foot">
  <img src="assets/lab_footer.png" alt="齒輪設計與先進製造實驗室" style="left:6mm; bottom:3mm; height:24mm;">
  <img src="assets/screw.png" alt="" style="left:200mm; bottom:7mm; height:9mm;">
  <div data-shape style="left:262mm; bottom:8.5mm; width:22mm; height:6mm; background:#4472C4;"></div>
  <img src="assets/screw.png" alt="" style="left:296mm; bottom:7mm; height:9mm;">
  <div data-shape style="left:358mm; bottom:8.5mm; width:22mm; height:6mm; background:#4472C4;"></div>
  <div data-text style="left:430mm; bottom:5mm; width:120mm; height:14mm; font-family:'Times New Roman',serif; font-size:52px; font-weight:700; color:#000; text-align:center;">2026/11/14</div>
  <img src="assets/gear_badge.png" alt="" style="right:6mm; bottom:3mm; height:24mm;">
</div>'''
D_body=body.replace('<div class="who">','<div class="pill" data-shape><span data-text>國立聯合大學 機械工程學系 電控組</span></div>\n    <div class="who">',1)
D_body=D_body.replace('</header>','</header>\n<div class="hr" data-shape></div>',1)
cn={'摘要':'一','研究動機':'二','研究目標':'三','研究方法':'四','研究結果':'五','結論':'六'}
for k,v in cn.items():
    D_body=D_body.replace(f'<div class="box"><div class="tab">{k}</div>',f'<div class="box"><div class="tab">{v}、{k}</div><div class="rl" data-shape></div>')
D_body=D_body.replace('<span style="color:#5a9a5a">■</span>','<span style="color:#1F6E8C">■</span>').replace('<span style="color:#e0a040">■</span>','<span style="color:#FFC000">■</span>').replace('<span style="color:#777">□</span>','<span style="color:#1F6E8C">□</span>')
D_body=D_body.replace('</main>','</main>\n'+footer,1)
D_body=D_body.replace('<figure><img src="assets/f03.png" alt="IMU角速度實驗"><figcaption>IMU 角速度實驗架設</figcaption></figure>','<figure><img src="assets/f03.png" alt="IMU角速度實驗" style="width:82%"><figcaption>IMU 角速度實驗架設</figcaption></figure>')
open('poster_D.html','w').write(page('下肢外骨骼專題海報－Canva 簡報風',D_css,D_body))
print('D ok')

# ---------- E：Canva 配色＋外框 ----------
E_css=D_css+'''
.box {{ position:relative; border:3px solid #3D4B63; border-radius:5mm; padding:11mm 6mm 3mm; margin-top:9mm; background:#fff; }}
.box > .tab {{ position:absolute; top:-8mm; left:6mm; display:block; background:#fff; border:3px solid #3D4B63; border-radius:3mm; padding:1mm 6mm; font-size:42px; letter-spacing:2px; }}
.sub {{ position:relative; border:3px solid; border-radius:4mm; padding:9mm 4mm 2.5mm; margin-top:8mm; }}
.sub .tab {{ position:absolute; top:-7mm; left:5mm; display:block; background:#fff; border:3px solid; border-radius:3mm; padding:0.5mm 5mm; font-size:30px; }}
.c1, .c3 {{ border-color:#1E6B5C; }} .c1 .tab, .c3 .tab {{ border-color:#1E6B5C; }}
.c2, .c4 {{ border-color:#B26A00; }} .c2 .tab, .c4 .tab {{ border-color:#B26A00; }}
header {{ height:118mm; }}
p {{ font-size:24px; }}
img[alt="AK60-39"] {{ width:86% !important; }} img[alt="外骨骼姿態模擬"] {{ width:84%; }} img[alt="系統硬體架構"] {{ width:94% !important; }}
'''.replace('{{','{').replace('}}','}')
E_body=D_body.replace('<div class="rl" data-shape></div>','')
open('poster_E.html','w').write(page('下肢外骨骼專題海報－Canva 配色外框版',E_css,E_body))
print('E ok')
