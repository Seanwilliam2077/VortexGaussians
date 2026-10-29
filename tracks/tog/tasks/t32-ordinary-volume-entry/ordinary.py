"""Ordinary HDR entry: existing GL kernel, explicit no-Simpson-fallback contract.

This wrapper supplies no oracle or fixture identifier to the solver. GL order
agreement is empirical; the separate reference enclosure qualifies its output.
"""
import importlib.util
import math
from pathlib import Path
import sys
import time


class OrdinaryFailure(RuntimeError):
    pass


def load_kernel(root):
    path=Path(root)/'tracks/tog/tasks/t22-prefix-complete-cost/integrators.py'
    spec=importlib.util.spec_from_file_location('t32_legacy_gl',path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module


def solve(prepared,nominal,counters,deadline_ns,cache,kernel):
    if time.perf_counter_ns()>=deadline_ns:
        raise TimeoutError('T32 ordinary deadline')
    n=len(prepared['mu'])
    if not (math.isfinite(nominal) and nominal>0 and
            math.isfinite(prepared['a']) and math.isfinite(prepared['b']) and prepared['a']<prepared['b']):
        raise OrdinaryFailure('Invalid domain/budget')
    if not all(len(prepared[k])==n for k in ['sd','weight','color','source_ids']):
        raise OrdinaryFailure('Mismatched parameter lengths')
    if prepared['background_term']!=[0,0,0]:
        raise OrdinaryFailure('This entry has only black background')
    for z,h,q,c in zip(prepared['mu'],prepared['sd'],prepared['weight'],prepared['color']):
        if not (all(math.isfinite(x) for x in [z,h,q,*c]) and h>0 and q>=0 and len(c)==3 and min(c)>=0):
            raise OrdinaryFailure('Invalid HDR Gaussian')
    masses=[q*kernel._normal_interval(prepared['a'],prepared['b'],z,h,counters)
            for z,h,q in zip(prepared['mu'],prepared['sd'],prepared['weight'])]
    tau=math.fsum(masses); alpha=-math.expm1(-tau)
    counters['ordinary_calls']=counters.get('ordinary_calls',0)+1
    if n==0 or tau==0:
        # tau==0 is a binary64 result, not a proof of real-arithmetic vacuum.
        # Qualification still compares against the full-field reference.
        counters['ordinary_zero_paths']=counters.get('ordinary_zero_paths',0)+1
        return dict(rgb=[0.,0.,0.],alpha=alpha,tau=tau,path='computed_zero_mass',nominal=nominal)
    lo=[min(c[k] for c in prepared['color']) for k in range(3)]
    hi=[max(c[k] for c in prepared['color']) for k in range(3)]
    radius=[alpha*(b-a)/2 for a,b in zip(lo,hi)]
    if max(radius)<=nominal:
        counters['ordinary_color_box_paths']=counters.get('ordinary_color_box_paths',0)+1
        return dict(rgb=[alpha*(a+b)/2 for a,b in zip(lo,hi)],alpha=alpha,tau=tau,
                    path='ordinary_color_box',nominal=nominal,real_arithmetic_radius=radius)
    local=dict(prepared,rule_cache=cache)
    points=kernel._breakpoints(local,counters)
    fun=kernel._Integrand(local,counters,deadline_ns,'gl')
    previous=None
    for degree in kernel.GL_ORDERS:
        kernel._check_deadline(deadline_ns)
        if degree not in cache:
            cache[degree]=kernel._gauss_legendre_rule(degree,counters,deadline_ns)
        else:
            counters['gl_rule_cache_hits']=counters.get('gl_rule_cache_hits',0)+1
        nodes,weights=cache[degree]
        emission=kernel._gl_emission(fun,points,nodes,weights)
        counters['gl_refinement_levels']=counters.get('gl_refinement_levels',0)+1
        if previous is not None:
            difference=[abs(a-b) for a,b in zip(emission,previous)]
            if max(difference)<=nominal:
                return dict(rgb=list(emission),alpha=alpha,tau=tau,path='gl_no_fallback',
                            gl_order=degree,nominal=nominal,empirical_difference=difference)
        previous=emission
    raise OrdinaryFailure('GL4/8/16/32/64 agreement exhausted; Simpson fallback prohibited')
