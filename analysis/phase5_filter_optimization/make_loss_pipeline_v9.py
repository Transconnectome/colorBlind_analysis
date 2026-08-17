#!/usr/bin/env python3
"""
Phase 2 Loss Pipeline — v9  (publication pass).
Fixes over v8 (user: too busy, text overflow, redundant text, flat landscape):
  - REMOVE heavy pastel panel fills + decorative ⇒ arrows → clean white panels,
    thin colored header rule per panel (journal style)
  - TRIM redundant text (bar z² annotations, micro-captions, mechanism lines)
  - LANDSCAPE: contourf topographic levels (nonlinear, dense near min) + labeled
    contours + crosshair → clear basin, not a flat ramp
  - guarantee no overflow (measured boxes, smaller consistent font ladder)
  - keep CVD-safe viridis dissim RDMs + faithful 45°-shift worked example
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe
import numpy as np
from scipy.ndimage import gaussian_filter

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica Neue', 'DejaVu Sans'],
    'font.size': 9, 'axes.titlesize': 9.5, 'axes.labelsize': 9,
    'xtick.labelsize': 8, 'ytick.labelsize': 8, 'legend.fontsize': 8,
    'axes.linewidth': 0.8,
    'xtick.major.width': 0.7, 'ytick.major.width': 0.7,
    'xtick.major.size': 2.5, 'ytick.major.size': 2.5,
})

C_BEH  = '#B23A1E'; C_NEU = '#1A6B4A'; C_COMP = '#143A66'
C_MED  = '#666666'; C_LIGHT='#C8C8C8'; WHITE='#FFFFFF'; C_DARK='#1A1A1A'
C_BEH_M='#E3A99B'; C_NEU_M='#9ECFB3'

# ─── 8 CIE L*a*b* hues ────────────────────────────────────────────────────────
def lab_to_rgb(L,a_s,b_s):
    fy=(L+16)/116; fx=a_s/500+fy; fz=fy-b_s/200
    def fi(t): return t**3 if t>6/29 else 3*(6/29)**2*(t-4/29)
    X,Y,Z=0.95047*fi(fx),1.0*fi(fy),1.08883*fi(fz)
    r= 3.2404542*X-1.5371385*Y-0.4985314*Z
    g=-0.9692660*X+1.8760108*Y+0.0415560*Z
    b= 0.0556434*X-0.2040259*Y+1.0572252*Z
    def gam(v): return 1.055*max(0,min(1,v))**(1/2.4)-.055 if v>.0031308 else 12.92*max(0,min(1,v))
    return tuple(gam(v) for v in (r,g,b))

hue_deg  = np.array([0,45,90,135,180,225,270,315])
hue_shrt = ['R','O','Y','G','C','B','P','M']
hue_rgb  = [lab_to_rgb(75,40*np.cos(np.radians(a)),40*np.sin(np.radians(a))) for a in hue_deg]
deutan_shift = np.array([+32,+22,+10,-8,0,0,0,+10])
cvd_deg = (hue_deg + deutan_shift) % 360

def circ_rdm(angles):
    n=len(angles); M=np.zeros((n,n))
    for i in range(n):
        for j in range(n):
            d=abs(angles[i]-angles[j])%360; M[i,j]=min(d,360-d)/180.
    return M
hc_rdm=circ_rdm(hue_deg); cvd_rdm=circ_rdm(cvd_deg)
np.fill_diagonal(hc_rdm,0); np.fill_diagonal(cvd_rdm,0)
delta_obs=cvd_rdm-hc_rdm

# sub-08 deutan filter → continuous δθ → nearest 45° bin (exact method)
bs_f,bc_f,tc=6,-42,150
dth=bs_f*np.cos(np.radians(hue_deg)-np.pi/2)+bc_f*np.cos(np.radians(hue_deg)-np.radians(tc))
perceived=(hue_deg+dth)%360.0
pbin=np.array([int(round(p/45.))%8 for p in perceived])
signed_shift=np.array([int(round(p/45.))-i for i,p in enumerate(perceived)])
delta_sim=np.zeros((8,8))
for i in range(8):
    for j in range(8):
        delta_sim[i,j]=hc_rdm[pbin[i],pbin[j]]-hc_rdm[i,j]

# JND
pair_nm=['OY','YG','YP','GB','RC','BP','RP','OG']
hc_jnd=np.array([2.1,1.8,2.4,2.2,1.9,2.3,2.0,2.1]); hc_sd=np.array([.40,.35,.50,.45,.38,.42,.40,.38])
cvd_obs_b=np.array([.55,.48,2.15,1.90,.50,2.20,1.82,.60]); pred_b=np.array([.58,.50,2.05,1.88,.52,2.18,1.80,.62])

# landscapes (steeper well, light blur → topographic)
bs_arr=np.arange(0,52,2); bc_arr=np.arange(-50,52,2); BS,BC=np.meshgrid(bs_arr,bc_arr)
np.random.seed(7)
r08=0.026*(BS-6)**2+0.019*(BC+42)**2+0.007*(BS-6)*(BC+42)+np.random.randn(*BS.shape)*.07
land08=gaussian_filter(r08,sigma=1.0); land08=(land08-land08.min())/(land08.max()-land08.min())
np.random.seed(13)
r09=0.026*(BS-2)**2+0.019*(BC-24)**2+0.006*(BS-2)*(BC-24)+np.random.randn(*BS.shape)*.07
land09=gaussian_filter(r09,sigma=1.0); land09=(land09-land09.min())/(land09.max()-land09.min())

triu=np.triu_indices(8,k=1); ov=delta_obs[triu]; sv=delta_sim[triu]
cos_v=np.dot(ov,sv)/(np.linalg.norm(ov)*np.linalg.norm(sv)+1e-9); l_rdm=1-cos_v

# ══════════════════════════════════════════════════════════════════════════════
fig=plt.figure(figsize=(23,8.0)); fig.patch.set_facecolor(WHITE)
outer=gridspec.GridSpec(1,3,figure=fig,left=.028,right=.985,top=.855,bottom=.070,
                        wspace=.10,width_ratios=[0.92,1.22,0.95])

gs_A=gridspec.GridSpecFromSubplotSpec(3,2,subplot_spec=outer[0],
     height_ratios=[0.17,1.0,0.40],width_ratios=[0.46,0.54],hspace=0.34,wspace=0.30)
gs_B=gridspec.GridSpecFromSubplotSpec(3,1,subplot_spec=outer[1],
     height_ratios=[0.17,1.0,0.80],hspace=0.34)
gs_C=gridspec.GridSpecFromSubplotSpec(3,2,subplot_spec=outer[2],
     height_ratios=[0.17,1.0,0.44],hspace=0.30,wspace=0.16)

# subtle panel frames (no fill)
for sp,ec in [(outer[0],C_BEH),(outer[1],C_NEU),(outer[2],C_COMP)]:
    bb=sp.get_position(fig)
    fig.add_artist(mpatches.FancyBboxPatch((bb.x0,bb.y0),bb.width,bb.height,
        boxstyle="round,pad=.006",transform=fig.transFigure,fc='none',ec='#E0E0E0',
        lw=1.0,zorder=0,clip_on=False))

fig.text(.5,.955,'Loss-function computation pipeline',ha='center',fontsize=15,fontweight='bold',color=C_DARK)
fig.text(.5,.915,r'per candidate $(\beta_s,\beta_c)$:  '
    r'$\delta\theta(c)=\beta_s\cos(\theta-90°)+\beta_c\cos(\theta-\theta_\mathrm{conf})$'
    r'  $\rightarrow$  loss atoms  $\rightarrow$  z-scored composite  $\rightarrow$  argmin',
    ha='center',fontsize=10,color=C_MED)

def header(ax,letter,title,color):
    ax.axis('off')
    ax.text(0.0,.42,letter,transform=ax.transAxes,fontsize=15,fontweight='bold',color=color,va='center')
    ax.text(.065,.42,title,transform=ax.transAxes,fontsize=12,fontweight='bold',color=color,va='center')
    ax.plot([0,1],[.0,.0],transform=ax.transAxes,color=color,lw=1.6,clip_on=False)

def draw_rdm(ax,data,title,cmap,vmin,vmax,cbar_lbl,hl_cell=None):
    im=ax.imshow(data,cmap=cmap,vmin=vmin,vmax=vmax,aspect='equal',interpolation='nearest')
    ax.set_xticks(range(8)); ax.set_yticks(range(8))
    ax.set_xticklabels(hue_shrt,fontsize=7.5); ax.set_yticklabels(hue_shrt,fontsize=7.5)
    for j,tk in enumerate(ax.get_xticklabels()): tk.set_color(hue_rgb[j]); tk.set_fontweight('bold')
    for j,tk in enumerate(ax.get_yticklabels()): tk.set_color(hue_rgb[j]); tk.set_fontweight('bold')
    ax.set_title(title,fontsize=9,fontweight='bold',color=C_DARK,pad=4)
    cb=plt.colorbar(im,ax=ax,fraction=.046,pad=.04,shrink=.82)
    cb.ax.tick_params(labelsize=6.5); cb.set_label(cbar_lbl,fontsize=7)
    for sp in ax.spines.values(): sp.set_color(C_LIGHT); sp.set_linewidth(.7)
    if hl_cell is not None:
        i,j=hl_cell
        for (a,b) in [(j,i),(i,j)]:
            ax.add_patch(Rectangle((a-0.5,b-0.5),1,1,fill=False,edgecolor='#111111',lw=2.2,zorder=6))

# ═══════════ PANEL A ═════════════════════════════════════════════════════════
header(fig.add_subplot(gs_A[0,:]),'A',r'Behavioral loss  $(\gamma)$',C_BEH)
ax_circ=fig.add_subplot(gs_A[1,0],polar=True)
ax_bar =fig.add_subplot(gs_A[1,1])
ax_til =fig.add_subplot(gs_A[2,:]); ax_til.axis('off')

ang=np.radians(hue_deg); cvd_ang=np.radians(cvd_deg)
ax_circ.set_facecolor(WHITE); ax_circ.spines['polar'].set_visible(False)
for i,(a,col) in enumerate(zip(ang,hue_rgb)):
    ax_circ.scatter(a,1.0,s=150,color=col,zorder=5,linewidths=1.4,edgecolors='white')
    ax_circ.text(a,1.28,hue_shrt[i],ha='center',va='center',fontsize=8.5,fontweight='bold',color=col,
                 path_effects=[pe.withStroke(linewidth=1.4,foreground='white')])
for i,(ah,ac,col) in enumerate(zip(ang,cvd_ang,hue_rgb)):
    ax_circ.scatter(ac,.64,s=80,color=col,zorder=4,marker='D',alpha=.9,edgecolors=C_BEH,linewidths=1.2)
    if abs(deutan_shift[i])>3:
        ax_circ.annotate('',xy=(ac,.69),xytext=(ah,.93),
            arrowprops=dict(arrowstyle='-|>',color=C_BEH,lw=1.4,mutation_scale=8,
                            connectionstyle='arc3,rad=0.18'),zorder=6)
ax_circ.set_xticks(ang); ax_circ.set_xticklabels([]); ax_circ.set_yticks([])
ax_circ.set_ylim(0,1.45); ax_circ.grid(alpha=.10,lw=.5,ls='--')
ax_circ.set_title(r'hue shift $\delta\theta(c)$',fontsize=9,fontweight='bold',pad=8,color=C_DARK)
ax_circ.legend(handles=[Line2D([0],[0],marker='o',color='w',mfc='gray',mec='white',ms=7,label='HC'),
                        Line2D([0],[0],marker='D',color='w',mfc='gray',mec=C_BEH,ms=6,label=r'CVD $\delta\theta$')],
               loc='lower center',bbox_to_anchor=(.5,-.13),ncol=2,fontsize=7.5,framealpha=.9,
               handletextpad=.3,columnspacing=.7,borderpad=.3)

x=np.arange(len(pair_nm)); w=.30
ax_bar.bar(x-w/2,hc_jnd,w,color='#CFCFCF',ec='#999999',lw=.6,zorder=3,label='HC ± SD')
ax_bar.errorbar(x-w/2,hc_jnd,yerr=hc_sd,fmt='none',ecolor='#555555',capsize=2,elinewidth=.8,zorder=4)
ax_bar.bar(x+w/2,pred_b,w,color=C_BEH,alpha=.9,ec='#7E2415',lw=.6,zorder=3,label=r'$\delta\theta_\mathrm{pred}$')
ax_bar.scatter(x+w/2,cvd_obs_b,s=22,color='#111111',zorder=5,label='CVD obs.')
ax_bar.set_xticks(x); ax_bar.set_xticklabels(pair_nm,fontsize=8)
ax_bar.set_ylabel('JND (norm.)',fontsize=9); ax_bar.set_ylim(0,3.0)
ax_bar.set_title(r'$z^2=\left((\delta\theta_\mathrm{pred}-\mathrm{JND}_\mathrm{CVD})/\mathrm{SD}_\mathrm{HC}\right)^2$',
                 fontsize=10.5,color=C_BEH,fontweight='bold',pad=4)
ax_bar.legend(fontsize=7.5,loc='upper right',framealpha=.85,handlelength=1.0,borderpad=.3)
ax_bar.tick_params(labelsize=8)
for sp in ['top','right']: ax_bar.spines[sp].set_visible(False)
for sp in ['left','bottom']: ax_bar.spines[sp].set_color(C_LIGHT)

for xi,nm,sub in [(.255,r'$\gamma_\mathrm{focal}$','single-pair  $z^2$'),
                   (.745,r'$\gamma_\mathrm{all}$',r'sum of 8-pair  $z^2$')]:
    ax_til.add_patch(FancyBboxPatch((xi-.225,.16),.45,.70,boxstyle="round,pad=.03",
        transform=ax_til.transAxes,fc='none',ec=C_BEH,lw=1.8,zorder=3))
    ax_til.text(xi-.085,.51,nm,transform=ax_til.transAxes,ha='center',va='center',
                fontsize=18,fontweight='bold',color=C_BEH,zorder=4)
    ax_til.text(xi+.085,.51,sub,transform=ax_til.transAxes,ha='center',va='center',
                fontsize=12,color=C_DARK,zorder=4)

# ═══════════ PANEL B ═════════════════════════════════════════════════════════
header(fig.add_subplot(gs_B[0]),'B',r'Neural RDM loss  $(L_\mathrm{RDM})$',C_NEU)
gs_B1=gridspec.GridSpecFromSubplotSpec(1,3,subplot_spec=gs_B[1],wspace=0.55)
axh=fig.add_subplot(gs_B1[0]); axs=fig.add_subplot(gs_B1[1]); axo=fig.add_subplot(gs_B1[2])
dmax=max(abs(delta_obs).max(),abs(delta_sim).max())*1.05
draw_rdm(axh,hc_rdm,r'$\overline{\mathrm{RDM}}_\mathrm{HC}$','viridis',0,1,'dissim.')
draw_rdm(axs,delta_sim,r'$\Delta\mathrm{RDM}_\mathrm{sim}$','RdBu_r',-dmax,dmax,r'$\Delta$',hl_cell=(0,3))
draw_rdm(axo,delta_obs,r'$\Delta\mathrm{RDM}_\mathrm{obs}$','RdBu_r',-dmax,dmax,r'$\Delta$')

axe=fig.add_subplot(gs_B[2]); axe.axis('off'); axe.set_xlim(0,30); axe.set_ylim(0,10)
axe.add_patch(FancyBboxPatch((0.2,0.3),29.6,9.4,boxstyle="round,pad=0.1",
    fc='#F6FBF8',ec=C_NEU_M,lw=1.2,zorder=0))
axe.plot([12.6,12.6],[0.9,8.3],color=C_NEU_M,lw=.9,ls='--',zorder=1)
axe.plot([20.4,20.4],[0.9,8.3],color=C_NEU_M,lw=.9,ls='--',zorder=1)

def swatch(xc,yc,col,lbl):
    axe.add_patch(FancyBboxPatch((xc-0.52,yc-0.78),1.04,1.56,boxstyle="round,pad=0.03",
        fc=col,ec='white',lw=1.2,zorder=4))
    axe.text(xc,yc,lbl,ha='center',va='center',fontsize=8,fontweight='bold',color='white',
             zorder=5,path_effects=[pe.withStroke(linewidth=1.5,foreground='#333333')])

axe.text(6.4,9.05,r'1.  hue $\rightarrow$ 45° bin shift',ha='center',fontsize=9,fontweight='bold',color=C_NEU)
axe.text(0.6,7.0,'stim',ha='left',va='center',fontsize=7,color=C_MED,style='italic')
axe.text(0.6,2.7,'perc',ha='left',va='center',fontsize=7,color=C_MED,style='italic')
x0=2.3; dx=1.30
for i in range(8):
    xc=x0+i*dx; sh=signed_shift[i]
    swatch(xc,7.0,hue_rgb[i],hue_shrt[i]); swatch(xc,2.7,hue_rgb[pbin[i]],hue_shrt[pbin[i]])
    if sh!=0:
        axe.annotate('',xy=(xc,3.6),xytext=(xc,6.2),
            arrowprops=dict(arrowstyle='-|>',color=C_BEH,lw=1.6,mutation_scale=10),zorder=3)
        axe.text(xc+0.15,4.9,f'{sh:+d}',ha='left',va='center',fontsize=8,fontweight='bold',color=C_BEH)
    else:
        axe.annotate('',xy=(xc,3.6),xytext=(xc,6.2),
            arrowprops=dict(arrowstyle='-',color=C_LIGHT,lw=1.0,ls=(0,(2,2))),zorder=2)

axe.text(16.5,9.05,'2.  one RDM cell (R–G)',ha='center',fontsize=9,fontweight='bold',color=C_NEU)
swatch(14.2,6.7,hue_rgb[0],'R'); swatch(15.7,6.7,hue_rgb[3],'G')
axe.text(16.6,6.7,r'$d_\mathrm{HC}=0.75$',ha='left',va='center',fontsize=8.5,color=C_DARK)
axe.annotate('',xy=(15.0,4.9),xytext=(15.0,5.9),
    arrowprops=dict(arrowstyle='-|>',color=C_BEH,lw=1.5,mutation_scale=10))
swatch(14.2,4.0,hue_rgb[1],'O'); swatch(15.7,4.0,hue_rgb[2],'Y')
axe.text(16.6,4.0,r'$d_\mathrm{sim}=0.25$',ha='left',va='center',fontsize=8.5,color=C_DARK)
axe.text(16.5,1.8,r'$\Delta=-0.50$',ha='center',va='center',fontsize=9.5,color=C_BEH,fontweight='bold',
         bbox=dict(boxstyle='round,pad=.25',fc='white',ec=C_BEH,lw=1.2))

axe.text(25.2,9.05,'3.  cosine loss',ha='center',fontsize=9,fontweight='bold',color=C_NEU)
axe.text(25.2,5.0,r'$L_\mathrm{RDM}=1-\cos(\Delta_\mathrm{sim},\Delta_\mathrm{obs})$'+'\n\n'
    +fr'$=1-{cos_v:.3f}={l_rdm:.3f}$',ha='center',va='center',fontsize=10,color=C_NEU,fontweight='bold',
    bbox=dict(boxstyle='round,pad=.45',fc='#EAF5EF',ec=C_NEU,lw=1.6))

# ═══════════ PANEL C ═════════════════════════════════════════════════════════
header(fig.add_subplot(gs_C[0,:]),'C',r'Composite $\rightarrow$ argmin',C_COMP)
axl8=fig.add_subplot(gs_C[1,0]); axl9=fig.add_subplot(gs_C[1,1])
axt8=fig.add_subplot(gs_C[2,0]); axt9=fig.add_subplot(gs_C[2,1])

LV=np.array([0,.015,.04,.08,.14,.22,.32,.45,.60,.78,1.0])   # dense near minimum
def landscape(ax,land,bs,bc,subj,lc):
    cf=ax.contourf(bs_arr,bc_arr,land,levels=LV,cmap='viridis_r')
    ax.contour(bs_arr,bc_arr,land,levels=LV,colors='white',linewidths=.5,alpha=.45)
    cb=plt.colorbar(cf,ax=ax,fraction=.046,pad=.03,ticks=[0,.25,.5,.75,1.0])
    cb.ax.tick_params(labelsize=8); cb.set_label('composite loss',fontsize=8)
    ax.axhline(bc,color='white',lw=.7,ls=':',alpha=.6); ax.axvline(bs,color='white',lw=.7,ls=':',alpha=.6)
    ax.scatter(bs,bc,s=240,color='white',marker='*',edgecolors=C_COMP,linewidths=1.6,zorder=6)
    ax.text(bs+3,bc+(6 if bc<0 else -10),fr'$({bs}°,\,{bc}°)$',fontsize=10,color='white',
            fontweight='bold',path_effects=[pe.withStroke(linewidth=2.4,foreground='#0A0A0A')])
    ax.set_xlabel(r'$\beta_s$ (°)',fontsize=10); ax.set_ylabel(r'$\beta_c$ (°)',fontsize=10)
    ax.set_title(subj,fontsize=10.5,fontweight='bold',color=lc,pad=5)
    ax.tick_params(labelsize=9); ax.set_xlim(0,50); ax.set_ylim(-50,50)

landscape(axl8,land08,6,-42,'sub-08 deutan','#C0561F')
landscape(axl9,land09,2,24,'sub-09 protan','#1A6B4A')

def tile(ax,lc,subj,params,extra):
    ax.set_facecolor(C_COMP); ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_edgecolor(lc); sp.set_linewidth(2.4)
    ax.text(.5,.74,subj,transform=ax.transAxes,ha='center',va='center',fontsize=11,fontweight='bold',color=lc)
    ax.text(.5,.42,params,transform=ax.transAxes,ha='center',va='center',fontsize=15,fontweight='bold',color='white')
    ax.text(.5,.13,extra,transform=ax.transAxes,ha='center',va='center',fontsize=10,color='#C6D2EA')

tile(axt8,'#E0905A','sub-08 deutan',r'$(\beta_s^*,\beta_c^*)=(+6°,\,-42°)$','IQR (8, 2) · mode ~70%')
tile(axt9,'#46A87A','sub-09 protan',r'$(\beta_s^*,\beta_c^*)=(+2°,\,+24°)$','IQR (0, 0) · mode 87.7%')

fig.text(.5,.022,'Illustrative data; the 45° RDM-shift step reproduces the implemented method '
         '(s10b_v6_pca_rdm.py). Grid step 2°.',ha='center',fontsize=7.5,color=C_MED,style='italic')

out='results/figures/loss_pipeline_v9.png'
plt.savefig(out,dpi=300,bbox_inches='tight',facecolor=WHITE)
print(f'Saved: {out}')
