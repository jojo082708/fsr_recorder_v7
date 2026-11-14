"""熱流實驗報告（實驗三）— 封面沿用使用者範本，內文以範本段落格式重建，數學式用 Word 方程式 (OMML)。
用法：python3 build.py <範本.docx>"""
import sys, copy
from docx import Document
from docx.shared import Cm
from docx.oxml.ns import qn
from docx.oxml import parse_xml

W='xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
MNS='xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"'
d=Document(sys.argv[1])
body=d.element.body
P=d.paragraphs

# ---------- 封面（只改文字，格式不動） ----------
P[0].runs[0].text="熱流實驗報告"
P[2].runs[0].text="實驗三"
P[3].runs[0].text="二維穩態熱傳導實驗"
members=[("U1311102","蔡朝欽"),("U1311103","沈于安"),("U1311108","彭奕凱"),
         ("U1311111","張恆睿"),("U1311121","蔡翔宇")]
tpl=P[12]._p
def setm(p,sid,name):
    rs=p.findall(qn("w:r"))
    rs[0].find(qn("w:t")).text=sid; rs[1].find(qn("w:t")).text=""; rs[5].find(qn("w:t")).text=name
setm(tpl,*members[0])
prev=tpl
for sid,name in members[1:]:
    n=copy.deepcopy(tpl); setm(n,sid,name); prev.addnext(n); prev=n
for p in P[13:17]: body.remove(p._p)          # 多 4 位組員 → 少 4 個空白段，封面維持一頁
P[24].runs[12].text="14"
# 刪除封面之後的舊內容
sect=body.find(qn("w:sectPr")); keep=P[24]._p; cut=False
for el in list(body):
    if cut and el is not sect: body.remove(el)
    if el is keep: cut=True

# ---------- 段落工具（照範本格式） ----------
def esc(s): return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
def wr(t,b=False,i=False,sub=False,sz=None):
    rp=("<w:b/><w:bCs/>" if b else "")+("<w:i/><w:iCs/>" if i else "")+('<w:vertAlign w:val="subscript"/>' if sub else "")+(f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>' if sz else "")
    return f'<w:r>{"<w:rPr>"+rp+"</w:rPr>" if rp else ""}<w:t xml:space="preserve">{esc(t)}</w:t></w:r>'
def rich(s,b=False):
    """'_x' 下標記號：以 {_..} 表示下標，{*..} 表示斜體"""
    out=""; import re
    for tok in re.split(r"(\{[_*][^}]*\})",s):
        if not tok: continue
        if tok.startswith("{_"): out+=wr(tok[2:-1],b=b,sub=True)
        elif tok.startswith("{*"): out+=wr(tok[2:-1],b=b,i=True)
        else: out+=wr(tok,b=b)
    return out
def add(xml):
    el=parse_xml(xml); sect.addprevious(el); return el
def section(t,first=False):
    br='<w:r><w:br w:type="page"/></w:r>' if first else ""
    pb="" if first else "<w:keepNext/><w:pageBreakBefore/>"
    add(f'<w:p {W}><w:pPr>{pb}<w:spacing w:before="{0 if first else 240}" w:after="120"/></w:pPr>{br}{wr(t,b=True,sz=32)}</w:p>')
def h2(t): add(f'<w:p {W}><w:pPr><w:keepNext/><w:spacing w:before="180" w:after="100"/><w:ind w:left="283"/></w:pPr>{rich(t,b=True)}</w:p>')
def item(t,after=60): add(f'<w:p {W}><w:pPr><w:spacing w:after="{after}"/><w:ind w:left="623" w:hanging="311"/><w:jc w:val="both"/></w:pPr>{rich(t)}</w:p>')
def bodyp(t): add(f'<w:p {W}><w:pPr><w:spacing w:after="60"/><w:ind w:firstLine="560"/><w:jc w:val="both"/></w:pPr>{rich(t)}</w:p>')
def caption(t): add(f'<w:p {W}><w:pPr><w:keepNext/><w:spacing w:before="60" w:after="160"/><w:jc w:val="center"/></w:pPr>{wr(t,b=True)}</w:p>')
def caption_below(t): add(f'<w:p {W}><w:pPr><w:spacing w:before="60" w:after="160"/><w:jc w:val="center"/></w:pPr>{wr(t,b=True)}</w:p>')
def note(t): add(f'<w:p {W}><w:pPr><w:spacing w:after="60"/><w:ind w:left="623"/></w:pPr>{wr(t,sz=24)}</w:p>')
def picture(path,w):
    p=d.add_paragraph(); p.alignment=1; p.paragraph_format.keep_with_next=True
    p.add_run().add_picture(path,width=Cm(w)); sect.addprevious(p._p)

# ---------- OMML 方程式 ----------
def mr(t,plain=False):
    sty='<m:rPr><m:sty m:val="p"/></m:rPr>' if plain else ""
    return f'<m:r>{sty}<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/></w:rPr><m:t xml:space="preserve">{esc(t)}</m:t></m:r>'
def num(t): return mr(t,True)
def T(s): return f'<m:sSub><m:e>{mr("T")}</m:e><m:sub>{mr(s)}</m:sub></m:sSub>'
Tinf=f'<m:sSub><m:e>{mr("T")}</m:e><m:sub>{num("∞")}</m:sub></m:sSub>'
def fr(a,b): return f'<m:f><m:num>{a}</m:num><m:den>{b}</m:den></m:f>'
def par(x): return f'<m:d><m:e>{x}</m:e></m:d>'
def absd(x): return f'<m:d><m:dPr><m:begChr m:val="|"/><m:endChr m:val="|"/></m:dPr><m:e>{x}</m:e></m:d>'
D=lambda v: num("Δ")+mr(v)
hdk=fr(mr("h")+D("x"),mr("k"))
def eq(*parts):
    add(f'<w:p {W} {MNS}><w:pPr><w:spacing w:before="60" w:after="60"/></w:pPr><m:oMathPara><m:oMathParaPr><m:jc m:val="center"/></m:oMathParaPr><m:oMath>{"".join(parts)}</m:oMath></m:oMathPara></w:p>')
pl,mi,eqs=num(" + "),num(" − "),num(" = ")

def table(rows,widths,hl=()):
    t=d.add_table(rows=len(rows),cols=len(rows[0])); t.alignment=1
    tblPr=t._tbl.tblPr
    tblPr.append(parse_xml(f'<w:tblLayout {W} w:type="fixed"/>'))
    for gc,wd in zip(t._tbl.tblGrid.findall(qn("w:gridCol")),widths): gc.set(qn("w:w"),str(int(wd*567)))
    tblPr.append(parse_xml(f'<w:tblBorders {W}>'+"".join(f'<w:{e} w:val="single" w:sz="6" w:space="0" w:color="000000"/>' for e in ("top","left","bottom","right","insideH","insideV"))+'</w:tblBorders>'))
    for i,r in enumerate(rows):
        for j,v in enumerate(r):
            c=t.cell(i,j); c.width=Cm(widths[j]); p=c.paragraphs[0]; p.alignment=1
            run=p.add_run(str(v)); run.bold=(i==0) or (i,j) in hl
            if (i,j) in hl: c._tc.get_or_add_tcPr().append(parse_xml(f'<w:shd {W} w:val="clear" w:color="auto" w:fill="FDE2E2"/>'))
    sect.addprevious(t._tbl)

# ================= 實驗項目 =================
section("實驗項目：",first=True)
h2("工作一：平板節點溫度量測")
item("1. 將鋁板底部置於加熱器上，加熱溫度設定為 80 °C。")
item("2. 開啟風扇（設定 4.3），使平板表面受強制對流冷卻，周圍空氣溫度 {*T}{_∞} = 20 °C。")
item("3. 待平板溫度達穩態後，依序量測 4 × 4 個節點之溫度，記錄於表一；實驗條件記錄於表二。")
caption("表一　各節點實測溫度（單位：°C）")
table([["列＼行","1","2","3","4"],["第 1 列（上）","49.3","48.0","47.2","48.2"],["第 2 列","49.1","49.1","48.9","48.4"],
       ["第 3 列","49.9","49.8","49.5","49.9"],["第 4 列（下）","51.8","51.3","51.3","50.4"]],[4.4,2.4,2.4,2.4,2.4],hl=((3,1),(3,4)))
note("註：底色標示者為左、右兩側孔洞（對流邊界節點）之實測溫度。")
caption("表二　實驗條件")
table([["項目","符號","數值"],["對流熱傳係數","h","10 W/m²·°C"],["周圍空氣溫度","T∞","20 °C"],["鋁之熱傳導係數","k","237 W/m·°C"],
       ["節點間距","Δx = Δy","2.5 cm = 0.025 m"],["底部加熱溫度","—","80 °C"],["風扇設定","—","4.3"]],[4.6,3,5])
picture("fig1.png",10.5)
caption_below("圖一　平板節點配置與實測溫度")
h2("工作二：對流邊界節點溫度計算")
item("1. 以平板左、右兩側孔洞（第 3 列第 1 行、第 3 列第 4 行）為對流邊界節點。")
item("2. 以對流邊界節點之有限差分方程式，代入相鄰節點之實測溫度，求出孔洞之理論溫度，並與實測值比較。")

# ================= 數值分析 =================
section("數值分析：")
h2("一、對流邊界節點方程式")
bodyp("取位於平板表面之節點 ({*m}, {*n})，其控制體積寬 Δ{*x}/2、高 Δ{*y}（Δ{*x} = Δ{*y}），單位深度。此節點由上、下、內側三個方向傳導熱量，並在表面與空氣對流（圖二）。")
picture("fig2.png",8.5)
caption_below("圖二　對流邊界節點之控制體積")
item("1. 穩態能量平衡：",after=0)
eq(mr("k"),fr(D("x"),num("2")),fr(T("m,n+1")+mi+T("m,n"),D("y")),pl,mr("k"),fr(D("x"),num("2")),fr(T("m,n−1")+mi+T("m,n"),D("y")))
eq(pl,mr("k"),D("y"),fr(T("m+1,n")+mi+T("m,n"),D("x")),pl,mr("h"),D("y"),par(Tinf+mi+T("m,n")),eqs,num("0"))
item("2. 因 Δ{*x} = Δ{*y}，兩邊同乘 2/{*k} 整理得：",after=0)
eq(T("m,n+1"),pl,T("m,n−1"),pl,num("2"),T("m+1,n"),mi,num("2"),par(hdk+pl+num("2")),T("m,n"),pl,num("2"),hdk,Tinf,eqs,num("0"))
item("3. 解出節點溫度：",after=0)
eq(T("m,n"),eqs,fr(T("m,n+1")+pl+T("m,n−1")+pl+num("2")+T("m+1,n")+pl+num("2")+hdk+Tinf, num("2")+par(hdk+pl+num("2"))))
item("4. 係數計算：",after=0)
eq(hdk,eqs,fr(num("10×0.025"),num("237")),eqs,num("0.0010549"))
eq(num("2"),par(hdk+pl+num("2")),eqs,num("4.0021"),num(" ,   "),num("2"),hdk,Tinf,eqs,num("2×0.0010549×20"),eqs,num("0.0422"))
h2("二、左側孔洞（第 3 列第 1 行）")
bodyp("上方節點 49.1 °C、下方節點 51.8 °C、內側節點 49.8 °C：")
eq(T("左"),eqs,fr(num("49.1")+pl+num("51.8")+pl+num("2×49.8")+pl+num("0.0422"),num("4.0021")),eqs,fr(num("200.5422"),num("4.0021")),eqs,num("50.109 °C"))
h2("三、右側孔洞（第 3 列第 4 行）")
bodyp("上方節點 48.4 °C、下方節點 50.4 °C、內側節點 49.5 °C（右側邊界之內側節點為 {*T}{_m−1,n}，方程式形式相同）：")
eq(T("右"),eqs,fr(num("48.4")+pl+num("50.4")+pl+num("2×49.5")+pl+num("0.0422"),num("4.0021")),eqs,fr(num("197.8422"),num("4.0021")),eqs,num("49.434 °C"))
note("註：手算稿將對流項寫成 197.8 − 0.0421，得 49.413 °C；對流項 2(hΔx/k)T∞ 應為正號，修正後為 49.434 °C。")
h2("四、理論值與實測值比較")
eq(mr("ε"),eqs,fr(absd(T("實測")+mi+T("計算")),T("計算")),num("×100%"))
caption("表三　對流邊界節點理論值與實測值比較")
table([["節點","實測值 (°C)","計算值 (°C)","差值 (°C)","誤差 ε (%)"],["左側孔洞","49.9","50.109","−0.209","0.42"],["右側孔洞","49.9","49.434","+0.466","0.94"]],[3,3,3,3,3])
h2("五、內部節點驗證")
bodyp("內部節點無對流，有限差分方程式為：")
eq(T("m,n"),eqs,fr(T("m+1,n")+pl+T("m−1,n")+pl+T("m,n+1")+pl+T("m,n−1"),num("4")))
bodyp("即節點溫度應等於四鄰點之平均，以實測值檢驗如表四。")
caption("表四　內部節點能量平衡檢驗")
table([["節點（列, 行）","實測值 (°C)","四鄰點平均 (°C)","差值 (°C)"],["(2, 2)","49.1","48.95","+0.15"],["(2, 3)","48.9","48.55","+0.35"],
       ["(3, 2)","49.8","49.95","−0.15"],["(3, 3)","49.5","49.98","−0.48"]],[3.6,3.2,4,3.2])

# ================= 討論與心得 =================
section("討論與心得：")
h2("一、實驗結果討論")
for t in[
"1. 左、右兩側孔洞以對流邊界節點方程式計算得 50.109 °C 與 49.434 °C，與實測值 49.9 °C 之誤差分別為 0.42 % 與 0.94 %，皆小於 1 %，顯示有限差分法能合理預測平板邊界節點之溫度。",
"2. 本實驗 {*h}Δ{*x}/{*k} 僅約 0.001，表示在一個節點間距內，對流熱阻遠大於鋁板之傳導熱阻，因此對流項對孔洞溫度影響很小（約 0.01 °C），孔洞溫度主要由相鄰節點溫度決定，量測誤差也會直接反映在計算結果上。",
"3. 內部節點實測值與四鄰點平均之差在 ±0.5 °C 以內，大致符合穩態熱傳導方程式；誤差可能來自溫度計解析度（0.1 °C）、各點量測時間不同造成的溫度飄移、溫度計與孔洞間之接觸熱阻，以及風扇氣流分布不均使實際 {*h} 值偏離 10 W/m²·°C。",
"4. 底部加熱設定為 80 °C，但最下列實測僅約 51 °C，表示加熱器與平板間存在明顯接觸熱阻，故不能直接以 80 °C 作為邊界溫度；本次分析直接使用相鄰節點實測值，可避開此不確定性。",
"5. 手算右側孔洞時對流項正負號寫錯，得 49.413 °C，修正後為 49.434 °C。雖然本實驗影響不大，但若 {*h} 或節點間距較大，符號錯誤會造成明顯誤差。"]:
    item(t)
h2("二、心得")
bodyp("這次實驗把課堂上推導的有限差分節點方程式實際應用在量測數據上。以前只在黑板上看老師用內部節點列聯立方程式，這次自己推導對流邊界節點的能量平衡，才真正理解為什麼邊界節點的控制體積只有一半、內側節點的係數是 2，以及 {*h}Δ{*x}/{*k} 代表的物理意義。計算結果與實測值誤差不到 1 %，讓我對數值方法更有信心；同時也發現接觸熱阻、讀值時間與氣流分布都會影響結果，邊界條件必須依實際情況選擇。另外一個正負號的疏忽就會讓結果偏差，提醒我之後計算要逐項檢查。")

# 移除範本中已不用的舊圖片
used=set(el.get(qn("r:embed")) for el in body.iter(qn("a:blip")))
for rid,rel in list(d.part.rels.items()):
    if "image" in rel.reltype and rid not in used: d.part.drop_rel(rid)
out="熱流實驗報告_實驗三_二維穩態熱傳導.docx"
d.save(out); print(out)
