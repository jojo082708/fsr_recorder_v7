import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
fm.fontManager.addfont("/usr/share/fonts/truetype/arphic/ukai.ttc")
plt.rcParams["font.family"]=["AR PL UKai TW"]; plt.rcParams["axes.unicode_minus"]=False
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
# Fig2 convection edge node control volume
fig,ax=plt.subplots(figsize=(6,4.6))
ax.plot([0,0],[-1.3,1.3],lw=3,color='k'); ax.text(-0.08,1.35,"平板表面",ha='right',fontsize=12)
ax.add_patch(plt.Rectangle((0,-0.5),0.5,1,fill=True,fc='#dde8f5',ec='steelblue',ls='--',lw=1.5))
pts={"T":(0,0),"T_up":(0,1),"T_down":(0,-1),"T_in":(1,0)}
lab={"T":"Tm","T_up":"T上","T_down":"T下","T_in":"T內"}
for k,(x,y) in pts.items():
    ax.plot(x,y,'o',color='crimson' if k=="T" else 'k',ms=8); ax.text(x+0.07,y+0.08,lab[k],fontsize=14)
for (x1,y1) in [(0,1),(0,-1),(1,0)]:
    ax.annotate("",xy=(0.02*x1,0.12*y1),xytext=(x1*0.95,y1*0.85),arrowprops=dict(arrowstyle='->',color='gray'))
ax.annotate("",xy=(-0.05,-0.15),xytext=(-0.9,-0.15),arrowprops=dict(arrowstyle='->',color='darkorange',lw=2))
ax.text(-0.95,-0.42,"對流 h(T∞ - Tm)",fontsize=12,color='darkorange')
ax.text(0.53,-0.7,"控制體積 (Δx/2)×Δy",fontsize=11,color='steelblue')
ax.set_xlim(-1.5,1.6); ax.set_ylim(-1.4,1.6); ax.set_aspect('equal'); ax.axis('off')
fig.savefig("fig2.png",dpi=200,bbox_inches='tight')
