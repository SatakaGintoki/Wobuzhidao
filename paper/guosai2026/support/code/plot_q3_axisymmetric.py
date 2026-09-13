"""Plot verified Q3 end-face sensitivity using saved arrays only."""
import hashlib
import json

import numpy as np

from problem2 import setup_mpl
from q3_axisymmetric import OUT
from utils import FIGURES_DIR


def main():
    summary=json.loads((OUT/"comparison.json").read_text(encoding="utf-8"))
    if not summary["pass"]:
        raise RuntimeError("Comparison must pass before plotting")
    path=OUT/f"{summary['production']}.npz"
    data=np.load(path)
    history=np.loadtxt(OUT/"paired_history.csv",delimiter=",",skiprows=1)
    C=data["t129600"][:,:,1]
    z=np.r_[-data["z"][:0:-1],data["z"]]*100
    r=np.r_[-data["r"][:0:-1],data["r"]]*100
    full=np.concatenate([C[:,:0:-1],C],axis=1)
    full=np.concatenate([full[:0:-1],full],axis=0)
    plt=setup_mpl()
    fig=plt.figure(figsize=(7.2,3.55),layout="constrained")
    gs=fig.add_gridspec(2,2,height_ratios=[.62,1.18],hspace=.06,wspace=.16)
    field=fig.add_subplot(gs[0,:])
    levels=np.linspace(np.floor(full.min()*100)/100,np.ceil(full.max()*100)/100,29)
    im=field.contourf(z,r,full,levels=levels,cmap="viridis")
    field.contour(z,r,full,levels=[.08,.12,.16,.18],colors="white",linewidths=.45,alpha=.65)
    field.set_aspect("equal")
    field.set(xlabel="轴向距离 $z$ / cm",ylabel="横向位置 / cm",xlim=(-12.5,12.5),ylim=(-2,2))
    field.text(.01,1.04,"(a) 36 h 含水率分布",transform=field.transAxes,fontsize=9)
    cb=fig.colorbar(im,ax=field,orientation="horizontal",fraction=.08,pad=.10,aspect=48)
    cb.set_label("干基含水率 / (kg/kg)",fontsize=8)
    cb.set_ticks([.05, .08, .11, .14, .17])
    cb.ax.xaxis.set_major_formatter("{x:.2f}")
    cb.ax.tick_params(labelsize=8)
    ax=fig.add_subplot(gs[1,0])
    ax.plot(history[:,0]/3600,history[:,1],color="#B65B3B",lw=1.8,label="配对一维")
    ax.plot(history[:,0]/3600,history[:,2],color="#247B87",lw=1.3,ls="--",label="二维开放端面")
    ax.axhline(.15,color=".45",lw=.8,ls=":",label="阈值 0.15")
    ax.set(xlabel="时间 / h",ylabel="全域最大含水率 / (kg/kg)",xlim=(0,60),ylim=(0,2.65))
    ax.text(.02,1.03,"(b) 全域最大含水率",transform=ax.transAxes,fontsize=9)
    ax.legend(frameon=False,fontsize=8)
    diff=fig.add_subplot(gs[1,1])
    diff.plot(history[:,0]/3600,history[:,3]*1e5,color="#247B87",lw=1.3)
    diff.axhline(0,color=".5",ls=":",lw=.8)
    diff.set(xlabel="时间 / h",ylabel="二维减一维 / ($10^{-5}$ kg/kg)",xlim=(0,60))
    diff.text(.02,1.03,"(c) 同时刻、同径向网格的差异",transform=diff.transAxes,fontsize=9)
    for axis in (ax,diff):
        axis.spines[["top","right"]].set_visible(False)
    FIGURES_DIR.mkdir(exist_ok=True)
    for ext in ("pdf","png"):
        fig.savefig(FIGURES_DIR/f"q3_axisymmetric_check.{ext}",dpi=200,bbox_inches="tight")
    plt.close(fig)
    evidence={"figure":"figures/q3_axisymmetric_check.pdf","field_time_s":129600,
              "sources":{str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in (path,OUT/"paired_history.csv",OUT/"comparison.json")},
              "field_reconstruction":"Mirror the symmetric half-cylinder across z=0 and transverse axis.",
              "curve_comparison":"Matched radial mesh; common exact 600 s sample times only."}
    (OUT/"figure_provenance.json").write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding="utf-8")


if __name__=="__main__":
    main()
