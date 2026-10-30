"""Bounded exact-rational weight construction for the frozen T67 contract.

No original physical moments or objective values are evaluated here. Exactness
concerns only supplied binary64 coefficients. No import-time numerical work.
"""
from fractions import Fraction
from functools import cmp_to_key
import math
import time


class GeometryUnresolved(Exception):
    pass


class Arithmetic:
    def __init__(self,deadline_ns):
        self.deadline_ns=deadline_ns
        self.counters=dict(rational_operations=0,fraction_additions=0,fraction_subtractions=0,
            fraction_multiplications=0,fraction_divisions=0,fraction_negations=0,
            fraction_conversions=0,fraction_float_conversions=0,rational_comparisons=0,polynomial_long_divisions=0,
            polynomial_division_requests=0,polynomial_evaluations=0,polynomial_derivatives=0,
            gcd_calls=0,sturm_chains_constructed=0,sturm_variation_evaluations=0,
            root_count_queries=0,isolation_nodes=0,max_depth=0,max_rational_bits=0,
            max_sturm_chain_length=0,distinct_roots=0,weight_attempts=0,
            unique_in_range_candidates=0,outside_weight_attempts=0,duplicate_weight_attempts=0,
            attempted_over_cap=0,max_attempted_rational_bits=0)

    def initialize(self):
        self.zero=self.convert(0); self.one=self.convert(1); self.two=self.convert(2)

    def tick(self):
        if self.deadline_ns is not None and time.perf_counter_ns()>=self.deadline_ns:
            raise TimeoutError('global scientific deadline inside weight solver')

    def unresolved(self,reason):
        self.counters['attempted_over_cap']+=1
        raise GeometryUnresolved(reason)

    def bounded(self,x):
        self.tick(); bits=max(abs(x.numerator).bit_length(),x.denominator.bit_length())
        self.counters['max_attempted_rational_bits']=max(self.counters['max_attempted_rational_bits'],bits)
        if bits>8192: self.unresolved('rational_bits_cap')
        self.counters['max_rational_bits']=max(self.counters['max_rational_bits'],bits)
        return x

    def convert(self,value):
        self.tick(); self.counters['fraction_conversions']+=1
        if isinstance(value,Fraction): return self.bounded(value)
        if isinstance(value,int): return self.bounded(Fraction(value))
        value=float(value)
        if not math.isfinite(value): raise GeometryUnresolved('nonfinite_supplied_coefficient')
        return self.bounded(Fraction.from_float(value))

    def operation(self,kind,a,b=None):
        self.tick(); self.counters['rational_operations']+=1
        self.counters['fraction_'+kind]+=1
        if kind=='additions': value=a+b
        elif kind=='subtractions': value=a-b
        elif kind=='multiplications': value=a*b
        elif kind=='divisions':
            if self.cmp(b,self.zero)==0: raise GeometryUnresolved('undefined_rational_division')
            value=a/b
        else: value=-a
        return self.bounded(value)

    def add(self,a,b): return self.operation('additions',a,b)
    def sub(self,a,b): return self.operation('subtractions',a,b)
    def mul(self,a,b): return self.operation('multiplications',a,b)
    def div(self,a,b): return self.operation('divisions',a,b)
    def neg(self,a): return self.operation('negations',a)

    def cmp(self,a,b):
        self.tick(); self.counters['rational_comparisons']+=1
        return (a>b)-(a<b)

    def midpoint(self,a,b): return self.div(self.add(a,b),self.two)

    def to_float(self,value):
        self.tick(); self.counters['fraction_float_conversions']+=1
        return float(value)


class Solver:
    def __init__(self,arithmetic):
        self.a=arithmetic; self.chain_cache={}; self.roots=[]; self.intervals=[]
        self.state=dict(status='inner_feasibility_unresolved',polynomial=None,axial_interval=None,
            roots=self.roots,intervals=self.intervals,stationary=None,attempts=[],candidates=[],coverage_groups=[],
            root_isolation_complete_for_rounded_polynomial=False,
            representable_candidate_construction_complete=False,rounded_feasible_set_empty=None,
            unresolved_reasons=[],counters=self.a.counters)

    def ensure(self,condition,reason):
        if not condition: raise GeometryUnresolved(reason)

    def trim(self,p):
        p=list(p)
        while p and self.a.cmp(p[-1],self.a.zero)==0: p.pop()
        return p

    def monic(self,p):
        p=self.trim(p)
        return [self.a.div(x,p[-1]) for x in p] if p else []

    def derivative(self,p):
        self.a.counters['polynomial_derivatives']+=1
        return self.trim([self.a.mul(p[i],self.a.convert(i)) for i in range(1,len(p))])

    def evaluate(self,p,x):
        self.a.counters['polynomial_evaluations']+=1; value=self.a.zero
        for coefficient in reversed(p): value=self.a.add(self.a.mul(value,x),coefficient)
        return value

    def divide(self,p,q):
        self.a.tick(); self.a.counters['polynomial_division_requests']+=1
        if self.a.counters['polynomial_long_divisions']>=24: self.a.unresolved('polynomial_long_divisions_cap')
        self.a.counters['polynomial_long_divisions']+=1
        p=self.trim(p); q=self.trim(q); self.ensure(bool(q),'zero_polynomial_divisor')
        if len(p)<len(q): return [],p
        quotient=[self.a.zero]*(len(p)-len(q)+1)
        while p and len(p)>=len(q):
            degree=len(p)-len(q); scale=self.a.div(p[-1],q[-1]); quotient[degree]=scale
            for j,value in enumerate(q): p[degree+j]=self.a.sub(p[degree+j],self.a.mul(scale,value))
            p=self.trim(p)
        return self.trim(quotient),p

    def exact_divide(self,p,q):
        quotient,remainder=self.divide(p,q)
        self.ensure(not remainder,'nonzero_exact_division_remainder'); return quotient

    def gcd(self,p,q):
        self.a.counters['gcd_calls']+=1; p=self.trim(p); q=self.trim(q)
        if len(p)<len(q): p,q=q,p
        while q:
            if len(q)==1: return [self.a.one]
            _,remainder=self.divide(p,q); p,q=q,remainder
        return self.monic(p)

    def square_free(self,p):
        common=self.gcd(p,self.derivative(p)); square_free=self.monic(self.exact_divide(p,common))
        w=square_free; c=common; multiplicity=1; factors=[]
        while len(w)>1:
            self.ensure(multiplicity<=4,'square_free_multiplicity_inconsistent')
            y=self.gcd(w,c); f=self.monic(self.exact_divide(w,y))
            if len(f)>1: factors.append((f,multiplicity))
            w=y; c=self.exact_divide(c,y); multiplicity+=1
        self.ensure(len(c)<=1 and sum((len(f)-1)*m for f,m in factors)==len(p)-1,'square_free_degree_inconsistent')
        self.state['polynomial'].update(gcd=common,square_free=square_free,
            square_free_factors=[dict(coefficients=f,multiplicity=m) for f,m in factors])
        return square_free,factors

    def sturm(self,p):
        p=self.monic(p); key=tuple(p)
        if key in self.chain_cache: return self.chain_cache[key]
        self.a.counters['sturm_chains_constructed']+=1
        chain=[p]; derivative=self.derivative(p)
        if derivative: chain.append(derivative)
        self.a.counters['max_sturm_chain_length']=max(self.a.counters['max_sturm_chain_length'],len(chain))
        while len(chain)>=2:
            _,remainder=self.divide(chain[-2],chain[-1])
            if not remainder: break
            remainder=[self.a.neg(x) for x in remainder]
            scale=remainder[-1] if self.a.cmp(remainder[-1],self.a.zero)>0 else self.a.neg(remainder[-1])
            remainder=[self.a.div(x,scale) for x in remainder]
            if len(chain)>=5: self.a.unresolved('sturm_chain_length_cap')
            chain.append(remainder)
            self.a.counters['max_sturm_chain_length']=max(self.a.counters['max_sturm_chain_length'],len(chain))
        self.a.counters['max_sturm_chain_length']=max(self.a.counters['max_sturm_chain_length'],len(chain))
        self.chain_cache[key]=chain; return chain

    def variations(self,chain,x):
        self.a.counters['sturm_variation_evaluations']+=1; previous=0; variations=0
        for p in chain:
            sign=self.a.cmp(self.evaluate(p,x),self.a.zero)
            if sign:
                if previous and previous!=sign: variations+=1
                previous=sign
        return variations

    def count_open(self,chain,left,right):
        self.a.counters['root_count_queries']+=1
        order=self.a.cmp(left,right); self.ensure(order<=0,'reversed_root_interval')
        if order==0: return 0
        # Zero-skipping variation at a simple root is its right-hand limit.
        count=self.variations(chain,left)-self.variations(chain,right)
        if self.a.cmp(self.evaluate(chain[0],right),self.a.zero)==0: count-=1
        self.ensure(0<=count<=len(chain[0])-1,'inconsistent_open_root_count')
        return count

    def multiplicity(self,left,right,exact,factors):
        hits=[]
        for f,m in factors:
            hit=(self.a.cmp(self.evaluate(f,left),self.a.zero)==0) if exact else self.count_open(self.sturm(f),left,right)==1
            if hit: hits.append(m)
        self.ensure(len(hits)==1,'unresolved_root_multiplicity'); return hits[0]

    def add_root(self,left,right,exact,factors,location):
        self.ensure(len(self.roots)<4,'too_many_distinct_roots')
        root=dict(left=left,right=right,exact=exact,multiplicity=self.multiplicity(left,right,exact,factors),location=location)
        self.roots.append(root); self.a.counters['distinct_roots']+=1

    def isolate(self,chain,left,right,count,depth,factors):
        self.a.tick()
        if self.a.counters['isolation_nodes']>=512: self.a.unresolved('isolation_nodes_cap')
        if depth>64: self.a.unresolved('isolation_depth_cap')
        self.a.counters['isolation_nodes']+=1; self.a.counters['max_depth']=max(self.a.counters['max_depth'],depth)
        if count==0: return
        p=chain[0]; left_root=self.a.cmp(self.evaluate(p,left),self.a.zero)==0
        right_root=self.a.cmp(self.evaluate(p,right),self.a.zero)==0
        width=self.a.sub(right,left)
        if count==1 and not left_root and not right_root and self.a.cmp(width,self.a.convert(Fraction(1,2**40)))<=0:
            self.add_root(left,right,False,factors,'interior'); return
        if depth==64: self.a.unresolved('isolation_depth_cap')
        middle=self.a.midpoint(left,right); middle_root=self.a.cmp(self.evaluate(p,middle),self.a.zero)==0
        lc=self.count_open(chain,left,middle); rc=self.count_open(chain,middle,right)
        self.ensure(lc+rc+int(middle_root)==count,'split_root_count_inconsistent')
        self.isolate(chain,left,middle,lc,depth+1,factors)
        if middle_root: self.add_root(middle,middle,True,factors,'interior')
        self.isolate(chain,middle,right,rc,depth+1,factors)

    def axial(self,values):
        z1,z2,mu,tol=(self.a.convert(values[k]) for k in ('z1','z2','mu_z','tolerance'))
        self.ensure(self.a.cmp(tol,self.a.zero)>=0,'negative_axial_tolerance')
        dz=self.a.sub(z2,z1); offset=self.a.sub(z1,mu)
        if self.a.cmp(dz,self.a.zero)==0:
            if self.a.cmp(offset,self.a.neg(tol))<0 or self.a.cmp(offset,tol)>0: return None
            return self.a.zero,self.a.one
        u=self.a.div(self.a.sub(self.a.neg(tol),offset),dz); v=self.a.div(self.a.sub(tol,offset),dz)
        if self.a.cmp(u,v)>0: u,v=v,u
        left=self.a.zero if self.a.cmp(u,self.a.zero)<0 else u
        right=self.a.one if self.a.cmp(v,self.a.one)>0 else v
        return (left,right) if self.a.cmp(left,right)<=0 else None

    def stationary(self,values,left,right):
        b1,b2,M11,M12,M22=(self.a.convert(values[k]) for k in ('b1','b2','M11','M12','M22'))
        beta=self.a.sub(b2,b1); m1=self.a.mul(self.a.two,self.a.sub(M12,M11))
        m2=self.a.add(self.a.sub(M11,self.a.mul(self.a.two,M12)),M22)
        A0=self.a.sub(self.a.mul(self.a.mul(self.a.two,beta),M11),self.a.mul(b1,m1))
        A1=self.a.sub(self.a.mul(beta,m1),self.a.mul(self.a.mul(self.a.two,b1),m2))
        if self.a.cmp(A1,self.a.zero)==0:
            record=dict(A0=A0,A1=A1,kind='constant_objective' if self.a.cmp(A0,self.a.zero)==0 else 'monotone',root=None,in_axial_interval=False)
        else:
            root=self.a.div(self.a.neg(A0),A1)
            record=dict(A0=A0,A1=A1,kind='one_stationary_root',root=root,
                in_axial_interval=self.a.cmp(left,root)<=0 and self.a.cmp(root,right)<=0)
        self.state['stationary']=record; return record

    def root_sides(self,p,left,right):
        for root in self.roots:
            if root['exact']:
                derivative=p
                for _ in range(root['multiplicity']): derivative=self.derivative(derivative)
                sign=self.a.cmp(self.evaluate(derivative,root['left']),self.a.zero)
                self.ensure(sign!=0,'multiplicity_derivative_inconsistent')
                ls=sign*(-1 if root['multiplicity']%2 else 1) if self.a.cmp(left,root['left'])<0 else None
                rs=sign if self.a.cmp(root['right'],right)<0 else None
            else:
                ls=self.a.cmp(self.evaluate(p,root['left']),self.a.zero)
                rs=self.a.cmp(self.evaluate(p,root['right']),self.a.zero)
                self.ensure(ls!=0 and rs!=0,'nonexact_bracket_endpoint_root')
            root.update(left_sign=ls,right_sign=rs,isolated_feasible=(ls is None or ls>0) and (rs is None or rs>0))

    def complementary_intervals(self,p,left,right):
        for i in range(len(self.roots)+1):
            previous=self.roots[i-1] if i else None; following=self.roots[i] if i<len(self.roots) else None
            lo=previous['right'] if previous else left; hi=following['left'] if following else right
            # An exact root at an axial endpoint leaves no outer open interval.
            if previous is None and following is not None and following['exact'] and self.a.cmp(following['left'],left)==0: continue
            if following is None and previous is not None and previous['exact'] and self.a.cmp(previous['right'],right)==0: continue
            if self.a.cmp(left,right)==0: continue
            comparison=self.a.cmp(lo,hi); self.ensure(comparison<=0,'overlapping_root_brackets')
            point=self.a.midpoint(lo,hi) if comparison<0 else lo
            sign=self.a.cmp(self.evaluate(p,point),self.a.zero)
            self.ensure(not p or sign!=0,'unresolved_complementary_interval_sign')
            record=dict(id='interval:'+str(i),left=lo,right=hi,sign=sign,feasible=sign<=0,
                certified_open_interior=comparison<0,midpoint=point if comparison<0 else None)
            self.intervals.append(record)
            if sign<=0 and comparison==0: self.state['unresolved_reasons'].append('no_isolated_open_interior:'+record['id'])

    def attempt(self,value,source,p,left,right):
        if self.a.counters['weight_attempts']>=26: self.a.unresolved('weight_attempts_cap')
        self.a.counters['weight_attempts']+=1
        self.ensure(math.isfinite(value),'nonfinite_float_weight'); eta=self.a.convert(value)
        domain=self.a.cmp(self.a.zero,eta)<=0 and self.a.cmp(eta,self.a.one)<=0
        if domain:
            axial=self.a.cmp(left,eta)<=0 and self.a.cmp(eta,right)<=0
            polynomial_value=self.evaluate(p,eta); polynomial=self.a.cmp(polynomial_value,self.a.zero)<=0
        else:
            self.a.counters['outside_weight_attempts']+=1; axial=False; polynomial=False; polynomial_value=None
        self.state['attempts'].append(dict(ordinal=self.a.counters['weight_attempts'],eta=value,source=source,
            in_unit_interval=domain,rounded_axial_feasible=axial,rounded_covariance_feasible=polynomial,
            rounded_polynomial_value=polynomial_value,rounded_feasible=domain and axial and polynomial))

    def nearest_three(self,value,source,p,left,right):
        center=self.a.to_float(value)
        for v in (math.nextafter(center,-math.inf),center,math.nextafter(center,math.inf)):
            self.attempt(v,source,p,left,right)

    def construct_candidates(self,p,left,right,stationary):
        for i,root in enumerate(self.roots):
            source='root:'+str(i); root['id']=source
            if root['exact']: self.nearest_three(root['left'],source,p,left,right)
            else:
                for value in (root['left'],self.a.midpoint(root['left'],root['right']),root['right']):
                    self.attempt(self.a.to_float(value),source,p,left,right)
        self.nearest_three(left,'axial:left',p,left,right)
        self.nearest_three(right,'axial:right',p,left,right)
        if stationary['in_axial_interval']: self.nearest_three(stationary['root'],'stationary',p,left,right)
        for interval in self.intervals:
            if interval['feasible'] and interval['certified_open_interior']:
                self.attempt(self.a.to_float(interval['midpoint']),interval['id'],p,left,right)
        unique={}
        for attempt in self.state['attempts']:
            if not attempt['in_unit_interval']: continue
            value=attempt['eta']
            if value not in unique:
                unique[value]=dict(eta=value,rounded_feasible=attempt['rounded_feasible'],sources=[attempt['source']])
                attempt['duplicate_of']=None
            else:
                self.a.counters['duplicate_weight_attempts']+=1
                attempt['duplicate_of']=value
                if attempt['source'] not in unique[value]['sources']: unique[value]['sources'].append(attempt['source'])
        self.state['candidates']=[unique[x] for x in sorted(unique)]
        self.a.counters['unique_in_range_candidates']=len(unique)
        self.coverage(p,left,right)

    def coverage(self,p,left,right):
        groups=[]; candidates=self.state['candidates']
        for root in self.roots:
            eligible=[]
            for candidate in candidates:
                if not candidate['rounded_feasible']: continue
                eta=self.a.convert(candidate['eta']); exact_zero=self.a.cmp(self.evaluate(p,eta),self.a.zero)==0
                inside=self.a.cmp(root['left'],eta)<=0 and self.a.cmp(eta,root['right'])<=0
                if (root['id'] in candidate['sources'] and not root['isolated_feasible']) or (inside and exact_zero): eligible.append(candidate['eta'])
            groups.append(dict(id=root['id'],kind='isolated_root' if root['isolated_feasible'] else 'root_boundary',candidate_etas=eligible))
        for source,value in (('axial:left',left),('axial:right',right)):
            if self.a.cmp(self.evaluate(p,value),self.a.zero)<=0:
                eligible=[c['eta'] for c in candidates if c['rounded_feasible'] and source in c['sources']]
                groups.append(dict(id=source,kind='axial_boundary',candidate_etas=eligible))
        for interval in self.intervals:
            if not interval['feasible']: continue
            eligible=[]
            for candidate in candidates:
                eta=self.a.convert(candidate['eta'])
                if candidate['rounded_feasible'] and self.a.cmp(interval['left'],eta)<0 and self.a.cmp(eta,interval['right'])<0:
                    eligible.append(candidate['eta'])
            groups.append(dict(id=interval['id'],kind='open_interval',candidate_etas=eligible))
        self.state['coverage_groups']=groups
        for group in groups:
            if not group['candidate_etas']: self.state['unresolved_reasons'].append('unrepresented_feasible_group:'+group['id'])
        self.state['representable_candidate_construction_complete']=not self.state['unresolved_reasons']

    def run(self,coefficients,axial,primary):
        self.ensure(1<=len(coefficients)<=5,'covariance_polynomial_degree_cap')
        p=self.trim([self.a.convert(x) for x in coefficients])
        self.state['polynomial']=dict(coefficients=p,degree=len(p)-1,zero_everywhere=not p)
        interval=self.axial(axial)
        if interval is None:
            self.state.update(status='rounded_infeasible',rounded_feasible_set_empty=True,
                root_isolation_complete_for_rounded_polynomial=True,representable_candidate_construction_complete=True)
            return
        left,right=interval; self.state['axial_interval']=dict(left=left,right=right,singleton=self.a.cmp(left,right)==0)
        if len(p)>1:
            square_free,factors=self.square_free(p); chain=self.sturm(square_free)
            if self.a.cmp(self.evaluate(square_free,left),self.a.zero)==0: self.add_root(left,left,True,factors,'left_endpoint')
            if self.a.cmp(left,right)<0:
                count=self.count_open(chain,left,right)
                self.isolate(chain,left,right,count,0,factors)
                if self.a.cmp(self.evaluate(square_free,right),self.a.zero)==0: self.add_root(right,right,True,factors,'right_endpoint')
            self.roots.sort(key=cmp_to_key(lambda x,y:self.a.cmp(x['left'],y['left'])))
            self.root_sides(p,left,right)
        self.complementary_intervals(p,left,right)
        endpoints_feasible=(self.a.cmp(self.evaluate(p,left),self.a.zero)<=0 or self.a.cmp(self.evaluate(p,right),self.a.zero)<=0)
        feasible=bool(self.roots) or endpoints_feasible or any(x['feasible'] for x in self.intervals)
        self.state['rounded_feasible_set_empty']=not feasible
        self.state['root_isolation_complete_for_rounded_polynomial']=True
        if not feasible:
            self.state.update(status='rounded_infeasible',representable_candidate_construction_complete=True); return
        stationary=self.stationary(primary,left,right)
        self.construct_candidates(p,left,right,stationary)
        self.state['status']='candidate_construction_complete' if self.state['representable_candidate_construction_complete'] else 'inner_feasibility_unresolved'


def _serializable(value):
    if isinstance(value,Fraction): return str(value.numerator)+'/'+str(value.denominator)
    if isinstance(value,dict): return {key:_serializable(item) for key,item in value.items()}
    if isinstance(value,(list,tuple)): return [_serializable(item) for item in value]
    return value


def solve_weights(covariance_coefficients,axial,primary,deadline_ns=None):
    """Return <=26 attempts and procedural coverage, never a physical verdict.

    axial keys: z1,z2,mu_z,tolerance. primary keys: b1,b2,M11,M12,M22.
    Global timeout propagates with partial_result; local caps return unresolved.
    """
    arithmetic=None; solver=None
    try:
        arithmetic=Arithmetic(deadline_ns); arithmetic.initialize(); solver=Solver(arithmetic)
        solver.run(covariance_coefficients,axial,primary)
    except TimeoutError as error:
        partial=solver.state if solver is not None else dict(status='global_deadline',counters=arithmetic.counters if arithmetic else {})
        error.partial_result=_serializable(partial); raise
    except (GeometryUnresolved,ZeroDivisionError,OverflowError) as error:
        if solver is None:
            return dict(status='inner_feasibility_unresolved',attempts=[],candidates=[],roots=[],intervals=[],coverage_groups=[],
                counters=arithmetic.counters if arithmetic else {},unresolved_reasons=[str(error)],rounded_feasible_set_empty=None,
                root_isolation_complete_for_rounded_polynomial=False,representable_candidate_construction_complete=False)
        solver.state['status']='inner_feasibility_unresolved'
        solver.state['representable_candidate_construction_complete']=False
        solver.state['unresolved_reasons'].append(str(error))
    return _serializable(solver.state)
