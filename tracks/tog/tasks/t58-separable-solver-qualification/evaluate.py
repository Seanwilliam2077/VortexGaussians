"""One fixed qualification; saved states and one known discrete solution, no flow."""
import datetime
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import sys
import time

START=time.perf_counter();ROOT=Path(__file__).resolve().parent;OLD=ROOT.parent/'t56-coupled-reference'
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
solver=module('t58_solver',ROOT/'solver.py');np=solver.np
spatial=module('t55_reconstruction_only',ROOT.parent/'t55-axisymmetric-reference'/'reference.py')

def identity(path):
    raw=path.read_bytes();return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def write(path,value):
    with path.open('x',encoding='utf8',newline='\n') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')

def stencil(phi,h):
    # Independent original flux/ghost stencil; no transform or Thomas coefficients used.
    nr,nz=phi.shape;faces=np.arange(nr+1)*h
    weight=(faces[1:]**4-faces[:-1]**4)/4.
    lower=np.concatenate((phi[:1],phi[:-1]),axis=0)
    upper=np.concatenate((phi[1:],-phi[-1:]),axis=0)
    radial=(faces[1:,None]**3*(phi-upper)+faces[:-1,None]**3*(phi-lower))/(weight[:,None]*h)
    bottom=np.concatenate((-phi[:,:1],phi[:,:-1]),axis=1)
    top=np.concatenate((phi[:,1:],-phi[:,-1:]),axis=1)
    return radial+(2.*phi-bottom-top)/h**2

def original_rhs(q,h,gR,gm,gp):
    nr=q.shape[0];R=nr*h;last_volume=(R**4-(R-h)**4)/4.
    b=q.copy();b[-1]+=2.*R**3/(last_volume*h)*gR
    b[:,0]+=2.*gm/h**2;b[:,-1]+=2.*gp/h**2
    return b

def weighted_relative(a,b,h):
    faces=np.arange(b.shape[0]+1)*h;w=(faces[1:]**4-faces[:-1]**4)/4.
    den=float(np.sum(w[:,None]*b**2));assert den>0.
    return math.sqrt(float(np.sum(w[:,None]*(a-b)**2))/den)

def original_residual(phi,b,h):return weighted_relative(stencil(phi,h),b,h)

def transform_checks():
    results=[]
    for n in (64,128,192,256,512):
        tick=time.perf_counter();j=np.arange(n)
        modes=np.stack([np.sin(np.pi*k*(j+.5)/n) if k!=n else (-1.)**j for k in (1,7,n)])
        dense=.3+np.cos(.37*(j+1.))+np.sin(.13*(j+1.)**2)
        vectors=np.concatenate((modes,dense[None,:]))
        coeff=solver.forward_sine(vectors);back=solver.inverse_sine(coeff)
        roundtrip=np.linalg.norm(back-vectors,axis=1)/np.linalg.norm(vectors,axis=1)
        expected=np.zeros((3,n))
        for row,k in enumerate((1,7,n)):expected[row,k-1]=n if k==n else n/2.
        forward_errors=np.linalg.norm(coeff[:3]-expected,axis=1)/np.linalg.norm(expected,axis=1)
        eigen=[]
        for row,k in enumerate((1,7,n)):
            v=modes[row];lam=4.*math.sin(math.pi*k/(2.*n))**2
            # h=1; dimensionless operator independent of the implementation's factors.
            applied=2.*v-np.concatenate(([-v[0]],v[:-1]))-np.concatenate((v[1:],[-v[-1]]))
            residual=float(np.linalg.norm(applied-lam*v));norm=float(np.linalg.norm(v))
            eigen.append(dict(k=k,operator_normalized_residual=residual/(4.*norm),
                              eigenvalue_relative_residual=residual/(lam*norm)))
        rec=dict(n=n,roundtrip_relative=roundtrip.tolist(),forward_mode_relative=forward_errors.tolist(),
            eigenmodes=eigen,seconds=time.perf_counter()-tick,
            passed=bool(max(roundtrip)<=1e-12 and max(forward_errors)<=1e-12 and
                max(x['operator_normalized_residual'] for x in eigen)<=1e-11))
        results.append(rec)
    write(ROOT/'local/transform-checks.json',results);return results

def fixture(name,index):
    tick=time.perf_counter();case=json.loads((OLD/'local'/(name+'.json')).read_bytes())
    raw=OLD/'local'/case['raw']['path'];assert identity(raw)=={k:case['raw'][k] for k in ('bytes','sha256')}
    nr,nz,h=case['radial_cells'],case['axial_cells'],case['h']
    with np.load(raw,allow_pickle=False) as arr:
        q=arr['q'][index];oldphi=arr['phi'][index];boundary=arr['boundary'][index]
        saved_u=arr['u'][index];saved_J0=arr['J0'] if index==0 else None;r=arr['r'];z=arr['z']
    assert q.shape==oldphi.shape==(nr,nz) and len(boundary)==nz+2*nr+2
    assert np.array_equal(r,(np.arange(nr)+.5)*h) and np.array_equal(z,-case['R']+(np.arange(nz)+.5)*h)
    gR=boundary[:nz];gm=boundary[nz:nz+nr];gp=boundary[nz+nr:nz+2*nr];corners=boundary[-2:]
    load_seconds=time.perf_counter()-tick
    phi,record=solver.solve(q,h,gR,gm,gp)
    check_start=time.perf_counter();b=original_rhs(q,h,gR,gm,gp)
    residual=original_residual(phi,b,h);old_residual=original_residual(oldphi,b,h)
    phi_error=weighted_relative(phi,oldphi,h)
    u,J=spatial.reconstruct(phi,h,r,gR,gm,gp,corners)
    old_u,old_J=spatial.reconstruct(oldphi,h,r,gR,gm,gp,corners)
    assert np.array_equal(old_u,saved_u)
    if index==0:assert np.array_equal(old_J,saved_J0)
    rr,zz=np.meshgrid(r,z,indexing='ij');core=(rr<=4.)&(np.abs(zz)<=4.);weight=2.*math.pi*rr*h*h
    eu=spatial.relative_error(u,old_u,weight,core);ej=spatial.relative_error(J,old_J,weight,core)
    rec=dict(name=name,index=index,time=case['snapshots'][index]['time'],shape=[nr,nz],h=h,
        old_case=identity(OLD/'local'/(name+'.json')),old_raw=identity(raw),
        solver=record,load_seconds=load_seconds,validation_seconds=time.perf_counter()-check_start,
        true_weighted_relative_residual=residual,old_CG_true_weighted_relative_residual=old_residual,
        phi_relative=phi_error,u_core_relative=eu,J_core_relative=ej,
        saved_u_exactly_reconstructed=True,saved_initial_J_exactly_reconstructed=(True if index==0 else None),
        passed=bool(residual<=1e-10 and phi_error<=1e-8 and eu<=1e-7 and ej<=1e-7))
    raw_out=ROOT/'local'/f'{name}-{index}.npz';assert not raw_out.exists()
    np.savez(raw_out,phi=phi,u=u,J=J)
    rec['raw']=dict(path=raw_out.name,**identity(raw_out));rec['fixture_elapsed_before_record_seconds']=time.perf_counter()-tick
    write(ROOT/'local'/f'{name}-{index}.json',rec);print(json.dumps(dict(fixture=f'{name}-{index}',passed=rec['passed'])),flush=True)
    return rec

def manufactured():
    tick=time.perf_counter();nr,nz,R=256,512,8.;h=R/nr;r=(np.arange(nr)+.5)*h;j=np.arange(nz)
    radial=1.+(r/R)**2
    axial=np.sin(np.pi*(j+.5)/nz)+.2*np.sin(7.*np.pi*(j+.5)/nz)+.03*(-1.)**j
    known=radial[:,None]*axial[None,:];b=stencil(known,h)
    phi,record=solver.solve(b,h,np.zeros(nz),np.zeros(nr),np.zeros(nr))
    check_start=time.perf_counter();residual=original_residual(phi,b,h);error=weighted_relative(phi,known,h)
    rec=dict(shape=[nr,nz],R=R,h=h,signed_linear_fixture_not_fluid=True,solver=record,
        true_weighted_relative_residual=residual,known_phi_relative=error,
        validation_seconds=time.perf_counter()-check_start,passed=bool(residual<=1e-10 and error<=1e-8))
    raw=ROOT/'local/manufactured.npz';assert not raw.exists();np.savez(raw,known_phi=known,b=b,phi=phi)
    rec['raw']=dict(path=raw.name,**identity(raw));rec['fixture_elapsed_before_record_seconds']=time.perf_counter()-tick
    write(ROOT/'local/manufactured.json',rec);return rec

def main():
    assert platform.python_version()=='3.12.14' and np.__version__=='2.3.5'
    transforms=transform_checks();cases=[]
    for name in ('S32','S64','S128','T64','D96','Q64'):
        for index in (0,1,2):cases.append(fixture(name,index))
    known=manufactured()
    checks=dict(transforms=all(x['passed'] for x in transforms),
        original_residual=all(x['true_weighted_relative_residual']<=1e-10 for x in cases),
        saved_phi_agreement=all(x['phi_relative']<=1e-8 for x in cases),
        saved_u_agreement=all(x['u_core_relative']<=1e-7 for x in cases),
        saved_J_agreement=all(x['J_core_relative']<=1e-7 for x in cases),manufactured=known['passed'])
    result=dict(schema='t58-separable-qualification-v1',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        status='qualified_same_operator_fixtures_only' if all(checks.values()) else 'failed_checks',
        python=platform.python_version(),numpy=np.__version__,executable=sys.executable,
        evaluator=identity(Path(__file__)),solver_code=identity(ROOT/'solver.py'),spatial_code=identity(Path(spatial.__file__)),
        transforms=transforms,fixtures=cases,manufactured=known,checks=checks,
        completed_saved_state_solves=len(cases),completed_manufactured_solves=1,
        new_fluid_trajectories=0,new_Green_matrices=0,new_CG_solves=0,candidate_trajectories=0,
        coupled_reference_qualified=False,full_t1_task_pass=None,formal_error_certificate=False,
        child_elapsed_before_result_write_seconds=time.perf_counter()-START)
    write(ROOT/'result.json',result);print(json.dumps(dict(status=result['status'],checks=checks)),flush=True)
    return 0 if all(checks.values()) else 2

if __name__=='__main__':raise SystemExit(main())
