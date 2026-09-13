"""Plot verified Appendix-4 control trajectories, without rerunning the PDE."""
import json
import numpy as np
from q4_fixed_comparison import OUT
from problem2 import setup_mpl
from utils import FIGURES_DIR


def main():
    result=json.loads((OUT/'comparison.json').read_text(encoding='utf-8'))
    if not result['pass']: raise RuntimeError('Unverified comparison')
    data={k:np.loadtxt(OUT/f'{k}_center.csv',delimiter=',',skiprows=1,encoding='utf-8-sig') for k in ['fixed','shrink']}
    plt=setup_mpl()
    plt.rcParams.update({'font.size':9,'axes.labelsize':9,'legend.fontsize':8,'pdf.fonttype':42})
    fig,(ax,zoom)=plt.subplots(1,2,figsize=(7.2,3.15),gridspec_kw={'width_ratios':[1.05,1]})
    styles={'fixed':('#B65B3B','--','固定半径 $R=R_0$'), 'shrink':('#247B87','-','实测收缩 $R(t)$')}
    for key,a in data.items():
        color,ls,label=styles[key]
        for axis in (ax,zoom):
            axis.plot(a[:,0]/3600,a[:,1],color=color,ls=ls,lw=1.5,label=label)
        zoom.plot(a[-1,0]/3600,a[-1,1],'o',color=color,ms=4)
    for axis in (ax,zoom):
        axis.axhline(.15,color='.4',ls=':',lw=1,label='达标阈值 0.15')
        axis.set_xlabel('时间 / h')
        axis.spines[['top','right']].set_visible(False)
    ax.set(ylabel='中心干基含水率 / (kg/kg)',xlim=(0,138),ylim=(0,2.65))
    ax.legend(frameon=False,loc='upper right')
    zoom.set(xlim=(24,138),ylim=(.135,.43),ylabel='中心干基含水率 / (kg/kg)')
    zoom.annotate(f"{result['shrink_report_h']:.4f} h",(result['shrink_report_h'],.15),xytext=(40,.22),
                  arrowprops={'arrowstyle':'-','color':styles['shrink'][0]},color=styles['shrink'][0],fontsize=8)
    zoom.annotate(f"{result['fixed_report_h']:.4f} h",(result['fixed_report_h'],.15),xytext=(97,.25),
                  arrowprops={'arrowstyle':'-','color':styles['fixed'][0]},color=styles['fixed'][0],fontsize=8)
    fig.tight_layout(w_pad=1.8)
    FIGURES_DIR.mkdir(exist_ok=True)
    fig.savefig(FIGURES_DIR/'q4_fixed_vs_shrink.pdf',bbox_inches='tight')
    fig.savefig(FIGURES_DIR/'q4_fixed_vs_shrink.png',dpi=180,bbox_inches='tight')
    plt.close(fig)


if __name__=='__main__': main()
