from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

d=Document()
s=d.sections[0]; s.page_height=Cm(29.7); s.page_width=Cm(21)
for a in("top_margin","bottom_margin","left_margin","right_margin"): setattr(s,a,Cm(2))
st=d.styles["Normal"]; st.font.name="Times New Roman"; st.font.size=Pt(14)
st.element.rPr.rFonts.set(qn("w:eastAsia"),"標楷體")
st.paragraph_format.line_spacing=1.5; st.paragraph_format.space_after=Pt(0)

def run(p,t,b=False,size=None,i=False):
    r=p.add_run(t); r.bold=b; r.italic=i
    r.font.name="Times New Roman"; r._element.rPr.rFonts.set(qn("w:eastAsia"),"標楷體")
    if size: r.font.size=Pt(size)
    return r
def para(t="",b=False,size=None,align=None,indent=False):
    p=d.add_paragraph()
    if align=="c": p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    if indent: p.paragraph_format.first_line_indent=Pt(28)
    if t: run(p,t,b,size)
    return p
def H(t): return para(t,True,16)
def H2(t): return para(t,True,14)
def eq(t): 
    p=para(t,align="c"); return p
def pagebreak(): d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
def pic(path,w,cap=None):
    p=d.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run().add_picture(path,width=Cm(w))
    if cap: para(cap,align="c",size=12)
def table(rows,widths=None,caption=None,bold_first=True,hl=()):
    if caption: para(caption,True,align="c")
    t=d.add_table(rows=len(rows),cols=len(rows[0])); t.style="Table Grid"; t.alignment=WD_TABLE_ALIGNMENT.CENTER
    for i,r in enumerate(rows):
        for j,v in enumerate(r):
            c=t.cell(i,j); c.text=""; p=c.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.line_spacing=1.2
            run(p,str(v),b=(bold_first and i==0) or (i,j) in hl,size=13)
            if widths: c.width=Cm(widths[j])
            if (i,j) in hl:
                sh=OxmlElement("w:shd"); sh.set(qn("w:fill"),"FDE2E2"); sh.set(qn("w:val"),"clear"); c._tc.get_or_add_tcPr().append(sh)
    return t

# ---------- 封面 ----------
for _ in range(5): para()
para("實驗報告",True,26,"c"); para()
para("實驗一",True,20,"c")
para("二維穩態熱傳導之有限差分分析",True,20,"c")
para("──對流邊界節點溫度計算",True,16,"c")
for _ in range(6): para()
for t in["班級：機械三乙","組別：第 12 組","組員：U1311102　蔡朝欽","日期：2026 年 11 月 14 日"]:
    p=para(); p.paragraph_format.left_indent=Cm(5.5); run(p,t,size=16)
pagebreak()

# ---------- 一、實驗項目 ----------
H("一、實驗項目")
H2("工作一：平板節點溫度量測")
para("以底部 80 °C 加熱一鋁製平板，平板兩側面受風扇強制對流冷卻，待溫度達穩態後，以溫度計量測平板上 4 × 4 個節點之溫度，記錄於表一。實驗條件如表二。",indent=True)
table([["列＼行","1","2","3","4"],
       ["第 1 列（上）","49.3","48.0","47.2","48.2"],
       ["第 2 列","49.1","49.1","48.9","48.4"],
       ["第 3 列","49.9","49.8","49.5","49.9"],
       ["第 4 列（下）","51.8","51.3","51.3","50.4"]],
      widths=[3.6,2.4,2.4,2.4,2.4],caption="表一　各節點實測溫度（單位：°C）",hl=((3,1),(3,4)))
para("註：底色標示者為兩側孔洞（對流邊界節點）之實測值。",size=12)
para()
table([["項目","符號","數值"],
       ["對流熱傳係數","h","10 W/m²·°C"],
       ["周圍流體溫度","T∞","20 °C"],
       ["鋁熱傳導係數","k","237 W/m·°C"],
       ["節點間距","Δx = Δy","2.5 cm = 0.025 m"],
       ["底部加熱溫度","T_b","80 °C"],
       ["風扇設定","—","4.3"]],widths=[5,3.5,5.5],caption="表二　實驗條件")
pagebreak()
pic("fig1.png",15,"圖一　平板節點配置與實測溫度（紅框為待求之左、右側孔洞節點）")
para()
H2("工作二：對流邊界節點溫度計算")
para("以平板左、右兩側孔洞位置（第 3 列第 1 行、第 3 列第 4 行）為對流邊界節點，利用對流邊界節點之有限差分方程式，由其相鄰節點之實測溫度求出該節點之理論溫度，並與實測值比較。",indent=True)
pagebreak()

# ---------- 二、分析 ----------
H("二、分析")
H2("1. 對流邊界節點方程式推導")
para("取位於平板表面之節點 m，其控制體積寬 Δx/2、高 Δy（Δx = Δy），單位深度。該控制體積接受上、下、內側三個方向之傳導熱，以及表面之對流熱（圖二）。穩態時能量平衡：",indent=True)
pic("fig2.png",9.5,"圖二　對流邊界節點之控制體積")
eq("k(Δx/2)(T上 − Tm)/Δy + k(Δx/2)(T下 − Tm)/Δy")
eq("+ kΔy(T內 − Tm)/Δx + hΔy(T∞ − Tm) = 0")
para("因 Δx = Δy，兩邊同乘 2/k 並整理得：")
eq("T上 + T下 + 2T內 − 2(2 + hΔx/k)Tm + 2(hΔx/k)T∞ = 0")
para("故")
eq("Tm = [ T上 + T下 + 2T內 + 2(hΔx/k)T∞ ] ／ [ 2(2 + hΔx/k) ]")
H2("2. 係數計算")
eq("hΔx/k = (10 × 0.025) / 237 = 0.0010549")
eq("2(2 + hΔx/k) = 4.0021　　2(hΔx/k)T∞ = 2 × 0.0010549 × 20 = 0.0422")
pagebreak()
H2("3. 左側孔洞（第 3 列第 1 行）")
para("T上 = 49.1 °C，T下 = 51.8 °C，T內 = 49.8 °C")
eq("49.1 + 51.8 + 2 × 49.8 − 4.0021 Tm + 0.0422 = 0")
eq("200.5422 = 4.0021 Tm")
p=eq(""); run(p,"Tm = 50.109 °C",b=True)
H2("4. 右側孔洞（第 3 列第 4 行）")
para("T上 = 48.4 °C，T下 = 50.4 °C，T內 = 49.5 °C")
eq("48.4 + 50.4 + 2 × 49.5 − 4.0021 Tm + 0.0422 = 0")
eq("197.8422 = 4.0021 Tm")
p=eq(""); run(p,"Tm = 49.434 °C",b=True)
para("註：手算稿中右側寫成 197.8 − 0.0421 = 197.7579，得 49.413 °C；對流項 +2(hΔx/k)T∞ 應為加號，修正後為 49.434 °C（相差 0.02 °C）。",size=12)
H2("5. 理論值與實測值比較")
table([["節點","實測值 (°C)","計算值 (°C)","差值 (°C)","誤差 (%)"],
       ["左側孔洞","49.9","50.109","−0.209","0.42"],
       ["右側孔洞","49.9","49.434","+0.466","0.94"]],widths=[3.2,3.2,3.2,3,2.6],caption="表三　對流邊界節點理論值與實測值比較")
para("誤差 (%) = |實測值 − 計算值| / 計算值 × 100%",size=12,align="c")
para()
H2("6. 內部節點驗證")
para("內部節點無對流，其有限差分式為 T上 + T下 + T左 + T右 − 4Tm = 0，即 Tm 應等於四鄰點平均。以實測值檢驗如表四：",indent=True)
table([["節點","實測值 (°C)","四鄰點平均 (°C)","差值 (°C)"],
       ["(2,2)","49.1","48.95","+0.15"],
       ["(2,3)","48.9","48.55","+0.35"],
       ["(3,2)","49.8","49.95","−0.15"],
       ["(3,3)","49.5","49.98","−0.48"]],widths=[3,3.4,4.2,3.2],caption="表四　內部節點能量平衡檢驗")
pagebreak()

# ---------- 三、討論與心得 ----------
H("三、討論與心得")
H2("一、實驗結果討論")
for t in[
"1. 左、右兩側孔洞以對流邊界節點方程式計算所得溫度分別為 50.109 °C 與 49.434 °C，與實測值 49.9 °C 之誤差分別為 0.42 % 與 0.94 %，皆在 1 % 以內，顯示有限差分法能合理預測平板邊界節點之溫度。",
"2. 本實驗 hΔx/k 僅約 0.001，表示在節點尺度上對流熱阻遠大於鋁板之傳導熱阻，因此對流項對節點溫度的影響極小；若忽略對流項，Tm 幾乎等於 (T上 + T下 + 2T內)/4，兩側孔洞計算值僅改變約 0.01 °C。也因為如此，邊界節點溫度主要由周圍節點的量測值決定，量測誤差會直接反映在計算結果上。",
"3. 內部節點檢驗中，實測值與四鄰點平均之差在 ±0.5 °C 以內，大致滿足拉普拉斯方程式；差異來源可能為溫度計讀值解析度（0.1 °C）、量測時間不同步造成的溫度飄移、溫度計插入孔洞之接觸熱阻，以及風扇氣流在板面上分布不均，使實際 h 值與假設之 10 W/m²·°C 不同。",
"4. 底部加熱設定為 80 °C，但最下列量測值僅約 51 °C，表示加熱器與平板間存在明顯接觸熱阻，且平板兩面均有對流散熱，因此不能直接以 80 °C 作為最下列節點之邊界溫度；本次分析以實測之相鄰節點溫度代入，可避開此一不確定性。",
"5. 手算右側孔洞時將對流項正負號寫錯，得到 49.413 °C，修正後為 49.434 °C；雖然因 hΔx/k 很小而影響不大，但在 h 較大或間距較大時符號錯誤會造成明顯誤差，計算時須注意能量平衡式中各項的方向。"]:
    para(t)
H2("二、心得")
para("這次實驗把課堂上推導的有限差分節點方程式實際應用在量測數據上。原本只在黑板上看老師用內部節點列出聯立方程式，這次親自推導對流邊界節點的能量平衡，才真正理解為什麼邊界節點的控制體積只有一半、內側節點的係數是 2，以及 hΔx/k 這個無因次數代表的物理意義。計算結果與實測值誤差不到 1 %，讓我對數值方法的可靠性更有信心；同時也發現實際量測時的接觸熱阻、讀值時間與氣流分布都會影響結果，理論模型中的邊界條件必須依實際情況選擇。另外，手算時一個正負號的疏忽就會讓結果偏差，提醒我之後計算要逐項檢查單位與符號。",indent=True)
pagebreak()
H("附錄　原始計算手稿")
pic("sheet.jpg",11.5)
d.save("實驗報告_二維熱傳導有限差分.docx")
