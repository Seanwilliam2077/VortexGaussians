"""Fixed short ordinary axisymmetric FV/Green/MUSCL/SSPRK2 qualification."""
import datetime
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import sys
import time

START=time.perf_counter()
import numpy as np

ROOT=Path(__file__).resolve().parent
PREVIOUS=ROOT.parent/'t55-axisymmetric-reference'/'reference.py'
spec=importlib.util.spec_from_file_location('t55_spatial',PREVIOUS)
spatial=importlib.util.module_from_spec(spec);spec.loader.exec_module(spatial)
CASES=[('S32',8.,32,.0025,32),('S64',8.,64,.0025,32),('S128',8.,128,.0025,32),
       ('T64',8.,64,.00125,32),('D96',12.,96,.0025,32),('Q64',8.,64,.0025,64)]
SHAPE_NORM=math.sqrt(1.+((4.-math.pi)/2.)**2)

def identity(path):
    b=path.read_bytes();return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())

def write_json(path,value):
    with path.open('x',encoding='utf8',newline='\n') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')

def geometry(R,nr):
    h=R/nr;nz=2*nr;rf=np.arange(nr+1)*h;zf=-R+np.arange(nz+1)*h
    r=(rf[:-1]+rf[1:])/2.;z=(zf[:-1]+zf[1:])/2.
    area=(rf[1:]**2-rf[:-1]**2)/2.
    rc=(rf[1:]**3-rf[:-1]**3)/(3.*area)
    return dict(R=R,nr=nr,nz=nz,h=h,r=r,z=z,rc=rc,rf=rf,zf=zf,V=area[:,None]*h,
                W=(rf[1:]**4-rf[:-1]**4)/4.)

def initial(g):
    rf=g['rf'];zf=g['zf'];area=g['V'][:,0]/g['h']
    radial=np.exp(-.5*rf[:-1]**2)*(-np.expm1(-.5*(rf[1:]**2-rf[:-1]**2)))/area
    axial=[]
    for lo,hi in zip(zf[:-1],zf[1:]):
        if hi<=0.:lo,hi=-hi,-lo
        if lo>=0.:
            value=math.sqrt(math.pi/2.)*(math.erfc(lo/math.sqrt(2.))-math.erfc(hi/math.sqrt(2.)))
        else:
            value=math.sqrt(math.pi/2.)*(math.erf(hi/math.sqrt(2.))-math.erf(lo/math.sqrt(2.)))
        axial.append(value/g['h'])
    q=1.5*radial[:,None]*np.array(axial)[None,:]
    assert np.all(np.isfinite(q)) and np.min(q)>=0.
    return q

def minmod(a,b):
    return np.where(a*b>0.,np.sign(a)*np.minimum(np.abs(a),np.abs(b)),0.)

def slopes(q,g):
    h=g['h'];rc=g['rc'];R=g['R']
    left=np.concatenate((q[:1],q[:-1]),axis=0)
    right=np.concatenate((q[1:],np.zeros_like(q[:1])),axis=0)
    outside=(2./3.)*((R+h)**3-R**3)/((R+h)**2-R**2)
    lc=np.concatenate(([-rc[0]],rc[:-1]));rr=np.concatenate((rc[1:],[outside]))
    sr=minmod((q-left)/(rc-lc)[:,None],(right-q)/(rr-rc)[:,None])
    bottom=np.concatenate((np.zeros_like(q[:,:1]),q[:,:-1]),axis=1)
    top=np.concatenate((q[:,1:],np.zeros_like(q[:,:1])),axis=1)
    sz=minmod((q-bottom)/h,(top-q)/h)
    extent=np.maximum(rc-g['rf'][:-1],g['rf'][1:]-rc)[:,None]
    dev=np.abs(sr)*extent+np.abs(sz)*h/2.
    theta=np.ones_like(q)
    np.divide((1.-64.*np.finfo(float).eps)*q,dev,out=theta,where=dev>0.)
    theta=np.minimum(1.,theta);sr*=theta;sz*=theta
    return sr,sz

def kernel(g,order):
    begin=time.perf_counter();r,z,R=g['r'],g['z'],g['R'];nr,nz=g['nr'],g['nz']
    tr=np.concatenate((np.full(nz,R),r,r,[R,R]))
    tz=np.concatenate((z,np.full(nr,-R),np.full(nr,R),[-R,R]))
    sr,sz=np.meshgrid(r,z,indexing='ij');sr=sr.ravel()[None,:];sz=sz.ravel()[None,:]
    mass=np.broadcast_to(g['W'][:,None]*g['h'],(nr,nz)).ravel()[None,:]
    angle,weight=spatial.gauss(order,0.,math.pi)
    mat=np.empty((len(tr),nr*nz))
    for start in range(0,len(tr),8):
        targetr=tr[start:start+8,None];targetz=tz[start:start+8,None]
        base=targetr**2+sr**2+(targetz-sz)**2;cross=2.*targetr*sr
        acc=np.zeros_like(base)
        for a,w in zip(angle,weight):
            den=base-cross*math.cos(float(a));assert np.all(den>0.)
            acc+=float(w)*math.sin(float(a))**2*den**(-1.5)
        mat[start:start+8]=acc*mass/(2.*math.pi)
    assert np.all(np.isfinite(mat))
    return mat,tr,tz,dict(build_seconds=time.perf_counter()-begin,shape=list(mat.shape),
        bytes=int(mat.nbytes),angular_order=order,scalar_kernel_pairs=len(tr)*nr*nz*order)

def current(q,g,mat):
    begin=time.perf_counter();nr,nz,h=g['nr'],g['nz'],g['h']
    tick=time.perf_counter();boundary=np.einsum('ij,j->i',mat,q.ravel(),optimize=False)
    boundary_seconds=time.perf_counter()-tick
    gr=boundary[:nz];gm=boundary[nz:nz+nr];gp=boundary[nz+nr:nz+2*nr];corners=boundary[-2:]
    tick=time.perf_counter();phi,solver=spatial.poisson(q,h,g['r'],gr,gm,gp)
    solve_seconds=time.perf_counter()-tick
    tick=time.perf_counter();u,J=spatial.reconstruct(phi,h,g['r'],gr,gm,gp,corners)
    pv=np.zeros((nr+1,nz+1))
    pv[1:-1,1:-1]=(phi[:-1,:-1]+phi[1:,:-1]+phi[:-1,1:]+phi[1:,1:])/4.
    pv[-1,1:-1]=(gr[:-1]+gr[1:])/2.
    pv[1:-1,0]=(gm[:-1]+gm[1:])/2.;pv[1:-1,-1]=(gp[:-1]+gp[1:])/2.
    pv[-1,0],pv[-1,-1]=corners
    psi=g['rf'][:,None]**2*pv
    fr=-np.diff(psi,axis=1);fz=np.diff(psi,axis=0)
    divergence=(np.diff(fr,axis=0)+np.diff(fz,axis=1))/g['V']
    maxdiv=float(np.max(np.abs(divergence)))
    assert np.all(fr[0]==0.) and maxdiv<=1e-10
    record=dict(boundary_seconds=boundary_seconds,linear_solve_seconds=solve_seconds,
        reconstruction_seconds=time.perf_counter()-tick,solver=solver,
        max_volume_divergence=maxdiv,current_seconds=time.perf_counter()-begin)
    return dict(phi=phi,u=u,J=J,boundary=boundary,fr=fr,fz=fz,record=record)

def rhs(q,g,flow,dt):
    begin=time.perf_counter();sr,sz=slopes(q,g);rc=g['rc'][:,None]
    qleft=q+sr*(g['rf'][:-1,None]-rc);qright=q+sr*(g['rf'][1:,None]-rc)
    qbottom=q-sz*g['h']/2.;qtop=q+sz*g['h']/2.
    for face in (qleft,qright,qbottom,qtop):
        assert np.all(np.isfinite(face)) and np.min(face)>=0.
        assert np.all(face<=2.*q*(1.+1e-12)+1e-300)
    fr,fz=flow['fr'],flow['fz']
    outward=np.maximum(fr[1:],0.)+np.maximum(-fr[:-1],0.)
    outward+=np.maximum(fz[:,1:],0.)+np.maximum(-fz[:,:-1],0.)
    cfl=float(np.max(dt*outward/g['V']));assert cfl<=.5
    gr=np.zeros_like(fr);gz=np.zeros_like(fz)
    gr[1:-1]=fr[1:-1]*np.where(fr[1:-1]>=0.,qright[:-1],qleft[1:])
    gr[-1]=fr[-1]*np.where(fr[-1]>=0.,qright[-1],0.)
    gz[:,1:-1]=fz[:,1:-1]*np.where(fz[:,1:-1]>=0.,qtop[:,:-1],qbottom[:,1:])
    gz[:,0]=fz[:,0]*np.where(fz[:,0]>=0.,0.,qbottom[:,0])
    gz[:,-1]=fz[:,-1]*np.where(fz[:,-1]>=0.,qtop[:,-1],0.)
    out=float(np.sum(gr[-1]-gr[0])+np.sum(gz[:,-1]-gz[:,0]))
    derivative=-(np.diff(gr,axis=0)+np.diff(gz,axis=1))/g['V']
    return derivative,dict(outgoing_CFL=cfl,boundary_circulation_outflow=out,
                           transport_seconds=time.perf_counter()-begin,
                           minimum_face_q=min(float(np.min(v)) for v in (qleft,qright,qbottom,qtop)))

def velocity_slopes(u,g):
    h=g['h'];left=u[:,:1,:].copy();left[0]*=-1.
    radial=np.concatenate((left,u,u[:,-1:,:]),axis=1)
    radial[:,-1,:]=2.*u[:,-1,:]-u[:,-2,:]
    sr=(radial[:,2:]-radial[:,:-2])/(2.*h)
    axial=np.concatenate((2.*u[:,:,:1]-u[:,:,1:2],u,2.*u[:,:,-1:]-u[:,:,-2:-1]),axis=2)
    sz=(axial[:,:,2:]-axial[:,:,:-2])/(2.*h)
    return sr,sz

def statistics(q,qr,qz,g,gauss):
    h=g['h'];tot=np.zeros(9)
    for xr,wr in zip(*gauss[0]):
        rn=g['r'][:,None]+xr*h/2.
        for xz,wz in zip(*gauss[1]):
            zn=g['z'][None,:]+xz*h/2.
            value=q+qr*(rn-g['rc'][:,None])+qz*(zn-g['z'][None,:])
            assert np.min(value)>=0. and np.all(np.isfinite(value))
            w=wr*wz*h*h/4.*rn;density=w*value
            tot+=np.array([np.sum(density),np.sum(density*rn),np.sum(density*zn),
                np.sum(density*rn**2),np.sum(density*rn*zn),np.sum(density*zn**2),
                2.*math.pi*np.sum(w*value**2),math.pi*np.sum(density*rn**2),
                2.*math.pi*np.sum(w*rn**2*value**2)])
    gamma=tot[0];assert gamma>0.
    mean=tot[1:3]/gamma
    covariance=np.array([[tot[3],tot[4]],[tot[4],tot[5]]])/gamma-np.outer(mean,mean)
    shell=np.zeros_like(q,dtype=bool);shell[-2:,:]=True;shell[:,:2]=True;shell[:,-2:]=True
    return dict(circulation=float(gamma),centroid=mean.tolist(),covariance=covariance.tolist(),
        q_squared_integral=float(tot[6]),axial_impulse=float(tot[7]),vorticity_squared_integral=float(tot[8]),
        min_q=float(q.min()),max_q=float(q.max()),negative_cell_mass=float(np.sum(np.minimum(q,0.)*g['V'])),
        outer_two_cell_circulation_fraction=float(np.sum((q*g['V'])[shell])/gamma))

def analytic_initial(flow,g):
    exact_u,exact_J=spatial.oracle(g['r'],g['z'])
    rr,zz=np.meshgrid(g['r'],g['z'],indexing='ij');core=(rr<=4.)&(np.abs(zz)<=4.)
    weight=2.*math.pi*rr*g['h']**2
    return dict(u=spatial.relative_error(flow['u'],exact_u,weight,core),
                J=spatial.relative_error(flow['J'],exact_J,weight,core)),exact_u,exact_J

def solve_case(config,gauss):
    name,R,nr,dt,order=config;begin=time.perf_counter();g=geometry(R,nr)
    local=ROOT/'local';q=initial(g);mat,tr,tz,krecord=kernel(g,order)
    steps=int(round(.25/dt));assert math.isclose(steps*dt,.25)
    snapshots=[];stats=[];records=[];ledger=[];gamma0=float(np.sum(q*g['V']));expected=gamma0
    path=local/(name+'-steps.jsonl')
    def log(record):
        records.append(record);logstream.write(json.dumps(record,allow_nan=False)+'\n');logstream.flush()
    def snapshot(step):
        flow=current(q,g,mat);log(dict(kind='snapshot',step=step,**flow['record']))
        qr,qz=slopes(q,g);ur,uz=velocity_slopes(flow['u'],g)
        snapshots.append(dict(q=q.copy(),qr=qr,qz=qz,u=flow['u'],ur=ur,uz=uz,
                              phi=flow['phi'],boundary=flow['boundary']))
        stats.append(dict(step=step,time=step*dt,**statistics(q,qr,qz,g,gauss)))
        return flow
    with path.open('x',encoding='utf8',newline='\n') as logstream:
        flow0=snapshot(0);initial_error,exact_u,exact_J=analytic_initial(flow0,g)
        for step in range(steps):
            f0=current(q,g,mat);l0,a0=rhs(q,g,f0,dt)
            log(dict(kind='stage',step=step,stage=0,**f0['record'],**a0))
            q1=q+dt*l0;assert np.all(np.isfinite(q1)) and np.min(q1)>=0.
            f1=current(q1,g,mat);l1,a1=rhs(q1,g,f1,dt)
            log(dict(kind='stage',step=step,stage=1,**f1['record'],**a1))
            q2=q1+dt*l1;assert np.all(np.isfinite(q2)) and np.min(q2)>=0.
            q=.5*q+.5*q2;assert np.all(np.isfinite(q)) and np.min(q)>=0.
            expected-=dt/2.*(a0['boundary_circulation_outflow']+a1['boundary_circulation_outflow'])
            error=abs(float(np.sum(q*g['V']))-expected)/gamma0;ledger.append(error)
            log(dict(kind='step',step=step+1,minimum_q=float(q.min()),
                     minimum_Euler_stage_q=min(float(q1.min()),float(q2.min())),
                     circulation_ledger_relative=error))
            if step+1 in (steps//2,steps):snapshot(step+1)
            if (step+1)%25==0:print(json.dumps(dict(case=name,completed_steps=step+1,steps=steps)),flush=True)
    raw=local/(name+'.npz');assert not raw.exists()
    arrays={key:np.stack([s[key] for s in snapshots]) for key in snapshots[0]}
    np.savez(raw,**arrays,r=g['r'],rc=g['rc'],z=g['z'],J0=flow0['J'],exact_u0=exact_u,exact_J0=exact_J,
             boundary_r=tr,boundary_z=tz)
    solves=[x for x in records if x['kind'] in ('stage','snapshot')]
    stages=[x for x in records if x['kind']=='stage']
    record=dict(name=name,R=R,Z=R,radial_cells=nr,axial_cells=g['nz'],h=g['h'],dt=dt,steps=steps,
        angular_order=order,kernel=krecord,elliptic_solves=len(solves),transport_stages=len(stages),
        initial_analytic_errors=initial_error,snapshots=stats,
        max_CFL=max(x['outgoing_CFL'] for x in stages),
        max_volume_divergence=max(x['max_volume_divergence'] for x in solves),
        max_solver_true_residual=max(x['solver']['true_weighted_relative_residual'] for x in solves),
        total_CG_iterations=sum(x['solver']['iterations'] for x in solves),
        max_CG_iterations=max(x['solver']['iterations'] for x in solves),
        total_CG_restarts=sum(x['solver']['direction_restarts'] for x in solves),
        max_circulation_ledger_relative=max(ledger),
        minimum_Euler_stage_q=min(x['minimum_Euler_stage_q'] for x in records if x['kind']=='step'),
        q_squared_relative_drift=[abs(s['q_squared_integral']/stats[0]['q_squared_integral']-1.) for s in stats],
        impulse_relative_drift=[abs(s['axial_impulse']/stats[0]['axial_impulse']-1.) for s in stats],
        phase_seconds={key:sum(x.get(key,0.) for x in records) for key in
                       ('boundary_seconds','linear_solve_seconds','reconstruction_seconds','transport_seconds')},
        log=dict(path=path.name,**identity(path)),raw=dict(path=raw.name,**identity(raw)),
        case_elapsed_before_record_write_seconds=time.perf_counter()-begin)
    write_json(local/(name+'.json'),record)
    print(json.dumps(dict(case=name,completed=True,seconds=record['case_elapsed_before_record_write_seconds'])),flush=True)
    return record,dict(g=g,snapshots=snapshots)

def evaluate_saved(case,index,r,z,key):
    g=case['g'];s=case['snapshots'][index]
    ir=np.floor(r/g['h']).astype(int);iz=np.floor((z+g['R'])/g['h']).astype(int)
    def select(a):return a[...,ir[:,None],iz[None,:]]
    if key=='q':
        return select(s['q'])+select(s['qr'])*(r[:,None]-g['rc'][ir,None])+select(s['qz'])*(z[None,:]-g['z'][None,iz])
    return select(s['u'])+select(s['ur'])*(r[:,None]-g['r'][ir,None])+select(s['uz'])*(z[None,:]-g['z'][None,iz])

def compare(a,b,index,gauss):
    h=min(a['g']['h'],b['g']['h']);r=(np.arange(round(4./h))+.5)*h;z=-4.+(np.arange(round(8./h))+.5)*h
    sums=np.zeros(4)
    for xr,wr in zip(*gauss[0]):
        rn=r+xr*h/2.
        for xz,wz in zip(*gauss[1]):
            zn=z+xz*h/2.;qa=evaluate_saved(a,index,rn,zn,'q');qb=evaluate_saved(b,index,rn,zn,'q')
            ua=evaluate_saved(a,index,rn,zn,'u');ub=evaluate_saved(b,index,rn,zn,'u')
            w=2.*math.pi*rn[:,None]*h*h*wr*wz/4.
            sums+=np.array([np.sum(w*rn[:,None]**2*(qa-qb)**2),np.sum(w*rn[:,None]**2*qb**2),
                            np.sum(w*np.sum((ua-ub)**2,axis=0)),np.sum(w*np.sum(ub**2,axis=0))])
    return dict(vorticity_relative=math.sqrt(sums[0]/sums[1]),velocity_relative=math.sqrt(sums[2]/sums[3]))

def main():
    gauss=(np.polynomial.legendre.leggauss(3),np.polynomial.legendre.leggauss(2))
    records=[];fields={}
    for config in CASES:
        record,field=solve_case(config,gauss);records.append(record);fields[record['name']]=field
    byname={c['name']:c for c in records};comparisons=[];tick=time.perf_counter()
    for a,b,kind in [('S32','S64','space'),('S64','S128','space'),('S64','T64','time'),
                     ('S64','D96','domain'),('S64','Q64','angular')]:
        for index,t in enumerate((0.,.125,.25)):
            metrics=compare(fields[a],fields[b],index,gauss)
            sa=byname[a]['snapshots'][index];sb=byname[b]['snapshots'][index]
            metrics.update(axial_centroid_absolute=abs(sa['centroid'][1]-sb['centroid'][1]),
                covariance_relative=float(np.linalg.norm(np.array(sa['covariance'])-np.array(sb['covariance']))/SHAPE_NORM))
            comparisons.append(dict(a=a,b=b,kind=kind,time=t,**metrics))
    ratios=[]
    for index in (1,2):
        coarse=comparisons[index]['vorticity_relative'];fine=comparisons[3+index]['vorticity_relative']
        ratios.append(dict(time=(.125,.25)[index-1],coarse=coarse,fine=fine,
            ratio=coarse/fine if fine>0. else None,small_error_waiver=max(coarse,fine)<=1e-8,
            passed=max(coarse,fine)<=1e-8 or coarse>=1.5*fine))
    initial_checks={c['name']:max(c['initial_analytic_errors'].values())<=
                    (.02 if c['name']=='S32' else .005 if c['name']=='S128' else .01) for c in records}
    checks=dict(initial_analytic=all(initial_checks.values()),
        all_stage_invariants=all(c['max_CFL']<=.5 and c['max_volume_divergence']<=1e-10 and
            c['minimum_Euler_stage_q']>=0. and c['max_solver_true_residual']<=1e-10 for c in records),
        vorticity_disagreements=all(c['vorticity_relative']<=.01 for c in comparisons),
        velocity_disagreements=all(c['velocity_relative']<=(.02 if c['kind']=='space' else .01) for c in comparisons),
        centroid_disagreements=all(c['axial_centroid_absolute']<=.01 for c in comparisons),
        covariance_disagreements=all(c['covariance_relative']<=.01 for c in comparisons),
        spatial_reduction=all(c['passed'] for c in ratios),
        circulation_ledger=all(c['max_circulation_ledger_relative']<=1e-10 for c in records),
        q_squared_drift=all(max(c['q_squared_relative_drift'])<=.02 for c in records),
        axial_impulse_drift=all(max(c['impulse_relative_drift'])<=.01 for c in records))
    result=dict(schema='t56-coupled-reference-v1',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        status='qualified_short_reference_only' if all(checks.values()) else 'failed_checks',
        python=platform.python_version(),numpy=np.__version__,executable=sys.executable,
        code=identity(Path(__file__)),spatial_code=identity(PREVIOUS),cases=records,comparisons=comparisons,
        spatial_reductions=ratios,initial_checks=initial_checks,checks=checks,
        comparison_seconds=time.perf_counter()-tick,completed_trajectories=len(records),time_end=.25,
        candidate_trajectories=0,full_t1_task_pass=None,formal_error_certificate=False,
        child_elapsed_before_result_write_seconds=time.perf_counter()-START)
    write_json(ROOT/'result.json',result)
    print(json.dumps(dict(status=result['status'],checks=checks)),flush=True)
    return 0 if all(checks.values()) else 2

if __name__=='__main__':raise SystemExit(main())
