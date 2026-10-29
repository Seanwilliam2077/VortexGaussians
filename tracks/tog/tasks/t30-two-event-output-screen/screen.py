"""One fixed rational necessary-condition screen; no candidate RGB evaluation."""
import argparse
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import time
import traceback

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
PARENT='6b081c60fded8ce9618326e7b6f5a35dfe41f642'
INPUT='tracks/tog/tasks/t17-order-inversion-bound/inputs.json'
REF='tracks/tog/tasks/t18-reference-robustness/run-01/results.json'
OLD='tracks/tog/tasks/t21-winner-prefix-bound/run-01/results.json'
PINS={INPUT:'5cccf0238c679e14bc50e67d2d24726a58295b484b1d3464bf77d4eca0491cb7',REF:'fa4fb6887c6b38e800f18e919634821b3ee51c2fb0122cd0dbb4047eead7873d',OLD:'94d3ad607ba70ee6d7192643e6ad39ec3802f2a269b12df8cbfe87e59917bf83'}
EPS=(0.001,0.01)
def require(ok,message):
    if not ok: raise ValueError(message)
def read(p): return json.loads(p.read_bytes())
def identity(p):
    b=p.read_bytes()
    return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def identities(freeze):
    expected=set(PINS)|{(HERE/name).relative_to(ROOT).as_posix() for name in ('PROTOCOL.md','DERIVATION.md','screen.py','supervise.py')}|{'tracks/validation/t30-pre-execution-review.md'}
    require(freeze['parent_commit']==PARENT,'Frozen parent differs')
    require(len(freeze['artifacts'])==8,'Eight distinct frozen artifacts required')
    found={}
    for x in freeze['artifacts']:
        require(x['path'] not in found,'Duplicate frozen artifact')
        p=(ROOT/x['path']).resolve()
        require(p.is_relative_to(ROOT),'Freeze path escapes repository')
        found[x['path']]=identity(p)
        require(found[x['path']]=={k:x[k] for k in ('bytes','sha256')},'Frozen identity differs: '+x['path'])
    for p,h in PINS.items(): require(found[p]['sha256']==h,'Pinned source differs')
    require(set(found)==expected,'Required frozen artifact set differs')
    return found
def pack(x): return {'numerator':str(x.numerator),'denominator':str(x.denominator),'approx':float(x)}
def finite(values,lo=None,hi=None):
    for x in values:
        require(isinstance(x,(float,int)) and math.isfinite(x),'Non-finite scalar')
        require(lo is None or x>=lo,'Scalar below domain')
        require(hi is None or x<=hi,'Scalar above domain')
def structure(f,s,old):
    require(s['fixture']==f and old['id']==f['id'],'Fixture mismatch')
    require(old['n']==f['n'] and old['group']==f['group'],'Metadata mismatch')
    n=f['n']
    require(len(s['clipped_optical_masses'])==len(f['color'])==n,'Shape mismatch')
    finite(s['clipped_optical_masses'],0)
    for row in f['color']:
        require(len(row)==3,'RGB shape')
        finite(row,0,1)
    require(s['clipped_optical_masses']==old['clipped_optical_masses'],'Mass disagreement')
    require(s['ordered_rgb']==old['ordered_rgb'] and s['G_rgb']==old['G_rgb'],'Saved values differ')
    require(s['gates']['passed'] and s['gates']['all_finite'] and s['gates']['reference_global_budget_pass'] and not s['gates']['failures'] and old['checks']['qualified'],'Missing inherited qualification')
    for e in EPS:
        entry=old['per_epsilon'][str(e)]
        require(entry['eligible_noncontrol_n_ge_4']==(f['group']!='control' and n>=4),'Eligibility differs')
        require(entry['common_unsolved']==(entry['eligible_noncontrol_n_ge_4'] and entry['common_path'] is None),'Common exclusion differs')
        for cap in ('simple','jensen'):
            require(entry['caps'][cap]['new_accept']==(max(old['caps'][cap]['combined']['E_rgb'])<=e),'T21 acceptance mismatch')

def floor_enclosure(masses,colors):
    """Only stored masses and original colors enter; no ids, eps or references."""
    tau=sum((F(x) for x in masses),F(0))
    ranges=[max((F(c[h]) for c in colors),default=F(0))-min((F(c[h]) for c in colors),default=F(0)) for h in range(3)]
    d=max(ranges)
    t=min(tau,F(1))
    term=F(1); series=F(1); s12=None
    for k in range(1,14):
        term=term*(-t)/k
        series+=term
        if k==12: s12=series
    s13=series
    polynomial=1+t+t*t/2
    lo=max(F(0),1-polynomial*s12)
    hi=min(F(1),1-polynomial*s13) if tau<=1 else F(1)
    require(0<=s13<=s12<=1,'Taylor enclosure ordering')
    require(0<=lo<=hi<=1,'Tail enclosure ordering')
    lower=lo*d/2; upper=hi*d/2
    require(0<=lower<=upper,'Radius ordering')
    return {'tau':pack(tau),'range_rgb':[pack(x) for x in ranges],'max_range':pack(d),'t':pack(t),'S12':pack(s12),'S13':pack(s13),'tail_lower':pack(lo),'tail_upper':pack(hi),'floor_lower':pack(lower),'floor_upper':pack(upper),'clamped_tau_to_one':tau>1,'term_recurrences':13},lower,upper

def run(out):
    start=time.perf_counter(); deadline=start+30
    out=Path(out).resolve(); out.mkdir(parents=True,exist_ok=False)
    record={'schema':'t30-two-event-necessary-screen-v1','parent_commit':PARENT,'qualified':False,'failures':[],'cases':[],'epsilons':{str(e):pack(F(e)) for e in EPS},'candidate_outputs_evaluated':0,'pair_moments_evaluated':0,'new_CDF_exp_integrand_quadrature_evaluations':0,'source_calls':0,'formal_underlying_Gaussian_certificate':False,'stored_binary64_inputs_interpreted_as_exact_rationals':True,'novelty_speed_or_TOG_claim':False}
    journal=(out/'journal.jsonl').open('x',encoding='utf-8',newline='\n')
    try:
        freeze=read(HERE/'freeze.json')
        record['freeze_before']=identity(HERE/'freeze.json')
        record['identities_before']=identities(freeze)
        inp,refs,old=read(ROOT/INPUT),read(ROOT/REF),read(ROOT/OLD)
        require(inp['fixture_count']==len(inp['fixtures'])==len(refs['cases'])==len(old['cases'])==48,'Original case count')
        require(refs['summary']['all_48_numerically_qualified'] and old['qualified'],'Source qualification')
        require(sum(f['n'] for f in inp['fixtures'])==399,'Label count')
        for f,s,before in zip(inp['fixtures'],refs['cases'],old['cases']): structure(f,s,before)
        for f,s,before in zip(inp['fixtures'],refs['cases'],old['cases']):
            require(time.perf_counter()<deadline,'Worker deadline')
            values,lo,hi=floor_enclosure(s['clipped_optical_masses'],f['color'])
            per={}
            for e in EPS:
                prior=before['per_epsilon'][str(e)]
                excluded=lo>F(e)
                per[str(e)]={'common_unsolved':prior['common_unsolved'],'common_path':prior['common_path'],'T21_accept':{cap:prior['caps'][cap]['new_accept'] for cap in ('simple','jensen')},'strictly_excluded_by_tail_floor':excluded,'floor_upper_at_most_epsilon':hi<=F(e),'necessary_filter_survivor':not excluded,'primary_unresolved_survivor':prior['common_unsolved'] and not prior['caps']['jensen']['new_accept'] and not excluded}
            c={'id':f['id'],'group':f['group'],'n':f['n'],'exact_arithmetic':values,'per_epsilon':per}
            record['cases'].append(c)
            json.dump(c,journal,ensure_ascii=False,allow_nan=False);journal.write('\n');journal.flush()
        summary={}
        for e in EPS:
            key=str(e); pop=[c for c in record['cases'] if c['per_epsilon'][key]['common_unsolved']]
            require(len(pop)==28,'Historical population changed')
            accepted={cap:[c['id'] for c in pop if c['per_epsilon'][key]['T21_accept'][cap]] for cap in ('simple','jensen')}
            require(all(len(v)==(1 if e==.001 else 4) for v in accepted.values()),'Historical acceptance count')
            summary[key]={'population':[c['id'] for c in pop],'T21_accepted':accepted,'tail_excluded':[c['id'] for c in pop if c['per_epsilon'][key]['strictly_excluded_by_tail_floor']],'primary_unresolved_survivors':[c['id'] for c in pop if c['per_epsilon'][key]['primary_unresolved_survivor']]}
        record['summary']=summary
        survivors=sorted(set().union(*(set(summary[str(e)]['primary_unresolved_survivors']) for e in EPS)))
        record['distinct_primary_unresolved_survivors']=survivors
        record['decision']='retain_unresolved_necessary_feasibility_only' if survivors else 'close_whole_interval_two_event_certificate_on_fixed_scope'
        record['automatic_next_run_queued']=False
        record['counters']={'cases':48,'labels':399,'fixed_taylor_term_recurrences':sum(c['exact_arithmetic']['term_recurrences'] for c in record['cases']),'exact_epsilon_classifications':96,'candidate_outputs':0,'pair_moment_evaluations':0}
        require(record['counters']['fixed_taylor_term_recurrences']==624,'Recurrence count')
        record['identities_after']=identities(freeze)
        record['freeze_after']=identity(HERE/'freeze.json')
        require(record['identities_before']==record['identities_after'] and record['freeze_before']==record['freeze_after'],'Frozen files changed during screen')
        record['qualified']=True
    except Exception as exc:
        record['failures'].append({'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()})
        record['decision']='unqualified_no_retry'
    finally:
        journal.close()
        record['worker_seconds_before_serialization']=time.perf_counter()-start
        (out/'results.json').write_text(json.dumps(record,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'qualified':record['qualified'],'cases':len(record['cases']),'decision':record['decision'],'failures':record['failures']}))
    return 0 if record['qualified'] else 2

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--out')
    args=parser.parse_args()
    if not args.execute: print('Plan only: one frozen 48-case rational necessary-condition screen; no candidate output.')
    else:
        require(args.out is not None,'A fresh output path is required')
        raise SystemExit(run(args.out))
