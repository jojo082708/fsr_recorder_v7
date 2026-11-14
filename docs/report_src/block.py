import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle
from matplotlib import font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc')
plt.rcParams['font.family']='WenQuanYi Zen Hei'; plt.rcParams['mathtext.fontset']='stix'
fig,ax=plt.subplots(figsize=(10,4.2),dpi=200); ax.set_xlim(0,100); ax.set_ylim(0,42); ax.axis('off')
def box(x,y,w,h,t,fc='#ffffff'):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.3',fc=fc,ec='black',lw=1.2)); ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=10)
def arr(x1,y1,x2,y2,t='',tx=0,ty=1.2,**k):
    ax.annotate('',xy=(x2,y2),xytext=(x1,y1),arrowprops=dict(arrowstyle='-|>',lw=1.1,color='black'))
    if t: ax.text((x1+x2)/2+tx,(y1+y2)/2+ty,t,ha='center',fontsize=10)
def line(xs,ys): ax.plot(xs,ys,color='black',lw=1.1)
Y=28
ax.text(0.5,Y,r'$\theta_d$',fontsize=12,va='center')
box(6,Y-4,21,8,'阻抗模型\n'+r'$M_v\ddot\theta_e+B_v\dot\theta_e+K_v\theta_e=\hat\tau_{ext}$','#e8f0fb')
arr(4,Y,6,Y)
ax.add_patch(Circle((32,Y),1.8,fc='white',ec='black')); ax.text(32,Y,'Σ',ha='center',va='center',fontsize=11)
arr(27.3,Y,30.2,Y,r'$\theta_{cmd}$'); ax.text(29.6,Y+1.6,'+',fontsize=10); 
box(37,Y-4,15,8,'位置控制器\n(PD：'+r'$K_p,K_D$'+')','#eaf5e6'); arr(33.8,Y,37,Y,'e',ty=0.8)
box(57,Y-4,12,8,'力矩/電流\n限制','#fbeaea'); arr(52.3,Y,57,Y,r'$i_{q,cmd}$')
box(74,Y-5,17,10,'AK 關節馬達\n＋外骨骼關節','#f2f2f2'); arr(69.3,Y,74,Y)
arr(91.3,Y,98,Y,r'$\theta,\ \omega$')
# human force
ax.text(82.5,40,'穿戴者交互力矩 '+r'$\tau_h$',ha='center',fontsize=10); arr(82.5,38.8,82.5,Y+5.3)
# angle feedback
line([95,95,32],[Y,14,14]); arr(32,14,32,Y-1.8); ax.text(33,Y-4.6,'-',fontsize=13)
ax.text(60,14.8,r'角度回授 $\theta$',fontsize=10)
# estimator
box(40,2,34,8,'外力估測  '+r'$\hat\tau_{ext}=K_t i_q-(\hat J\alpha+\hat B\omega+\hat\tau_c+\hat\tau_g)$','#fdf6e3')
line([88,88],[Y-5.3,6]); arr(88,6,74.3,6,r'$i_q,\ \theta,\ \omega$',ty=0.8)
line([39.7,16.5],[6,6]); arr(16.5,6,16.5,Y-4.3); ax.text(17.3,12,r'$\hat\tau_{ext}$',fontsize=11)
ax.text(57,1.0-1,'$K_t$、$\\hat\\tau_c$、$\\hat\\tau_g$ 取自第 6.2、6.3 節系統鑑別結果',ha='center',fontsize=8.5,color='#444')
plt.savefig('figs2/f_block.png',bbox_inches='tight',facecolor='white')
