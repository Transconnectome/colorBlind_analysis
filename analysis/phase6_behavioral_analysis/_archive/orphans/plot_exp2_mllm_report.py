#!/usr/bin/env python3
"""Reporting figure for exp2 behavioral filter evaluation (deficit-anchor + HLLM auditor + RSVP CI).
Panels: (A,B) JND per-pair distance-to-HC & targeting; (C) HLLM specification auditor;
        (D) RSVP aggregate Wilson CI; (E,F) RSVP per-color targeting.
Output: results/exp2_behavior/fig_exp2_mllm_report.png"""
import warnings, os, numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import statsmodels.formula.api as smf
from scipy.stats import t as tdist, ttest_rel, binomtest, fisher_exact
warnings.filterwarnings("ignore")
rng = np.random.default_rng(0)

def star(p):
    return '***' if p<0.001 else '**' if p<0.01 else '*' if p<0.05 else 'n.s.'

ROOT = "/Users/jinilkim/LocalProj/colorBlind_analysis"
BEH  = f"{ROOT}/data/behavior"
OUT  = f"{ROOT}/analysis/phase6_behavioral_analysis/results/exp2_behavior"
HC   = [f"sub-0{i}" for i in range(1,8)]
PAIRS= ['orange-yellow','yellow-green','green-blue','red-orange',
        'blue-purple','yellow-purple','cyan-magenta','red-cyan']
HUES = ['red','orange','yellow','green','cyan','blue','purple','magenta']
HUE_HEX = {'red':'#d62728','orange':'#ff7f0e','yellow':'#e6c200','green':'#2ca02c',
           'cyan':'#17becf','blue':'#1f77b4','purple':'#9467bd','magenta':'#e377c2'}
HUEMAP = {i+1:h for i,h in enumerate(HUES)}

def jnd(path): return pd.read_csv(path).groupby('pair_name')['jnd_mean'].mean()
def stairs(sid, cond, run):
    p = (f"{BEH}/{sid}_jnd_ses1_no_filter_summary.csv" if cond=='baseline'
         else f"{BEH}/2nd_exp/{sid}/jnd_ses2_run{run}_{'window_no_filter' if cond=='window' else f'optimal_{sid}'}_summary.csv")
    d = pd.read_csv(p)[['pair_name','jnd_mean']].copy(); d['condition']=cond; return d
def ch_z(x, ctrl):
    ctrl=np.asarray(ctrl,float); m,s=ctrl.mean(),ctrl.std(ddof=1); return (x-m)/s
def ch_p(x, ctrl):
    """Crawford-Howell two-tailed p (single case vs n control sample)."""
    ctrl=np.asarray(ctrl,float); n=ctrl.size; m,s=ctrl.mean(),ctrl.std(ddof=1)
    tval=(x-m)/(s*np.sqrt((n+1)/n)); return 2*tdist.sf(abs(tval), n-1)

HCm = pd.DataFrame({s:jnd(f"{BEH}/{s}_jnd_ses1_no_filter_summary.csv") for s in HC}).reindex(PAIRS)
hc_mean, hc_sd = HCm.mean(axis=1), HCm.std(axis=1, ddof=1)

fig = plt.figure(figsize=(15, 8.6), constrained_layout=True)
gs = fig.add_gridspec(2, 3)

# ---------- (A,B) JND per-pair: HC band + CVD baseline + optimal ----------
for col, (sid, tag) in enumerate([('sub-08','deutan'),('sub-09','protan')]):
    ax = fig.add_subplot(gs[0, col])
    base = jnd(f"{BEH}/{sid}_jnd_ses1_no_filter_summary.csv").reindex(PAIRS)
    opt  = jnd(f"{BEH}/2nd_exp/{sid}/jnd_ses2_run2_optimal_{sid}_summary.csv").reindex(PAIRS)
    x = np.arange(len(PAIRS))
    ax.fill_between(x, (hc_mean-hc_sd).values, (hc_mean+hc_sd).values, color='0.8', label='HC mean±SD (n=7)', zorder=0)
    ax.plot(x, hc_mean.values, '-', color='0.5', lw=1, zorder=1)
    # deficit markers (baseline z>0 & p<.05)
    for i,p in enumerate(PAIRS):
        z = ch_z(base[p], HCm.loc[p]); df=6
        pv = 2*tdist.sf(abs(z*np.sqrt(6/7)),df)
        if z>0 and pv<0.05: ax.axvspan(i-0.4,i+0.4,color='#ffe08a',alpha=0.35,zorder=0)
    ax.plot(x, base.values, 'o', color='0.25', ms=8, label='no-filter (baseline)', zorder=3)
    ax.plot(x, opt.values,  'D', color='#d1620a', ms=7, label='individualized (optimal)', zorder=3)
    for i in x: ax.annotate('', xy=(i,opt.values[i]), xytext=(i,base.values[i]),
                            arrowprops=dict(arrowstyle='->',color='#d1620a',lw=1.2,alpha=0.7), zorder=2)
    ymax = max(base.max(), 0.3)
    # Crawford-Howell stars: baseline & optimal deviation vs HC (only if significant)
    for i,p in enumerate(PAIRS):
        pb = ch_p(base[p], HCm.loc[p]); po = ch_p(opt[p], HCm.loc[p])
        if pb<0.05: ax.text(i, base.values[i]+0.028*ymax, star(pb), ha='center', va='bottom', color='0.15', fontsize=10, fontweight='bold')
        if po<0.05: ax.text(i, opt.values[i]+0.028*ymax, star(po), ha='center', va='bottom', color='#d1620a', fontsize=10, fontweight='bold')
    ax.set_xticks(x); ax.set_xticklabels(PAIRS, rotation=45, ha='right', fontsize=8)
    ax.set_ylabel('JND threshold'); ax.set_title(f'({"AB"[col]}) {tag} ({sid}) — JND per pair (vs HC, Crawford–Howell)\nyellow band = baseline-deficit pair · * on marker = deviates from HC', fontsize=9.5)
    if col==0: ax.legend(fontsize=7.5, loc='upper right')
    ax.set_ylim(-0.02, ymax*1.15)

# ---------- (C) HLLM auditor: sub-08 optimal effect across specifications ----------
ax = fig.add_subplot(gs[0, 2])
df8 = pd.concat([stairs('sub-08','baseline',None), stairs('sub-08','optimal',2)], ignore_index=True)
df8['condition']=pd.Categorical(df8['condition'],['baseline','optimal'])
# random intercept
mi = smf.mixedlm("jnd_mean ~ C(condition)", df8, groups=df8['pair_name']).fit(reml=True)
ni='C(condition)[T.optimal]'; est_i=mi.params[ni]; ci_i=mi.conf_int().loc[ni].values; p_i=mi.pvalues[ni]
# random slope
ms = smf.mixedlm("jnd_mean ~ C(condition)", df8, groups=df8['pair_name'], re_formula='~C(condition)').fit(reml=True)
est_s=ms.params[ni]; ci_s=ms.conf_int().loc[ni].values; p_s=ms.pvalues[ni]
# paired t on pair means
piv=df8.groupby(['pair_name','condition'])['jnd_mean'].mean().unstack().reindex(PAIRS)
d=(piv['optimal']-piv['baseline']); est_t=d.mean(); se=d.std(ddof=1)/np.sqrt(len(d))
ci_t=(est_t-2.365*se, est_t+2.365*se); p_t=ttest_rel(piv['optimal'],piv['baseline'])[1]
# bootstrap
boots=[np.mean(rng.choice(d.values,len(d),replace=True)) for _ in range(5000)]
ci_b=np.percentile(boots,[2.5,97.5])
# drop orange-yellow
d2=d.drop('orange-yellow'); est_d=d2.mean(); se2=d2.std(ddof=1)/np.sqrt(len(d2))
ci_d=(est_d-2.447*se2, est_d+2.447*se2); p_d=ttest_rel(piv['optimal'].drop('orange-yellow'),piv['baseline'].drop('orange-yellow'))[1]
rows=[("random-int (1|pair)",est_i,ci_i,p_i,False),
      ("random-slope (cond|pair)",est_s,ci_s,p_s,True),
      ("paired t (8 pairs)",est_t,ci_t,p_t,True),
      ("pair bootstrap",est_t,ci_b,None,True),
      ("drop orange-yellow",est_d,ci_d,p_d,True)]
for j,(lab,est,ci,pv,honest) in enumerate(rows):
    y=len(rows)-1-j; c='#2a7f3f' if honest else '#c0392b'
    ax.plot([ci[0],ci[1]],[y,y],'-',color=c,lw=2.5)
    ax.plot(est,y,'o',color=c,ms=7)
    txt=f"p={pv:.2f}" if pv is not None else "CI"
    ax.annotate(txt, xy=(ci[1],y), xytext=(4,0), textcoords='offset points', va='center', fontsize=8, color=c)
ax.axvline(0, color='k', lw=0.8, ls='--')
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=8.5)
ax.set_xlabel('ΔJND (optimal − baseline)'); ax.set_title('(C) HLLM auditor — sub-08 (deutan)\ngreen=honest n.s. · red=misspecified', fontsize=10)
ax.set_xlim(-0.42, 0.12)

# ---------- (D) RSVP aggregate Wilson CI ----------
ax = fig.add_subplot(gs[1, 0])
rsvp={'sub-08 (deutan)':{'baseline':52,'deployed':62,'individualized':62},
      'sub-09 (protan)':{'baseline':64,'deployed':55,'individualized':63}}
conds=['baseline','deployed','individualized']; ccol={'baseline':'0.5','deployed':'#1f77b4','individualized':'#d1620a'}
w=0.25
def brk(ax, x1, x2, y, txt):
    ax.plot([x1,x1,x2,x2],[y,y+0.015,y+0.015,y],color='k',lw=1)
    ax.text((x1+x2)/2, y+0.02, txt, ha='center', va='bottom', fontsize=8.5,
            fontweight=('bold' if txt!='n.s.' else 'normal'))
for gi,(sid,cc) in enumerate(rsvp.items()):
    xp={}
    for ci_,cond in enumerate(conds):
        k=cc[cond]; acc=k/64; r=binomtest(k,64).proportion_ci(method='wilson')
        xpos=gi + (ci_-1)*w; xp[cond]=xpos
        ax.bar(xpos, acc, w*0.92, color=ccol[cond], zorder=2)
        ax.errorbar(xpos, acc, yerr=[[acc-r.low],[r.high-acc]], fmt='none', ecolor='k', capsize=3, lw=1, zorder=3)
    # Fisher-exact: each filter vs baseline
    kb=cc['baseline']
    p_dep=fisher_exact([[cc['deployed'],64-cc['deployed']],[kb,64-kb]])[1]
    p_ind=fisher_exact([[cc['individualized'],64-cc['individualized']],[kb,64-kb]])[1]
    brk(ax, xp['baseline'], xp['deployed'], 1.005, star(p_dep))       # base vs deployed
    brk(ax, xp['baseline'], xp['individualized'], 1.075, star(p_ind))  # base vs individualized
ax.axhline(0.125, color='r', ls=':', lw=1, label='chance (1/8)')
ax.set_xticks(range(len(rsvp))); ax.set_xticklabels(list(rsvp.keys()), fontsize=9)
ax.set_ylabel('8AFC accuracy'); ax.set_ylim(0,1.18); ax.set_title('(D) RSVP accuracy ± Wilson 95% CI (n=64)\nbrackets: filter vs baseline (Fisher exact)', fontsize=9.5)
ax.legend([Patch(color='0.5'),Patch(color='#1f77b4'),Patch(color='#d1620a')],
          ['baseline','deployed','individualized'], fontsize=7.5, loc='lower left')

# ---------- (E,F) RSVP per-color: baseline vs optimal ----------
def rsvp_by_color(path):
    d=pd.read_csv(path); d['tc']=d['stimulus_label'].str.split('_').str[1].astype(int).map(HUEMAP)
    return d.groupby('tc')['correct'].mean().reindex(HUES)
for col,(sid,tag,fb,fo) in enumerate([
    ('sub-08','deutan',f"{BEH}/sub-08_rsvp_8afc_ses1_run1.csv",f"{BEH}/2nd_exp/sub-08/rsvp_8afc_ses2_run2_optimal_sub-08.csv"),
    ('sub-09','protan',f"{BEH}/sub-09_rsvp_8afc_ses1_run1.csv",f"{BEH}/2nd_exp/sub-09/rsvp_8afc_ses2_run2_optimal_sub-09.csv")]):
    ax=fig.add_subplot(gs[1,col+1])
    b=rsvp_by_color(fb); o=rsvp_by_color(fo); x=np.arange(len(HUES))
    ax.bar(x-0.2,b.values,0.4,color=[HUE_HEX[h] for h in HUES],alpha=0.45,label='baseline',edgecolor='0.4')
    ax.bar(x+0.2,o.values,0.4,color=[HUE_HEX[h] for h in HUES],label='individualized',edgecolor='k')
    ax.set_xticks(x); ax.set_xticklabels(HUES,rotation=45,ha='right',fontsize=8)
    ax.set_ylabel('per-color accuracy'); ax.set_ylim(0,1.08)
    ax.set_title(f'({"EF"[col]}) {tag} RSVP per color (base=faint, opt=solid)', fontsize=10)

fig.suptitle('Exp2 behavioral filter evaluation — deficit-anchored (Crawford–Howell) + HLLM auditor + RSVP', fontsize=12, fontweight='bold')
os.makedirs(OUT, exist_ok=True)
fp=f"{OUT}/fig_exp2_mllm_report.png"
fig.savefig(fp, dpi=140, bbox_inches='tight')
print("saved:", fp)
