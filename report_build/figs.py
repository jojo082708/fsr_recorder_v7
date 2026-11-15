import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
fm.fontManager.addfont("/usr/share/fonts/truetype/arphic/ukai.ttc")
plt.rcParams["font.family"]=["AR PL UKai TW"]; plt.rcParams["axes.unicode_minus"]=False; plt.rcParams["mathtext.fontset"]="dejavuserif"
T=[[49.3,48,47.2,48.2],[49.1,49.1,48.9,48.4],[49.9,49.8,49.5,49.9],[51.8,51.3,51.3,50.4]]
# Fig1 node layout
fig,ax=plt.subplots(figsize=(7,6.2))
ax.add_patch(plt.Rectangle((0,-0.5),3,4,fill=False,lw=2))
for i in range(4):
    for j in range(4):
        x,y=j,3-i
        hole=(i==2 and j in(0,3))
        ax.plot(x,y,'o',ms=7,color='crimson' if hole else 'k')
        ax.text(x,y+0.18,f"{T[i][j]:.1f}",ha='center',fontsize=13,family='Liberation Serif',bbox=dict(fc='white',ec='none',pad=1))
        if hole: ax.add_patch(plt.Rectangle((x-0.32,y-0.2),0.64,0.55,fill=False,ec='crimson',lw=1.6))
ax.annotate("左側孔洞(求 °C)",xy=(-0.35,1.08),xytext=(-2.75,1.08),fontsize=13,arrowprops=dict(arrowstyle='->'),va='center')
ax.annotate("右側孔洞(求 °C)",xy=(3.35,1.08),xytext=(3.75,1.08),fontsize=13,arrowprops=dict(arrowstyle='<-'),va='center')
ax.plot([-0.8,3.8],[-0.65,-0.65],lw=3,color='firebrick'); ax.text(1.5,-0.95,"底部加熱 80 °C",ha='center',fontsize=13)
ax.text(1.5,3.75,"對流：h = 10 W/m²·°C，T∞ = 20 °C",ha='center',fontsize=13)
ax.annotate("",xy=(0,-1.3),xytext=(1,-1.3),arrowprops=dict(arrowstyle='<->'))
ax.text(0.5,-1.65,"Δx = Δy = 2.5 cm",ha='center',fontsize=12)
ax.set_xlim(-2.9,5.8); ax.set_ylim(-1.9,4.0); ax.set_aspect('equal'); ax.axis('off')
fig.savefig("fig1.png",dpi=200,bbox_inches='tight')
# Fig2 對流邊界節點（照老師板書：邊界在右側）
def node_fig(fname, conv):
    fig,ax=plt.subplots(figsize=(5.6,4.6))
    if conv:
        ax.plot([1,1],[-1.4,1.4],lw=3,color='k')
        ax.plot([0,1],[1,1],color='gray',lw=1); ax.plot([0,1],[-1,-1],color='gray',lw=1); ax.plot([0,0],[-1,1],color='gray',lw=1)
        ax.add_patch(plt.Rectangle((0.5,-0.5),0.5,1,fill=True,fc='#dde8f5',ec='steelblue',ls='--',lw=1.4))
        pts={"T上":(1,1),"T中":(1,0),"T下":(1,-1),"T左":(0,0)}
    else:
        ax.add_patch(plt.Rectangle((-1,-1),2,2,fill=False,ec='gray'))
        ax.plot([-1,1],[0,0],color='gray'); ax.plot([0,0],[-1,1],color='gray')
        ax.add_patch(plt.Rectangle((-0.5,-0.5),1,1,fill=True,fc='#dde8f5',ec='steelblue',ls='--',lw=1.4))
        pts={"T上":(0,1),"T中":(0,0),"T下":(0,-1),"T左":(-1,0),"T右":(1,0)}
    for k,(x,y) in pts.items():
        ax.plot(x,y,'o',ms=11,color='#a0522d')
        dx,dy={"T上":(0.1,0.12),"T中":(0.1,0.12) if not conv else (0.1,0.08),"T下":(0.1,-0.25),"T左":(-0.42,0.12),"T右":(0.1,0.12)}[k]
        ax.text(x+dx,y+dy,k,fontsize=15)
    ar=dict(arrowstyle='->',color='darkorange',lw=2)
    if conv:
        ax.annotate("",xy=(0.55,0.12),xytext=(0.05,0.12),arrowprops=ar); ax.text(0.02,0.25,"$q_{in,x}$",fontsize=14,color='darkorange')
        ax.annotate("",xy=(0.75,-0.3),xytext=(0.75,-0.85),arrowprops=ar); ax.text(0.28,-0.75,"$q_{in,y}$",fontsize=14,color='darkorange')
        ax.annotate("",xy=(0.75,0.85),xytext=(0.75,0.3),arrowprops=ar); ax.text(0.22,0.6,"$q_{out,y}$",fontsize=14,color='darkorange')
    else:
        ax.annotate("",xy=(-0.2,0.12),xytext=(-0.75,0.12),arrowprops=ar); ax.text(-0.85,0.25,"$q_{in,x}$",fontsize=14,color='darkorange')
        ax.annotate("",xy=(0.12,-0.25),xytext=(0.12,-0.8),arrowprops=ar); ax.text(0.18,-0.75,"$q_{in,y}$",fontsize=14,color='darkorange')
        ax.annotate("",xy=(0.12,0.85),xytext=(0.12,0.3),arrowprops=ar); ax.text(0.18,0.6,"$q_{out,y}$",fontsize=14,color='darkorange')
    if conv:
        ax.annotate("",xy=(1.75,-0.12),xytext=(1.1,-0.12),arrowprops=ar); ax.text(1.2,-0.4,"$q_{out,x}$",fontsize=14,color='darkorange')
        ax.text(1.25,0.7,"h, T∞",fontsize=14)
        ax.text(0.0,-1.35,"Δx",fontsize=13); ax.text(-0.35,-0.55,"Δy",fontsize=13)
        ax.set_xlim(-0.7,2.0)
    else:
        ax.annotate("",xy=(0.95,-0.12),xytext=(0.3,-0.12),arrowprops=ar); ax.text(0.45,-0.35,"$q_{out,x}$",fontsize=14,color='darkorange')
        ax.text(-0.6,-1.3,"Δx",fontsize=13); ax.text(-1.3,-0.6,"Δy",fontsize=13)
        ax.set_xlim(-1.5,1.6)
    ax.set_ylim(-1.5,1.5); ax.set_aspect('equal'); ax.axis('off')
    fig.savefig(fname,dpi=200,bbox_inches='tight')
node_fig("fig3.png",False)
node_fig("fig2.png",True)
