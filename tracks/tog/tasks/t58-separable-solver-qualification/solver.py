"""Ordinary sine-transform/Thomas solution of the unchanged axisymmetric FV operator."""
import time
import numpy as np

def forward_sine(x):
    n=x.shape[-1]
    assert n>=2 and np.all(np.isfinite(x))
    extended=np.concatenate((x,-x[...,::-1]),axis=-1)
    spectrum=np.fft.rfft(extended,axis=-1)
    phase=np.exp(-1j*np.pi*np.arange(1,n+1)/(2.*n))
    return -.5*np.imag(spectrum[...,1:]*phase)

def inverse_sine(coefficients):
    n=coefficients.shape[-1]
    assert n>=2 and np.all(np.isfinite(coefficients))
    spectrum=np.zeros(coefficients.shape[:-1]+(n+1,),dtype=np.complex128)
    phase=np.exp(1j*np.pi*np.arange(1,n+1)/(2.*n))
    spectrum[...,1:]=-2j*phase*coefficients
    spectrum[...,-1]=2.*coefficients[...,-1]  # The single real Nyquist coefficient.
    return np.fft.irfft(spectrum,n=2*n,axis=-1)[...,:n]

def solve(q,h,gR,gminus,gplus):
    begin=time.perf_counter();nr,nz=q.shape
    assert nr>=2 and nz>=2 and h>0. and np.all(np.isfinite(q))
    assert gR.shape==(nz,) and gminus.shape==gplus.shape==(nr,)
    tick=time.perf_counter()
    faces=np.arange(nr+1)*h
    volumes=(faces[1:]**4-faces[:-1]**4)/4.
    left=faces[:-1]**3/(volumes*h);right=faces[1:]**3/(volumes*h)
    b=q.copy();b[-1]+=2.*right[-1]*gR
    b[:,0]+=2.*gminus/h**2;b[:,-1]+=2.*gplus/h**2
    rhs_seconds=time.perf_counter()-tick
    tick=time.perf_counter();transformed=forward_sine(b);forward_seconds=time.perf_counter()-tick
    tick=time.perf_counter()
    eigenvalues=4.*np.sin(np.pi*np.arange(1,nz+1)/(2.*nz))**2/h**2
    pivots=left[:,None]+right[:,None]+eigenvalues[None,:]
    pivots[-1]+=right[-1]
    multipliers=np.zeros_like(pivots)
    assert np.all(np.isfinite(pivots[0])) and np.min(pivots[0])>0.
    for i in range(1,nr):
        multipliers[i]=-left[i]/pivots[i-1]
        pivots[i]-=multipliers[i]*(-right[i-1])
        assert np.all(np.isfinite(pivots[i])) and np.min(pivots[i])>0.
    factor_seconds=time.perf_counter()-tick
    tick=time.perf_counter();work=transformed.copy()
    for i in range(1,nr):work[i]-=multipliers[i]*work[i-1]
    modes=np.empty_like(work);modes[-1]=work[-1]/pivots[-1]
    for i in range(nr-2,-1,-1):modes[i]=(work[i]+right[i]*modes[i+1])/pivots[i]
    triangular_seconds=time.perf_counter()-tick
    tick=time.perf_counter();phi=inverse_sine(modes);inverse_seconds=time.perf_counter()-tick
    assert np.all(np.isfinite(phi))
    return phi,dict(method='ordinary_FFT_sine_Thomas',shape=[nr,nz],factor_reuse=False,
        minimum_pivot=float(pivots.min()),minimum_eigenvalue=float(eigenvalues.min()),
        rhs_seconds=rhs_seconds,forward_transform_seconds=forward_seconds,factor_seconds=factor_seconds,
        triangular_seconds=triangular_seconds,inverse_transform_seconds=inverse_seconds,
        solver_seconds=time.perf_counter()-begin)
