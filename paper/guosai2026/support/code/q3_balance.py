"""Continuous-solution balance integrals for the accepted Q3 effective model."""
import numpy as np
from numpy.polynomial.legendre import leggauss
from appendix3 import heat_capacity, heat_capacity_deriv, moisture_diffusivity_q2
from utils import R, L, H, HM


def audit_segment(fvm, sol, Ta_fun, Ca_fun, t_end=None, orders=(4,8)):
    if sol.sol is None:
        raise ValueError("balance audit requires a dense solution")
    n = fvm.n_nodes
    start = float(sol.sol.ts[0])
    end = float(sol.sol.ts[-1]) if t_end is None else float(t_end)
    if not start < end <= sol.sol.ts[-1]+1e-9:
        raise ValueError("audit outside dense-solution interval")
    edges = np.r_[sol.sol.ts[sol.sol.ts < end],end]
    edges = np.unique(edges)
    z0, z1 = sol.sol(start), sol.sol(end)
    factor = 2*np.pi*L
    def energy(z):
        return float(factor*np.dot(fvm.W,heat_capacity(z[n:])*(z[:n]-28.)))
    def quadrature(order):
        gx,gw=leggauss(order)
        total=np.zeros(3)
        for j in range(0,len(edges)-1,64):
            aa,bb=edges[j:-1][:64],edges[j+1:][:64]
            tt=((aa+bb)[:,None]/2+(bb-aa)[:,None]/2*gx).ravel()
            Y=sol.sol(tt);T,C=Y[:n],Y[n:]
            Ta,Ca=np.asarray(Ta_fun(tt)),np.asarray(Ca_fun(tt))
            D=moisture_diffusivity_q2(C,T)
            Df=2*D[:-1]*D[1:]/np.maximum(D[:-1]+D[1:],1e-300)
            F=-fvm.r_half[:,None]*Df*np.diff(C,axis=0)/fvm.dr_face[:,None]
            flows=np.vstack([np.zeros((1,len(tt))),F,R*HM*(C[-1]-Ca)])
            Cdot=-np.diff(flows,axis=0)/fvm.W[:,None]
            vals=np.vstack([R*HM*(C[-1]-Ca),factor*R*H*(Ta-T[-1]),
                factor*np.sum(fvm.W[:,None]*heat_capacity_deriv(C)*(T-28.)*Cdot,axis=0)])
            weights=((bb-aa)[:,None]/2*gw).ravel()
            total+=vals@weights
        return total
    integrals={str(o):quadrature(o).tolist() for o in orders}
    return {"start_s":start,"end_s":end,"accepted_intervals":len(edges)-1,
            "M_start":float(fvm.W@z0[n:]),"M_end":float(fvm.W@z1[n:]),
            "E_start":energy(z0),"E_end":energy(z1),"integrals_by_order":integrals}


def combine(parts):
    if not parts:
        raise ValueError('no balance segments')
    for left, right in zip(parts, parts[1:]):
        if abs(left['end_s']-right['start_s']) > 1e-9:
            raise ValueError('balance segments have a time gap or overlap')
        for field in ('M', 'E'):
            if not np.isclose(left[field+'_end'], right[field+'_start'], rtol=1e-12, atol=1e-14):
                raise ValueError('balance segments have a state discontinuity')
    I=np.sum([p['integrals_by_order']['8'] for p in parts],axis=0)
    I4=np.sum([p['integrals_by_order']['4'] for p in parts],axis=0)
    M0,M1=parts[0]['M_start'],parts[-1]['M_end']
    E0,E1=parts[0]['E_start'],parts[-1]['E_end']
    mass_denom=max(abs(M0-M1),abs(I[0]),1e-18)
    heat_denom=max(abs(E1-E0-I[2]),abs(I[1]),1e-12)
    return {
        'moisture':{'M0':M0,'M_end':M1,'surface_integral':float(I[0]),
                    'relative_residual':float(abs(M1-M0+I[0])/mass_denom)},
        'heat':{'E_end_minus_E0':E1-E0,'composition_correction':float(I[2]),'Q_surface':float(I[1]),
                'relative_residual':float(abs(E1-E0-I[2]-I[1])/heat_denom)},
        'quadrature_relative_difference':{'moisture':float(abs(I[0]-I4[0])/mass_denom),
            'heat_and_composition':float((abs(I[1]-I4[1])+abs(I[2]-I4[2]))/heat_denom)},
        'parts':parts,
        'interpretation':'Integrated effective equation with B_prime(C)*(T-28)*Cdot correction; not full multiphase energy conservation.'}
