"""Ordinary initial axisymmetric FV Poisson + free-space Green boundary check."""
import datetime
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import time

START=time.perf_counter()
import numpy as np

CASES=[('S32',8.,32,(32,64,32)),('S64',8.,64,(32,64,32)),
       ('S128',8.,128,(32,64,32)),('Q64',8.,64,(64,128,64)),
       ('D96',12.,96,(48,96,48))]


def identity(path):
    b=path.read_bytes()
    return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def gauss(n,lo,hi):
    x,w=np.polynomial.legendre.leggauss(n)
    return lo+(hi-lo)*(x+1.)/2.,w*(hi-lo)/2.


def green_boundary(target_r,target_z,R,orders):
    sr,wr=gauss(orders[0],0.,R)
    sz,wz=gauss(orders[1],-R,R)
    theta,wt=gauss(orders[2],0.,math.pi)
    rr,zz=np.meshgrid(sr,sz,indexing='ij')
    mass=(wr[:,None]*wz[None,:]*rr**3*1.5*np.exp(-.5*(rr*rr+zz*zz))).ravel()
    rr=rr.ravel()[None,:];zz=zz.ravel()[None,:]
    out=np.zeros(len(target_r))
    for start in range(0,len(out),8):
        tr=target_r[start:start+8,None];tz=target_z[start:start+8,None]
        base=tr*tr+rr*rr+(tz-zz)**2
        product=2.*tr*rr
        total=np.zeros_like(base)
        for angle,weight in zip(theta,wt):
            den=base-product*math.cos(float(angle))
            assert np.all(den>0.)
            total += float(weight)*math.sin(float(angle))**2*den**(-1.5)
        out[start:start+8]=np.sum(total*mass[None,:],axis=1)/(2.*math.pi)
    assert np.all(np.isfinite(out))
    return out


def poisson(q,h,r,gR,gminus,gplus):
    nr,nz=q.shape
    faces=np.arange(nr+1)*h
    volumes=(faces[1:]**4-faces[:-1]**4)/4.
    left=faces[:-1]**3/(volumes*h)
    right=faces[1:]**3/(volumes*h)
    diag=np.broadcast_to((left+right+2./h**2)[:,None],q.shape).copy()
    diag[-1,:]+=right[-1]
    diag[:,0]+=1./h**2;diag[:,-1]+=1./h**2
    b=q.copy()
    b[-1,:]+=2.*right[-1]*gR
    b[:,0]+=2.*gminus/h**2;b[:,-1]+=2.*gplus/h**2
    def apply(x):
        y=diag*x
        y[1:,:]-=left[1:,None]*x[:-1,:]
        y[:-1,:]-=right[:-1,None]*x[1:,:]
        y[:,1:]-=x[:,:-1]/h**2
        y[:,:-1]-=x[:,1:]/h**2
        return y
    def dot(x,y):
        return float(np.sum(volumes[:,None]*x*y))
    x=np.zeros_like(q);res=b.copy();pre=res/diag;p=pre.copy()
    rz=dot(res,pre);bnorm=math.sqrt(dot(b,b));restarts=0
    for iteration in range(1,2001):
        ap=apply(p);den=dot(p,ap)
        assert den>0. and math.isfinite(den)
        alpha=rz/den;x+=alpha*p;res-=alpha*ap
        relative=math.sqrt(dot(res,res))/bnorm
        assert math.isfinite(relative)
        if relative<=1e-10:
            true_res=b-apply(x)
            true_relative=math.sqrt(dot(true_res,true_res))/bnorm
            if true_relative<=1e-10:
                return x,dict(iterations=iteration,true_weighted_relative_residual=true_relative,
                              recurrence_relative_residual=relative,direction_restarts=restarts)
            res=true_res;pre=res/diag;p=pre.copy();rz=dot(res,pre);restarts+=1
            continue
        pre=res/diag;next_rz=dot(res,pre)
        assert next_rz>0. and math.isfinite(next_rz)
        p=pre+(next_rz/rz)*p;rz=next_rz
    raise RuntimeError('fixed 2000-iteration limit exhausted')


def reconstruct(phi,h,r,gR,gminus,gplus,corners):
    nr,nz=phi.shape
    ghost=np.empty((nr+2,nz+2));ghost[1:-1,1:-1]=phi
    ghost[1:-1,0]=2.*gminus-phi[:,0]
    ghost[1:-1,-1]=2.*gplus-phi[:,-1]
    ghost[0,:]=ghost[1,:]
    ghost[-1,1:-1]=2.*gR-phi[-1,:]
    ghost[-1,0]=4.*corners[0]-ghost[-2,0]-ghost[-1,1]-ghost[-2,1]
    ghost[-1,-1]=4.*corners[1]-ghost[-2,-1]-ghost[-1,-2]-ghost[-2,-2]
    dr=(ghost[2:,1:-1]-ghost[:-2,1:-1])/(2.*h)
    dz=(ghost[1:-1,2:]-ghost[1:-1,:-2])/(2.*h)
    drr=(ghost[2:,1:-1]-2.*phi+ghost[:-2,1:-1])/h**2
    dzz=(ghost[1:-1,2:]-2.*phi+ghost[1:-1,:-2])/h**2
    drz=(ghost[2:,2:]-ghost[2:,:-2]-ghost[:-2,2:]+ghost[:-2,:-2])/(4.*h**2)
    rr=r[:,None]
    u=np.stack((-rr*dz,2.*phi+rr*dr))
    jac=np.stack((-dz-rr*drz,-rr*dzz,-dz,3.*dr+rr*drr,2.*dz+rr*drz))
    assert np.all(np.isfinite(u)) and np.all(np.isfinite(jac))
    return u,jac


def oracle(r,z):
    rr,zz=np.meshgrid(r,z,indexing='ij');distance=np.sqrt(rr*rr+zz*zz)
    f=np.empty_like(distance);d=np.empty_like(distance);e=np.empty_like(distance)
    for index,value in np.ndenumerate(distance):
        radius=float(value);square=radius*radius
        if radius<=.5:
            term=1.;sf=[];sd=[];se=[]
            for n in range(16):
                if n:term*=(-.5*square)/n
                sf.append(term/(2*n+3));sd.append(term/(2*n+5));se.append(term/(2*n+7))
            f[index]=1.5*math.fsum(sf);d[index]=-1.5*math.fsum(sd);e[index]=1.5*math.fsum(se)
        else:
            q=1.5*math.exp(-.5*square)
            f[index]=1.5*(math.sqrt(math.pi/2.)*math.erf(radius/math.sqrt(2.))
                          -radius*math.exp(-.5*square))/radius**3
            d[index]=(q-3.*f[index])/square
            e[index]=(-q-5.*d[index])/square
    u=np.stack((-rr*zz*d,2.*f+rr*rr*d))
    jac=np.stack((-zz*d-rr*rr*zz*e,-rr*d-rr*zz*zz*e,-zz*d,
                  4.*rr*d+rr**3*e,2.*zz*d+rr*rr*zz*e))
    return u,jac


def relative_error(actual,exact,weight,mask):
    numerator=float(np.sum(np.sum((actual-exact)**2,axis=0)[mask]*weight[mask]))
    denominator=float(np.sum(np.sum(exact**2,axis=0)[mask]*weight[mask]))
    return math.sqrt(numerator/denominator)


def solve_case(name,R,nr,orders,local):
    begin=time.perf_counter();nz=2*nr;h=R/nr
    r=(np.arange(nr)+.5)*h;z=-R+(np.arange(nz)+.5)*h
    rr,zz=np.meshgrid(r,z,indexing='ij');q=1.5*np.exp(-.5*(rr*rr+zz*zz))
    tr=np.concatenate((np.full(nz,R),r,r,np.array([R,R])))
    tz=np.concatenate((z,np.full(nr,-R),np.full(nr,R),np.array([-R,R])))
    boundary_start=time.perf_counter();boundary=green_boundary(tr,tz,R,orders)
    boundary_seconds=time.perf_counter()-boundary_start
    gR=boundary[:nz];gm=boundary[nz:nz+nr];gp=boundary[nz+nr:nz+2*nr];corners=boundary[-2:]
    solve_start=time.perf_counter();phi,solver=poisson(q,h,r,gR,gm,gp)
    solve_seconds=time.perf_counter()-solve_start
    reconstruction_start=time.perf_counter();u,jac=reconstruct(phi,h,r,gR,gm,gp,corners)
    reconstruction_seconds=time.perf_counter()-reconstruction_start
    oracle_start=time.perf_counter();exact_u,exact_jac=oracle(r,z)
    oracle_seconds=time.perf_counter()-oracle_start
    core=(rr<=4.)&(np.abs(zz)<=4.);all_cells=np.ones_like(core,dtype=bool)
    weight=2.*math.pi*rr*h*h
    metrics=dict(core_u_relative=relative_error(u,exact_u,weight,core),
        core_J_relative=relative_error(jac,exact_jac,weight,core),
        box_u_relative=relative_error(u,exact_u,weight,all_cells),
        box_J_relative=relative_error(jac,exact_jac,weight,all_cells))
    source_r_tail=(1.+.5*R*R)*math.exp(-.5*R*R)
    source_z_tail=math.erfc(R/math.sqrt(2.))
    raw=local/(name+'.npz');assert not raw.exists()
    np.savez(raw,r=r,z=z,q=q,phi=phi,u=u,J=jac,exact_u=exact_u,exact_J=exact_jac,
             boundary_r=tr,boundary_z=tz,boundary_phi=boundary)
    record=dict(name=name,R=R,Z=R,radial_cells=nr,axial_cells=nz,h=h,
        boundary_orders=list(orders),boundary_target_count=len(tr),
        scalar_boundary_kernel_pairs=len(tr)*math.prod(orders),
        solver=solver,metrics=metrics,source_5D_mass_omission_fraction=source_r_tail+source_z_tail-source_r_tail*source_z_tail,
        boundary_seconds=boundary_seconds,linear_solve_seconds=solve_seconds,
        reconstruction_seconds=reconstruction_seconds,oracle_seconds=oracle_seconds,
        raw=dict(path=raw.name,**identity(raw)),case_elapsed_before_record_write_seconds=time.perf_counter()-begin)
    with (local/(name+'.json')).open('x',encoding='utf8') as stream:json.dump(record,stream,indent=2)
    print(json.dumps(dict(case=name,metrics=metrics,solver=solver)),flush=True)
    core_fields=dict(u=u[:,core],J=jac[:,core],exact_u=exact_u[:,core],exact_J=exact_jac[:,core],
                     weight=weight[core],r=rr[core],z=zz[core])
    return record,core_fields


def compare_core(base,other,key):
    assert np.array_equal(base['r'],other['r']) and np.array_equal(base['z'],other['z'])
    difference=other[key]-base[key];exact=base['exact_'+key]
    return math.sqrt(float(np.sum(np.sum(difference*difference,axis=0)*base['weight']))/
                     float(np.sum(np.sum(exact*exact,axis=0)*base['weight'])))


def main():
    root=Path(__file__).resolve().parent;local=root/'local';out=root/'result.json'
    assert not out.exists();records=[];fields={}
    for name,R,nr,orders in CASES:
        record,core=solve_case(name,R,nr,orders,local);records.append(record);fields[name]=core
    metrics={x['name']:x['metrics'] for x in records}
    boundary_diff={key:compare_core(fields['S64'],fields['Q64'],key) for key in ('u','J')}
    domain_diff={key:compare_core(fields['S64'],fields['D96'],key) for key in ('u','J')}
    ratios={key:[metrics[a][key]/metrics[b][key] for a,b in [('S32','S64'),('S64','S128')]]
            for key in ('core_u_relative','core_J_relative')}
    checks=dict(all_linear_solves=all(x['solver']['true_weighted_relative_residual']<=1e-10 for x in records),
        fine_u=metrics['S128']['core_u_relative']<=.005,fine_J=metrics['S128']['core_J_relative']<=.005,
        spatial_reductions=all(value>=1.5 for values in ratios.values() for value in values),
        boundary_u=boundary_diff['u']<=1e-4,boundary_J=boundary_diff['J']<=1e-4,
        domain_u=domain_diff['u']<=1e-3,domain_J=domain_diff['J']<=1e-3)
    tailr=(1.+16.)*math.exp(-16.);tailz=math.erfc(4.)
    result=dict(schema='t55-initial-axisymmetric-reference-v1',
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        status='qualified_initial_only' if all(checks.values()) else 'failed_checks',
        python=platform.python_version(),numpy=np.__version__,executable=sys.executable,
        code=identity(Path(__file__)),cases=records,spatial_error_reduction_factors=ratios,
        boundary_disagreements=boundary_diff,domain_disagreements=domain_diff,checks=checks,
        initial_vorticity_squared_norm_core_omission_fraction=tailr+tailz-tailr*tailz,
        fluid_trajectories=0,physical_task_pass=None,formal_error_certificate=False,
        child_elapsed_before_result_write_seconds=time.perf_counter()-START)
    with out.open('x',encoding='utf8',newline='\n') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=result['status'],checks=checks)),flush=True)
    return 0 if all(checks.values()) else 2


if __name__=='__main__':raise SystemExit(main())
