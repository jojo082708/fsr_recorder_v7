import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle
from matplotlib import font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc')
plt.rcParams['font.family']='WenQuanYi Zen Hei'; plt.rcParams['mathtext.fontset']='stix'; plt.rcParams['axes.unicode_minus']=False
fig,ax=plt.subplots(figsize=(8.6,4.6),dpi=200); ax.set_xlim(0,110); ax.set_ylim(0,52); ax.axis('off')
def box(x,y,w,h,t,fc='#ffffff',fs=10):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.3',fc=fc,ec='black',lw=1.2)); ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=fs)
def arr(x1,y1,x2,y2,t='',tx=0,ty=1.2,fs=10):
    ax.annotate('',xy=(x2,y2),xytext=(x1,y1),arrowprops=dict(arrowstyle='-|>',lw=1.1,color='black'))
    if t: ax.text((x1+x2)/2+tx,(y1+y2)/2+ty,t,ha='center',fontsize=fs)
def line(xs,ys): ax.plot(xs,ys,color='black',lw=1.1)
def summ(x,y): ax.add_patch(Circle((x,y),1.8,fc='white',ec='black')); ax.text(x,y,'Σ',ha='center',va='center',fontsize=11)
Y=38
ax.text(0.5,Y+1.5,r'$\hat\tau_{h,Q}$',fontsize=12)
summ(9,Y); arr(1,Y,7.2,Y); ax.text(6.3,Y+1.4,'+',fontsize=10)
box(14,Y-4.5,16,9,'導納函數\n'+r'$P_d=(J_d s+B_d)^{-1}$','#e8f0fb'); arr(10.8,Y,14,Y)
arr(30.3,Y,37,Y,r'$\dot q_c$'); box(37,Y-4.5,8,9,r'$\times\, r$'+'\n減速比','#ffffff')
box(50,Y-4.5,17,9,'AK 關節馬達\n伺服速度迴路','#eaf5e6'); arr(45.3,Y,50,Y,r'$\dot q_{m,c}$')
box(73,Y-6,20,12,'人體–外骨骼\n耦合系統 (HES)','#f2f2f2'); arr(67.3,Y,73,Y,r'$\tau_l$')
ax.text(83,51,r'$\tau_h$ 穿戴者  $\tau_b$ 上身＋7 kg 負載  $J^TF_{GR}$ 地面反力',ha='center',fontsize=9.5); arr(83,49.6,83,Y+6.3)
arr(93.3,Y,108,Y,r'$q,\ \dot q$',tx=-4.2,ty=1.0)
# gravity term
box(14,Y+7,16,6,r'重力項 $\tau_g=P_g(q)$','#fbeaea',fs=9.5); line([100,100],[Y,Y+10]); arr(100,Y+10,30.3,Y+10)
line([13.7,9],[Y+10,Y+10]); arr(9,Y+10,9,Y+1.8); ax.text(10,Y+2.2,'-',fontsize=14)
# DOB
box(40,10,46,10,'外擾估測器 (DOB)\n'+r'$\hat\tau_h=\hat\tau_e(q,\dot q,\ddot q)-K_t i_q-\hat\tau_b-J^T F_{GR}$','#fdf6e3',fs=9.5)
line([104,104],[Y,15]); arr(104,15,86.3,15,r'$q,\dot q,i_q$',ty=0.8)
box(90,1,18,7,'軀幹 IMU：'+r'$q_B$'+'\n足底感測：'+r'$F_{GR}$','#ffffff',fs=8.5); arr(90,4.5,72,9.7)
box(18,11,13,8,'低通濾波\n'+r'$Q(s)$','#ffffff'); arr(39.7,15,31.3,15,r'$\hat\tau_h$',ty=0.8)
line([17.7,4],[15,15]); line([4,4],[15,Y]); 
ax.text(55,24,'系統鑑別結果（第 6.2、6.3 節）提供 '+r'$K_t$'+'、摩擦與重力參數',ha='center',fontsize=8.5,color='#444')
plt.savefig('figs2/f_adm.png',bbox_inches='tight',facecolor='white')
