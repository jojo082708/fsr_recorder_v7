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
P[9].runs[1].text="二"            # 組別：第二組
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
def Q(s): return f'<m:sSub><m:e>{mr("q")}</m:e><m:sub>{num(s)}</m:sub></m:sSub>'
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

# ================= 實驗項目（簡化版） =================
section("實驗項目：",first=True)
h2("工作一：平板節點溫度量測")
item("1. 鋁板底部以 80 °C 加熱，開啟風扇（設定 4.3）使表面對流冷卻。")
item("2. 待溫度穩定後，量測 4 × 4 個節點溫度，記錄於表一。")
caption("表一　各節點實測溫度（單位：°C）")
table([["列＼行","1","2","3","4"],["第 1 列（上）","49.3","48.0","47.2","48.2"],["第 2 列","49.1","49.1","48.9","48.4"],
       ["第 3 列","49.9","49.8","49.5","49.9"],["第 4 列（下）","51.8","51.3","51.3","50.4"]],[4.4,2.4,2.4,2.4,2.4],hl=((3,1),(3,4)))
note("註：底色為左、右兩側孔洞。條件：h = 10 W/m²·°C，T∞ = 20 °C，k = 237 W/m·°C，Δx = Δy = 0.025 m。")
picture("fig1.png",10)
caption_below("圖一　平板節點配置")
h2("工作二：對流邊界節點溫度計算")
item("1. 以左、右兩側孔洞為對流邊界節點，代入相鄰節點實測溫度求孔洞溫度，並與實測值比較。")

# ================= 數值分析（簡化版） =================
section("數值分析：")
h2("一、統御方程式")
bodyp("二維穩態、無內熱源之熱傳導滿足 Laplace 方程式，以網格將溫度場離散後，對每個節點寫 {*E}{_in} = {*E}{_out}：")
eq(fr(num("∂²")+mr("T"),num("∂")+mr("x")+num("²")),pl,fr(num("∂²")+mr("T"),num("∂")+mr("y")+num("²")),eqs,num("0"))
h2("二、對流邊界節點")
picture("fig2.png",6.5)
caption_below("圖二　對流邊界節點")
eq(Q("in,x"),pl,Q("in,y"),eqs,Q("out,x"),pl,Q("out,y"))
eq(D("y"),mr("k"),fr(T("左")+mi+T("中"),D("x")),pl,fr(D("x"),num("2")),mr("k"),fr(T("下")+mi+T("中"),D("y")),eqs,mr("h"),D("y"),par(T("中")+mi+Tinf),pl,fr(D("x"),num("2")),mr("k"),fr(T("中")+mi+T("上"),D("y")))
bodyp("同除 {*k}，Δ{*x} = Δ{*y}，整理得：")
eq(T("上"),pl,T("下"),pl,num("2"),T("左"),mi,num("2"),par(num("2")+pl+hdk),T("中"),pl,num("2"),hdk,Tinf,eqs,num("0"))
bodyp("其中 {*h}Δ{*x}/{*k} = 10 × 0.025 / 237 = 0.0010549。")
h2("三、計算結果")
bodyp("右側孔洞（{*T}{_上} = 48.4、{*T}{_下} = 50.4、{*T}{_左} = 49.5）：")
eq(T("中"),eqs,fr(num("48.4")+pl+num("50.4")+pl+num("2×49.5")+pl+num("0.0422"),num("4.0021")),eqs,num("49.434 °C"))
bodyp("左側孔洞（左右對稱，內側為 {*T}{_右} = 49.8；{*T}{_上} = 49.1、{*T}{_下} = 51.8）：")
eq(T("中"),eqs,fr(num("49.1")+pl+num("51.8")+pl+num("2×49.8")+pl+num("0.0422"),num("4.0021")),eqs,num("50.109 °C"))
caption("表二　理論值與實測值比較")
table([["節點","實測值 (°C)","計算值 (°C)","誤差 (%)"],["左側孔洞","49.9","50.109","0.42"],["右側孔洞","49.9","49.434","0.94"]],[3.4,3.4,3.4,3])

# ================= 討論與心得（簡化版） =================
section("討論與心得：")
h2("一、實驗結果討論")
for t in[
"1. 兩側孔洞計算值與實測值誤差皆小於 1 %，有限差分法可合理預測邊界節點溫度。",
"2. {*h}Δ{*x}/{*k} 僅約 0.001，對流項影響很小，孔洞溫度主要由相鄰節點溫度決定。",
"3. 誤差可能來自溫度計解析度、量測時間不同、接觸熱阻及風扇氣流不均。"]:
    item(t)
h2("二、心得")
bodyp("這次實驗把課堂上的節點能量平衡實際用在量測數據上，親自推導對流邊界節點後，才理解為什麼邊界節點只有半個控制體積、內側節點係數為 2。計算結果與實測誤差不到 1 %，讓我對數值方法更有信心。")

# ================= 附錄 =================
add(f'<w:p {W}><w:pPr><w:keepNext/><w:spacing w:before="240" w:after="120"/></w:pPr>{wr("附錄：手寫計算",b=True,sz=32)}</w:p>')
picture("handwritten.jpg",13)
caption_below("附圖　對流邊界節點手寫計算")

# 移除範本中已不用的舊圖片
used=set(el.get(qn("r:embed")) for el in body.iter(qn("a:blip")))
for rid,rel in list(d.part.rels.items()):
    if "image" in rel.reltype and rid not in used: d.part.drop_rel(rid)
out="熱流實驗報告_實驗三_二維穩態熱傳導.docx"
d.save(out); print(out)
