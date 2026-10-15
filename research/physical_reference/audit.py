"""Independent P5c audit. Does not import the production core or fixture builder."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from decimal import Decimal, localcontext
from pathlib import Path

import numpy as np

ATOL = 1e-11
RTOL = 1e-10
PI_TEXT = "3.14159265358979323846264338327950288419716939937510582097494459230781640628620899"
CASE_IDS = [
    "measure-base", "measure-split2", "measure-split4", "measure-selective2",
    "measure-reverse", "measure-volume-half", "measure-volume-double",
    "kernel-analytic", "field-n8", "field-n16", "field-n32", "field-domain40",
    "temperature-constant", "temperature-linear-samples", "buoyancy-source-units",
    "strain-dt010", "strain-dt005", "strain-dt0025",
    "mean-dt010", "mean-dt005", "mean-dt0025",
]
STATIC_IDS = CASE_IDS[:12]
CENTER = np.array([0., .8, 0.])
OFFSETS = np.array([
    [-.12, -.08, -.10], [.11, -.06, -.09], [-.10, .13, -.07], [.14, .09, -.12],
    [-.13, -.11, .15], [.09, -.10, .11], [-.08, .12, .14], [.12, .14, .10],
])
FIELD_SAMPLE_INDICES = [0, 12, 24, 50, 62, 74, 100, 112, 124]


def _dec(x):
    return Decimal.from_float(float(x))


def _erf_decimal(x):
    """Entire convergent series in Decimal, independent of production special functions."""
    if not x:
        return Decimal(0)
    term = x
    value = term
    for k in range(1, 2000):
        term *= -(x*x) / Decimal(k)
        add = term / Decimal(2*k+1)
        value += add
        if abs(add) < Decimal("1e-90"):
            return Decimal(2) * value / Decimal(PI_TEXT).sqrt()
    raise ArithmeticError("Decimal erf series did not converge")


def _decimal_factors(radius, sigma):
    r, s = _dec(radius), _dec(sigma)
    pi = Decimal(PI_TEXT)
    c = (Decimal(2)/pi).sqrt()
    if not r:
        return c/(3*s**3), -c/(5*s**5)
    q = r/s
    exp = (-q*q/2).exp()
    g = _erf_decimal(q/Decimal(2).sqrt()) - c*q*exp
    gp = c*q*q*exp
    return g/r**3, (q*gp-3*g)/r**5


def _cross_decimal(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def decimal_fields(sources, positions, velocity=True, thermal=True):
    """100 working digits; independent scalar arithmetic on exact binary64 inputs."""
    result = {k: [] for k in ("velocity", "jacobian", "temperature", "gradient", "numerator", "denominator")}
    with localcontext() as ctx:
        ctx.prec = 100  # Guard against the alternating erf series' large-q cancellation.
        pi = Decimal(PI_TEXT)
        inv4pi = 1/(4*pi)
        norm = (2*pi)**Decimal("1.5")
        for point in positions:
            u = [Decimal(0) for _ in range(3)]
            jac = [[Decimal(0) for _ in range(3)] for _ in range(3)]
            weights, grads, temps = [], [], []
            for src in sources:
                r = [_dec(point[k])-_dec(src["position"][k]) for k in range(3)]
                sig = _dec(src["sigma"])
                r2 = sum((v*v for v in r), Decimal(0))
                if velocity:
                    # Radius is kept in Decimal; do not re-round it through binary64.
                    rr = r2.sqrt()
                    c = (2/pi).sqrt()
                    if not rr:
                        f, dd = c/(3*sig**3), -c/(5*sig**5)
                    else:
                        q = rr/sig
                        e = (-q*q/2).exp()
                        g = _erf_decimal(q/Decimal(2).sqrt())-c*q*e
                        gp = c*q*q*e
                        f, dd = g/rr**3, (q*gp-3*g)/rr**5
                    gamma = [_dec(v) for v in src["Gamma"]]
                    cr = _cross_decimal(gamma, r)
                    for row in range(3):
                        u[row] += inv4pi*f*cr[row]
                    for col in range(3):
                        basis = [Decimal(int(k == col)) for k in range(3)]
                        cb = _cross_decimal(gamma, basis)
                        for row in range(3):
                            jac[row][col] += inv4pi*(f*cb[row]+dd*cr[row]*r[col])
                if thermal:
                    w = _dec(src["volume"])*(-r2/(2*sig*sig)).exp()/(norm*sig**3)
                    weights.append(w)
                    grads.append([-v*w/(sig*sig) for v in r])
                    temps.append(_dec(src["temperature"]))
            if velocity:
                result["velocity"].append([float(v) for v in u])
                result["jacobian"].append([[float(v) for v in row] for row in jac])
            if thermal:
                den = sum(weights, Decimal(0))
                if den <= 0:
                    raise ArithmeticError("independent thermal denominator is non-positive")
                num = sum((w*t for w, t in zip(weights, temps)), Decimal(0))
                tbar = num/den
                grad = [sum(((t-tbar)*gg[k] for t, gg in zip(temps, grads)), Decimal(0))/den for k in range(3)]
                for key, val in [("temperature", float(tbar)), ("gradient", [float(v) for v in grad]),
                                 ("numerator", float(num)), ("denominator", float(den))]:
                    result[key].append(val)
    return {k: np.asarray(v, dtype=float) for k, v in result.items() if v}


def radial_quadrature(radius, sigma, order):
    """Positive integral reference, no erf or Taylor polynomial."""
    nodes, weights = np.polynomial.legendre.leggauss(order)
    t, weights = .5*(nodes+1.), .5*weights
    radius, sigma = np.broadcast_arrays(np.asarray(radius, float), np.asarray(sigma, float))
    q = radius/sigma
    e = np.exp(-.5*q[..., None]**2*t**2)
    c = math.sqrt(2/math.pi)
    f = c*np.sum(e*(weights*t**2), axis=-1)/sigma**3
    d = -c*np.sum(e*(weights*t**4), axis=-1)/sigma**5
    return f, d


def quadrature_velocity(sources, positions, order):
    sp = np.asarray([s["position"] for s in sources], float)
    sg = np.asarray([s["sigma"] for s in sources], float)
    gamma = np.asarray([s["Gamma"] for s in sources], float)
    out = []
    for p in positions:
        r = np.asarray(p)-sp
        radius = np.sqrt(np.sum(r*r, axis=1))
        f, _ = radial_quadrature(radius, sg, order)
        # fsum keeps the audit reduction independent of NumPy/production pairwise summation.
        terms = np.cross(gamma, r)*f[:, None]/(4*math.pi)
        out.append([math.fsum(terms[:, k]) for k in range(3)])
    return np.asarray(out)


def filtered_field(points):
    r = np.asarray(points)-CENTER
    a, sig, amp = .1, .06, .01
    width2 = a*a+sig*sig
    coeff = amp*a**3/width2**2.5*np.exp(-np.sum(r*r, axis=-1)/(2*width2))
    return coeff[:, None]*np.column_stack((-r[:, 1], r[:, 0], np.zeros(len(r))))


def gh_filtered(points, order):
    nodes, weights = np.polynomial.hermite.hermgauss(order)
    nodes = math.sqrt(2)*nodes
    weights = weights/math.sqrt(math.pi)
    shift = .06*np.stack(np.meshgrid(nodes, nodes, nodes, indexing="ij"), axis=-1).reshape(-1, 3)
    ww = np.einsum("i,j,k->ijk", weights, weights, weights).reshape(-1)
    out = []
    for point in points:
        r = np.asarray(point)-CENTER+shift
        e = np.exp(-np.sum(r*r, axis=1)/(2*.1**2))
        u = (.01/.1**2)*e[:, None]*np.column_stack((-r[:, 1], r[:, 0], np.zeros(len(r))))
        out.append([math.fsum(ww*u[:, k]) for k in range(3)])
    return np.asarray(out)


def rel_l2(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    den = float(np.sum(b*b))
    return math.sqrt(float(np.sum((a-b)**2))/den) if den else (0. if np.array_equal(a, b) else None)


class Checks:
    def __init__(self):
        self.rows = []

    def check(self, name, passed, kind="physical", **details):
        self.rows.append({"name": name, "kind": kind, "passed": bool(passed), **details})
        return bool(passed)

    def close(self, name, actual, expected, kind="physical", atol=ATOL, rtol=RTOL):
        a, b = np.asarray(actual, float), np.asarray(expected, float)
        if a.shape != b.shape or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
            return self.check(name, False, kind, actualShape=list(a.shape), expectedShape=list(b.shape), reason="shape or nonfinite")
        err = np.abs(a-b)
        limit = atol+rtol*np.maximum(np.abs(a), np.abs(b))
        flat = int(np.argmax(err)) if err.size else 0
        index = list(np.unravel_index(flat, err.shape)) if err.size else []
        ratio = np.divide(err, limit, out=np.zeros_like(err), where=limit>0)
        # Exact comparisons have a zero tolerance; report mismatch separately,
        # never encode an infinite/NaN ratio in immutable JSON evidence.
        exact_mismatches = int(np.sum((limit == 0) & (err != 0)))
        return self.check(name, bool(np.all(err <= limit)), kind, maxAbsError=float(err.max()) if err.size else 0.,
                          maxToleranceRatio=float(np.max(ratio)) if err.size else 0., exactMismatches=exact_mismatches,
                          maxErrorIndex=[int(i) for i in index])


def _sources_arrays(sources):
    return {k: np.asarray([s[k] for s in sources], float) for k in
            ("position", "volume", "Gamma", "sigma", "temperature", "capacityPerVolume")}


def _base_sources():
    out = []
    for i, p in enumerate(OFFSETS):
        v = .001*(1+.2*i)
        omega = np.array([.5+.125*i, -.25+.05*i, .4-.03*i])
        out.append({"id": f"s{i}", "anchorId": f"s{i}", "position": (CENTER+p).tolist(), "volume": v,
                    "Gamma": (v*omega).tolist(), "sigma": .07+.0025*i, "temperature": 300+10*i,
                    "capacityPerVolume": 3.})
    return out


def _base_queries():
    return [{"id": f"q-{a}-{b}-{d}", "position": (CENTER+.1*(np.array([a,b,d])-1.5)).tolist()}
            for a in range(4) for b in range(4) for d in range(4)]


def _finite_tree(value):
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(_finite_tree(v) for v in value.values())
    if isinstance(value, list):
        return all(_finite_tree(v) for v in value)
    return True


def _source_sanity(ch, cid, sources):
    ids = [s["id"] for s in sources]
    ch.check(cid+"/source-ids", len(ids) == len(set(ids)) and all(isinstance(i, str) for i in ids), "execution")
    arr = _sources_arrays(sources)
    ch.check(cid+"/source-shapes", arr["position"].shape == (len(sources),3) and arr["Gamma"].shape == (len(sources),3), "execution")
    ch.check(cid+"/source-domain", bool(np.all(arr["volume"]>0) and np.all(arr["sigma"]>0)
             and np.all(arr["capacityPerVolume"]>0) and np.all(arr["temperature"]>=0)), "execution")


def _compare_sources(ch, name, sources, expected, id_exact=True, evolved=False):
    if not ch.check(name+"/count", len(sources)==len(expected), "execution"):
        return
    if id_exact:
        ch.check(name+"/ids", [s["id"] for s in sources]==[s["id"] for s in expected], "execution")
        ch.check(name+"/anchor-ids", [s["anchorId"] for s in sources]==[s["anchorId"] for s in expected], "execution")
    actual_arrays = _sources_arrays(sources)
    for key, val in _sources_arrays(expected).items():
        if evolved and key in ("position", "Gamma"):
            ch.close(name+"/"+key, actual_arrays[key], val, "physical")
        else:
            ch.close(name+"/"+key, actual_arrays[key], val, "execution", atol=2e-15, rtol=2e-14)


def _totals(sources):
    return {"volume": math.fsum(s["volume"] for s in sources),
            "Gamma": [math.fsum(s["Gamma"][k] for s in sources) for k in range(3)],
            "energy": math.fsum(s["volume"]*s["capacityPerVolume"]*s["temperature"] for s in sources)}


def _check_queries(ch, cid, queries, expected_positions, expected_ids=None):
    ids = [q["id"] for q in queries]
    ch.check(cid+"/query-ids-unique", len(ids)==len(set(ids)), "execution")
    if expected_ids is not None:
        ch.check(cid+"/query-ids", ids==expected_ids, "execution")
    ch.close(cid+"/query-positions", [q["position"] for q in queries], expected_positions, "execution", atol=2e-15, rtol=2e-14)


def _check_output(ch, case, reference):
    cid = case["id"]
    for key, val in reference.items():
        ch.close(cid+"/reference-"+key, case["output"][key], val)
    if "temperature" in reference:
        n = len(reference["temperature"])
        out = case["output"]
        ch.check(cid+"/supported", len(out["supported"])==n and all(v is True for v in out["supported"]), "execution")
        ch.check(cid+"/no-underflow", len(out["denominatorUnderflow"])==n and all(v is False for v in out["denominatorUnderflow"]), "execution")
        ch.check(cid+"/no-numerator-underflow", len(out["numeratorUnderflow"])==n and all(v is False for v in out["numeratorUnderflow"]), "execution")
        ch.close(cid+"/log-denominator", out["logDenominator"], np.log(reference["denominator"]))


def _clone_sources(sources):
    return copy.deepcopy(sources)


def _measure_expected(cid):
    base = _base_sources()
    if cid == "measure-reverse":
        return base[::-1]
    if cid in ("measure-volume-half", "measure-volume-double"):
        scale = .5 if cid.endswith("half") else 2.
        for s in base:
            s["volume"] *= scale
            s["Gamma"] = [g*scale for g in s["Gamma"]]
        return base
    out = []
    for i, s in enumerate(base):
        n = 2 if cid=="measure-split2" or (cid=="measure-selective2" and i%2) else 4 if cid=="measure-split4" else 1
        for k in range(n):
            cp = copy.deepcopy(s)
            if n>1:
                cp["id"] = f"{s['id']}/{k}"
            cp["volume"] /= n
            cp["Gamma"] = [g/n for g in cp["Gamma"]]
            out.append(cp)
    return out


def _audit_measure(ch, cases, diagnostics):
    queries = _base_queries()
    for cid in CASE_IDS[:7]:
        case = cases[cid]
        expected = _measure_expected(cid)
        _compare_sources(ch, cid+"/fixture", case["sources"], expected)
        _check_queries(ch, cid, case["queries"], [q["position"] for q in queries], [q["id"] for q in queries])
        for key, val in _totals(case["sources"]).items():
            ch.close(cid+"/total-"+key, case["totals"][key], val)
        ref = decimal_fields(case["sources"], [q["position"] for q in queries])
        _check_output(ch, case, ref)
    base = cases["measure-base"]
    for cid in CASE_IDS[1:7]:
        scale = .5 if cid.endswith("half") else 2. if cid.endswith("double") else 1.
        for key in ("velocity", "jacobian", "numerator", "denominator", "temperature", "gradient"):
            fac = 1. if key in ("temperature", "gradient") else scale
            ch.close(cid+"/representation-"+key, cases[cid]["output"][key], np.asarray(base["output"][key])*fac)
        for key in ("volume", "Gamma", "energy"):
            ch.close(cid+"/representation-total-"+key, cases[cid]["totals"][key], np.asarray(base["totals"][key])*scale)
    diagnostics["measure"] = {"cases": 7, "queriesPerCase": 64, "independentReference": "100-working-digit Decimal scalar sums"}


def _audit_kernel(ch, case, diagnostics):
    qs = [.01, .1, .25, math.nextafter(.5, 0.), .5, math.nextafter(.5, math.inf), 1., 2., 4., 8.]
    dirs = [np.array([1.,0.,0.]), np.array([0.,0.,1.]), np.array([2.,-1.,2.])/3]
    expected_positions = [np.zeros(3)]+[.07*q*d for q in qs for d in dirs]
    expected_ids=["q-origin"]+[f"q-{i}-{j}" for i in range(len(qs)) for j in range(3)]
    _check_queries(ch, case["id"], case["queries"], expected_positions,expected_ids)
    src = case["sources"]
    ch.check("kernel/source-count", len(src)==1, "execution")
    ch.check("kernel/source-ids",[(s["id"],s["anchorId"]) for s in src]==[("s0","s0")],"execution")
    expected = {"position": [[0.,0.,0.]], "volume": [.001], "Gamma": [[0.,0.,.001]], "sigma": [.07], "temperature": [450.], "capacityPerVolume": [3.]}
    for key, val in expected.items():
        ch.close("kernel/fixture-"+key, _sources_arrays(src)[key], val, "execution", atol=2e-15, rtol=2e-14)
    positions = [q["position"] for q in case["queries"]]
    ch.close("kernel/constants-switch",case["constants"]["qSwitch"],.5,"execution",atol=0,rtol=0)
    ch.check("kernel/constants-terms",case["constants"]["seriesTerms"]==12,"execution")
    ch.check("kernel/constants-branch",case["constants"]["seriesBranch"]=="q < qSwitch","execution")
    branch_counts={"series":0,"regular":0}
    for i,qrow in enumerate(case["queries"]):
        requested=0. if i==0 else qs[(i-1)//3]
        actual=math.hypot(*qrow["position"])/.07
        ch.close(f"kernel/q-{i}-requested",qrow["requestedQ"],requested,"execution",atol=0,rtol=0)
        ch.close(f"kernel/q-{i}-actual",qrow["actualQ"],actual,"execution",atol=2e-15,rtol=2e-14)
        if i:
            ch.close(f"kernel/q-{i}-direction",qrow["direction"],dirs[(i-1)%3],"execution",atol=0,rtol=0)
        # Actual q is logged using the production norm; require its declared branch
        # and separately certify the exact sigma=1 radial probes below.
        branch="series" if qrow["actualQ"]<.5 else "regular"
        ch.check(f"kernel/q-{i}-branch",qrow["branch"]==branch,"execution")
        branch_counts[branch]+=1
    for qi,relation in [(3,"lower"),(4,"equal"),(5,"upper")]:
        qrow=case["queries"][1+3*qi]
        independently_computed_q=math.hypot(*qrow["position"])/.07
        ok=independently_computed_q<.5 if relation=="lower" else independently_computed_q==.5 if relation=="equal" else independently_computed_q>.5
        ch.check("kernel/world-switch-"+relation,ok,"execution",actualQ=independently_computed_q)
    ref = decimal_fields(src, positions)
    _check_output(ch, case, ref)
    jac = np.asarray(case["output"]["jacobian"])
    trace = np.trace(jac, axis1=1, axis2=2)
    limit = 1e-11+1e-10*np.max(np.abs(jac), axis=(1,2))
    ch.check("kernel/divergence", bool(np.all(np.abs(trace)<=limit)), maxAbsTrace=float(np.max(np.abs(trace))))
    fd_rows = []
    for h in (.07*1e-4, .07*5e-5):
        fd = np.empty_like(jac)
        for axis in range(3):
            plus, minus = np.asarray(positions).copy(), np.asarray(positions).copy()
            plus[:,axis] += h
            minus[:,axis] -= h
            up = decimal_fields(src, plus, thermal=False)["velocity"]
            um = decimal_fields(src, minus, thermal=False)["velocity"]
            fd[:,:,axis] = (up-um)/(2*h)
        err = float(np.max(np.abs(jac-fd)))
        lim = 1e-7+1e-6*float(np.max(np.abs(ref["jacobian"])))
        ch.check(f"kernel/finite-difference-{h}", err<=lim, maxAbsError=err, limit=lim)
        fd_rows.append({"h":h,"maxAbsError":err})
    radial = case["radialProbes"]
    expected_q = [0.,.25,math.nextafter(.5,0.),.5,math.nextafter(.5,math.inf),1.]
    ch.close("kernel/radial-fixture", [p["q"] for p in radial], expected_q, "execution", atol=0, rtol=0)
    radial_rows = []
    for i, p in enumerate(radial):
        ch.check(f"kernel/radial-{i}-id",p["id"]==f"radial-{i}","execution")
        ch.check(f"kernel/radial-{i}-branch",p["branch"]==("series" if expected_q[i]<.5 else "regular"),"execution")
        ch.close(f"kernel/radial-{i}-radius", p["radius"], expected_q[i], "execution", atol=0, rtol=0)
        ch.close(f"kernel/radial-{i}-sigma", p["sigma"], 1., "execution", atol=0, rtol=0)
        with localcontext() as ctx:
            ctx.prec = 100
            f, d = _decimal_factors(p["radius"], p["sigma"])
        for key, val in [("F",float(f)),("D",float(d))]:
            ch.close(f"kernel/radial-{i}-{key}", p[key], val)
        for order in (32,64):
            gf, gd = radial_quadrature(p["radius"],p["sigma"],order)
            ch.close(f"kernel/gl{order}-{i}", [gf,gd], [float(f),float(d)], "reference")
        radial_rows.append({"q":p["q"],"branch":p["branch"],"F":float(f),"D":float(d)})
    diagnostics["kernel"]={"queries":len(positions),"finiteDifferences":fd_rows,"radial":radial_rows,"branchCounts":branch_counts}


def _field_expected(n, halfwidth):
    dx = 2*halfwidth/n
    r1 = -halfwidth+(np.arange(n)+.5)*dx
    r = np.stack(np.meshgrid(r1,r1,r1,indexing="ij"),axis=-1).reshape(-1,3)
    a, amp = .1,.01
    factor = amp*np.exp(-np.sum(r*r,axis=1)/(2*a*a))
    omega = factor[:,None]*np.column_stack((r[:,0]*r[:,2]/a**4,r[:,1]*r[:,2]/a**4,2/a**2-(r[:,0]**2+r[:,1]**2)/a**4))
    return {"position":r+CENTER,"volume":np.full(n**3,dx**3),"Gamma":omega*dx**3,"sigma":np.full(n**3,.06),"temperature":np.full(n**3,300.),"capacityPerVolume":np.full(n**3,3.)}


def _check_filtered_reference(ch,positions,ref):
    gh = {n:gh_filtered(positions,n) for n in (16,24)}
    gh_errors = {str(n):rel_l2(gh[n],ref) for n in (16,24)}
    gh_errors["16-vs-24"] = rel_l2(gh[16],gh[24])
    for key, err in gh_errors.items():
        ch.check("field/GH-"+key, err is not None and err<=1e-8,"reference",relativeL2=err)
    return gh_errors


def _audit_fields(ch, cases, diagnostics):
    positions = np.array([CENTER+.05*(np.array([a,b,d])-2) for a in range(5) for b in range(5) for d in range(5)])
    ref = filtered_field(positions)
    gh_errors = _check_filtered_reference(ch,positions,ref)
    rows=[]
    for cid,n,L in [("field-n8",8,.5),("field-n16",16,.5),("field-n32",32,.5),("field-domain40",40,.625)]:
        case=cases[cid]
        ch.check(cid+"/source-count",len(case["sources"])==n**3,"execution")
        expected=_field_expected(n,L)
        arr=_sources_arrays(case["sources"])
        for key,val in expected.items():
            ch.close(cid+"/fixture-"+key,arr[key],val,"execution",atol=2e-15,rtol=2e-14)
        ids=[f"s-{i}-{j}-{k}" for i in range(n) for j in range(n) for k in range(n)]
        ch.check(cid+"/grid-ids",[s["id"] for s in case["sources"]]==ids and [s["anchorId"] for s in case["sources"]]==ids,"execution")
        _check_queries(ch,cid,case["queries"],positions,[f"q-{i}-{j}-{k}" for i in range(5) for j in range(5) for k in range(5)])
        constants=case["constants"]
        for key,val in {"A":.01,"a":.1,"sigma":.06,"center":CENTER,"halfWidth":L,"n":n,"spacing":2*L/n}.items():
            ch.close(cid+"/constant-"+key,constants[key],val,"execution",atol=2e-15,rtol=2e-14)
        actual=np.asarray(case["output"]["velocity"])
        err=rel_l2(actual,ref)
        subset=positions[FIELD_SAMPLE_INDICES]
        gl={order:quadrature_velocity(case["sources"],subset,order) for order in (32,64)}
        gl_delta=rel_l2(gl[32],gl[64])
        ch.check(cid+"/GL-convergence",gl_delta is not None and gl_delta<=1e-8,"reference",relativeL2=gl_delta)
        ch.close(cid+"/GL64-discrete-velocity",actual[FIELD_SAMPLE_INDICES],gl[64])
        rows.append({"id":cid,"n":n,"halfWidth":L,"relativeL2":err,"maxAbsError":float(np.max(np.abs(actual-ref))),
                     "independentDiscreteCoverage":{"queryIndices":FIELD_SAMPLE_INDICES,"queries":9,"totalQueries":125,"sourceCount":len(case["sources"]),"orders":[32,64],"GL32vs64RelativeL2":gl_delta}})
    errors=[r["relativeL2"] for r in rows]
    ch.check("field/spatial-convergence",all(e is not None for e in errors[:3]) and errors[1]<errors[0] and errors[2]<errors[1] and errors[2]<=.01,relativeL2=errors[:3])
    domain_delta=np.asarray(cases["field-domain40"]["output"]["velocity"])-np.asarray(cases["field-n32"]["output"]["velocity"])
    diagnostics["field"]={"cases":rows,"GH":gh_errors,"domainExtension":{"sameSpacing":.03125,"relativeL2Difference":rel_l2(domain_delta+ref,ref),"maxAbsDifference":float(np.max(np.abs(domain_delta))),"decisionEffect":"descriptive only"}}


def _audit_temperature(ch,cases,diagnostics):
    queries=_base_queries()
    positions=np.asarray([q["position"] for q in queries])
    g=np.array([40.,-25.,30.])
    rows=[]
    for cid in ("temperature-constant","temperature-linear-samples"):
        case=cases[cid]
        expected=_base_sources()
        for s in expected:
            r=np.asarray(s["position"])-CENTER
            s["temperature"]=450. if cid.endswith("constant") else 450.+float(np.dot(g,r))
        _compare_sources(ch,cid+"/fixture",case["sources"],expected)
        _check_queries(ch,cid,case["queries"],positions,[q["id"] for q in queries])
        ref=decimal_fields(case["sources"],positions)
        _check_output(ch,case,ref)
        actual=np.asarray(case["output"]["gradient"])
        fd_rows=[]
        for h in (1e-5,5e-6):
            fd=np.empty_like(actual)
            for axis in range(3):
                plus,minus=positions.copy(),positions.copy()
                plus[:,axis]+=h
                minus[:,axis]-=h
                tp=decimal_fields(case["sources"],plus,velocity=False)["temperature"]
                tm=decimal_fields(case["sources"],minus,velocity=False)["temperature"]
                fd[:,axis]=(tp-tm)/(2*h)
            err=np.abs(actual-fd)
            lim=2e-6+2e-6*np.abs(ref["gradient"])
            ch.check(f"{cid}/finite-difference-{h}",bool(np.all(err<=lim)),maxAbsError=float(err.max()),maxToleranceRatio=float(np.max(err/lim)))
            fd_rows.append({"h":h,"maxAbsError":float(err.max())})
        if cid.endswith("constant"):
            ch.close(cid+"/constant-value",case["output"]["temperature"],np.full(64,450.),atol=1e-10,rtol=0)
            ch.close(cid+"/constant-gradient",actual,np.zeros((64,3)),atol=1e-9,rtol=0)
        rows.append({"id":cid,"finiteDifferences":fd_rows,"maxGradientMagnitude":float(np.max(np.linalg.norm(actual,axis=1)))})
    case=cases["buoyancy-source-units"]
    for key,val in {"ambientTemperature":300.,"temperatureScale":100.,"buoyancy":.5,"dt":.01,"prescribedGradient":g}.items():
        ch.close("buoyancy/constant-"+key,case["constants"][key],val,"execution",atol=0,rtol=0)
    reps=case["representations"]
    ch.check("buoyancy/representation-coverage",[r["id"] for r in reps]==["base","all-split2","selective2","reverse"],"execution")
    _compare_sources(ch,"buoyancy/top-level-base",case["sources"],reps[0]["sources"])
    aggregated={}
    for rep in reps:
        variant=rep["id"]
        mid={"base":"measure-base","all-split2":"measure-split2","selective2":"measure-selective2","reverse":"measure-reverse"}[variant]
        expected=_measure_expected(mid)
        for s in expected:
            s["Gamma"]=[0.,0.,0.]
            s["temperature"]=450.+float(np.dot(g,np.asarray(s["position"])-CENTER))
        sources=rep["sources"]
        name="buoyancy/"+variant
        _source_sanity(ch,name,sources)
        _compare_sources(ch,name+"/fixture",sources,expected)
        n=len(sources)
        rhs=np.asarray([s["volume"] for s in sources])[:,None]*np.array([-.15,0.,.2])
        ch.close(name+"/gradient",rep["gradient"],np.tile(g,(n,1)))
        ch.close(name+"/initial-velocity",rep["velocity"],np.zeros((n,3)))
        ch.close(name+"/initial-jacobian",rep["jacobian"],np.zeros((n,3,3)))
        ch.close(name+"/rhs",rep["rhs"],rhs)
        upd=copy.deepcopy(expected)
        for s,inc in zip(upd,.01*rhs):
            s["Gamma"]=inc.tolist()
        _compare_sources(ch,name+"/updated",rep["updatedSources"],upd,evolved=True)
        anchor={}
        for s in rep["updatedSources"]:
            anchor.setdefault(s["anchorId"],[]).append(s["Gamma"])
        agg={key:[math.fsum(row[k] for row in vals) for k in range(3)] for key,vals in anchor.items()}
        aggregated[variant]=agg
        for label, records in [("totalsBefore",sources),("totalsAfter",rep["updatedSources"])]:
            for key,val in _totals(records).items():
                ch.close(name+"/"+label+"-"+key,rep[label][key],val)
        ch.check(name+"/inputUnchanged",rep["inputUnchanged"] is True,"execution")
    for variant,agg in aggregated.items():
        ch.check("buoyancy/"+variant+"/anchor-coverage",set(agg)==set(aggregated["base"]),"execution")
        for anchor,val in agg.items():
            ch.close("buoyancy/"+variant+"/anchor-"+anchor,val,aggregated["base"][anchor])
    diagnostics["temperature"]={"cases":rows,"buoyancyAnchorUpdates":aggregated,
        "scope":"Shepard derivative checked against own field; analytic linear gradient injected only for source-unit test."}


def _audit_time(ch,cases,diagnostics):
    x0=np.array([.03,-.04,.05])
    strain=np.array([-.5,-.5,1.])
    accel=np.array([0.,.25,0.])
    result={"strain":[],"mean":[]}
    for mode in ("strain","mean"):
        for suffix,dt in [("010",.01),("005",.005),("0025",.0025)]:
            cid=f"{mode}-dt{suffix}"
            case=cases[cid]
            n=round(.1/dt)
            ch.close(cid+"/dt",case["dt"],dt,"execution",atol=0,rtol=0)
            ch.check(cid+"/steps",case["steps"]==n,"execution")
            ch.close(cid+"/horizon",case["constants"]["horizon"],.1,"execution",atol=0,rtol=0)
            base={"id":"s0","anchorId":"s0","position":x0.tolist(),"volume":.001,
                  "Gamma":[0.,0.,.001 if mode=="strain" else 0.],"sigma":.07,
                  "temperature":300. if mode=="strain" else 350.,"capacityPerVolume":3.}
            _compare_sources(ch,cid+"/initial-fixture",case["sources"],[base])
            if mode=="strain":
                ch.close(cid+"/strain",case["constants"]["strain"],np.diag(strain),"execution",atol=0,rtol=0)
            else:
                for key,val in {"ambientTemperature":300.,"temperatureScale":100.,"buoyancy":.5,"acceleration":accel}.items():
                    ch.close(cid+"/constant-"+key,case["constants"][key],val,"execution",atol=0,rtol=0)
            states=case["states"]
            ch.check(cid+"/state-coverage",len(states)==n+1 and [s["step"] for s in states]==list(range(n+1)),"execution")
            outputs=case["stepOutputs"]
            ch.check(cid+"/step-output-coverage",len(outputs)==n and [s["step"] for s in outputs]==list(range(1,n+1)),"execution")
            for k,state in enumerate(states):
                ch.close(cid+f"/time-{k}",state["time"],k*dt,"execution")
                exp=copy.deepcopy(base)
                if mode=="strain":
                    exp["position"]=(x0*(1+dt*strain)**k).tolist()
                    exp["Gamma"]=(np.asarray(base["Gamma"])*(1+dt*strain)**k).tolist()
                else:
                    exp["position"]=(x0+.5*accel*dt*dt*k*(k-1)).tolist()
                    ch.close(cid+f"/mean-{k}",state["meanVelocity"],accel*k*dt)
                _compare_sources(ch,cid+f"/state-{k}",state["sources"],[exp],evolved=True)
                for key,val in _totals(state["sources"]).items():
                    ch.close(cid+f"/total-{k}-{key}",state["totals"][key],val)
                if k<n:
                    op=outputs[k]
                    if mode=="strain":
                        ch.close(cid+f"/velocity-{k}",op["velocity"],[np.asarray(exp["position"])*strain])
                        ch.close(cid+f"/rhs-{k}",op["rhs"],[np.asarray(exp["Gamma"])*strain])
                        # Full J includes the nonzero Gaussian self skew matrix.
                        # Its product with this same Gamma is zero, so the
                        # closed-form strength evolution still uses D*Gamma.
                        old_gamma=np.asarray(exp["Gamma"])
                        gx,gy,gz=old_gamma
                        skew=np.array([[0.,-gz,gy],[gz,0.,-gx],[-gy,gx,0.]])
                        self_j=math.sqrt(2/math.pi)/(12*math.pi*base["sigma"]**3)*skew
                        ch.close(cid+f"/full-J-{k}",op["jacobian"],[self_j+np.diag(strain)])
                    else:
                        ch.close(cid+f"/velocity-{k}",op["velocity"],[accel*k*dt])
                        ch.close(cid+f"/rhs-{k}",op["rhs"],[[0.,0.,0.]])
                        ch.close(cid+f"/acceleration-{k}",op["acceleration"],accel)
            final=states[-1]["sources"][0]
            if mode=="strain":
                xr=x0*np.exp(.1*strain)
                gr=np.asarray(base["Gamma"])*np.exp(.1*strain)
                errors={"positionRelativeL2":rel_l2(final["position"],xr),"GammaRelativeL2":rel_l2(final["Gamma"],gr)}
            else:
                xr=x0+.5*accel*.1**2
                errors={"positionAbsoluteL2":float(np.linalg.norm(np.asarray(final["position"])-xr)),
                        "meanVelocityMaxAbsError":float(np.max(np.abs(np.asarray(states[-1]["meanVelocity"])-accel*.1)))}
            result[mode].append({"id":cid,"dt":dt,"steps":n,**errors})
        fields=["positionRelativeL2","GammaRelativeL2"] if mode=="strain" else ["positionAbsoluteL2"]
        for field in fields:
            es=[row[field] for row in result[mode]]
            good=all(e is not None and e>0 for e in es)
            ratios=[es[0]/es[1],es[1]/es[2]] if good else []
            passed=good and es[1]<es[0] and es[2]<es[1] and all(1.8<=r<=2.2 for r in ratios)
            if mode=="strain":
                passed=passed and es[2]<=2e-4
            ch.check(mode+"/convergence-"+field,passed,errors=es,ratios=ratios)
    diagnostics["time"]=result


def fault_injections(case_records):
    """Six predeclared negative tests, copied data only; no production imports.

    These exercise the same numerical/reference/fixture gates as audit_cases,
    in focused blocks to avoid repeating the large C reference calculation six
    times. A detection is valid only if the matching unmodified control passes.
    """
    cases={c["id"]:c for c in case_records}
    if list(cases)!=CASE_IDS:
        raise ValueError("fault suite requires the complete ordered 21-case evidence")
    rows=[]

    def exercise(label,control,mutant):
        good, bad=Checks(),Checks()
        control(good)
        mutant(bad)
        failures=[r for r in bad.rows if not r["passed"]]
        control_ok=all(r["passed"] for r in good.rows)
        rows.append({"id":label,"controlPassed":control_ok,"rejected":bool(failures),
                     "passed":control_ok and bool(failures),"failureKinds":sorted({r["kind"] for r in failures}),
                     "failedChecks":failures})

    base=cases["measure-base"]
    base_positions=[q["position"] for q in base["queries"]]
    base_ref=decimal_fields(base["sources"],base_positions)
    missing_v=copy.deepcopy(base)
    wrong_sources=copy.deepcopy(base["sources"])
    for s in wrong_sources:
        s["Gamma"]=[v/s["volume"] for v in s["Gamma"]]
    wrong_ref=decimal_fields(wrong_sources,base_positions,thermal=False)
    missing_v["output"]["velocity"]=wrong_ref["velocity"].tolist()
    missing_v["output"]["jacobian"]=wrong_ref["jacobian"].tolist()
    exercise("Gamma-omits-volume",lambda c:_check_output(c,base,base_ref),lambda c:_check_output(c,missing_v,base_ref))

    kernel=cases["kernel-analytic"]
    kernel_ref=decimal_fields(kernel["sources"],[q["position"] for q in kernel["queries"]])
    bad_j=copy.deepcopy(kernel)
    bad_j["output"]["jacobian"][0][0][1]*=-1
    exercise("Jacobian-cross-sign",lambda c:_check_output(c,kernel,kernel_ref),lambda c:_check_output(c,bad_j,kernel_ref))

    wrong_temp=copy.deepcopy(base)
    src=base["sources"]
    for qi,point in enumerate(base_positions):
        r=np.asarray(point)-np.asarray([s["position"] for s in src])
        sig=np.asarray([s["sigma"] for s in src])
        temp=np.asarray([s["temperature"] for s in src])
        # Deliberately omit sigma^-3 only; retain the common normalization.
        w=np.asarray([s["volume"] for s in src])*np.exp(-np.sum(r*r,axis=1)/(2*sig*sig))/(2*math.pi)**1.5
        den=math.fsum(w)
        num=math.fsum(w*temp)
        tbar=num/den
        grad=[math.fsum((temp-tbar)*(-r[:,k]/sig**2)*w)/den for k in range(3)]
        for key,value in (("temperature",tbar),("gradient",grad),("numerator",num),("denominator",den),("logDenominator",math.log(den))):
            wrong_temp["output"][key][qi]=value
    exercise("thermal-missing-sigma-normalization",lambda c:_check_output(c,base,base_ref),lambda c:_check_output(c,wrong_temp,base_ref))

    split=cases["measure-split2"]
    bad_split=copy.deepcopy(split["sources"])
    for s in bad_split:
        s["volume"]*=2
    expected=_measure_expected("measure-split2")
    exercise("split-does-not-divide-volume",lambda c:_compare_sources(c,"split-fixture",split["sources"],expected),
             lambda c:_compare_sources(c,"split-fixture",bad_split,expected))

    time_cases={k:cases[k] for k in CASE_IDS[15:]}
    wrong_time=copy.deepcopy(time_cases)
    for cid in CASE_IDS[18:]:
        case=wrong_time[cid]
        dt=case["dt"]
        for state in case["states"]:
            state["sources"][0]["position"][1]+=.25*dt*dt*state["step"]
        for output in case["stepOutputs"]:
            output["velocity"][0][1]+=.25*dt
    exercise("mean-position-uses-new-U",lambda c:_audit_time(c,time_cases,{}),lambda c:_audit_time(c,wrong_time,{}))

    positions=np.asarray([q["position"] for q in cases["field-n32"]["queries"]])
    r=positions-CENTER
    unfiltered=(.01/.1**2)*np.exp(-np.sum(r*r,axis=1)/(2*.1**2))[:,None]*np.column_stack((-r[:,1],r[:,0],np.zeros(len(r))))
    exercise("reference-incorrectly-unfiltered",lambda c:_check_filtered_reference(c,positions,filtered_field(positions)),
             lambda c:_check_filtered_reference(c,positions,unfiltered))
    return {"status":"passed" if all(r["passed"] for r in rows) else "failed","count":len(rows),"cases":rows,
            "scope":"Copied evidence/reference faults only; no new physical experiments and no production core import."}


def audit_cases(case_records, static_only=False):
    """Audit raw case records. Runner may call static gate without importing core here."""
    ch=Checks()
    diagnostics={}
    expected=STATIC_IDS if static_only else CASE_IDS
    try:
        ids=[c["id"] for c in case_records]
        ch.check("case-coverage",ids==expected,"execution",expected=expected,actual=ids)
        ch.check("raw-finite",_finite_tree(case_records),"execution")
        if not all(r["passed"] for r in ch.rows):
            raise ValueError("invalid coverage or nonfinite raw")
        cases={c["id"]:c for c in case_records}
        for cid,case in cases.items():
            index=CASE_IDS.index(cid)
            family="A" if index<7 else "B" if index<8 else "C" if index<12 else "D" if index<15 else "E" if index<18 else "F"
            ch.check(cid+"/family",case["family"]==family,"execution")
            ch.check(cid+"/inputUnchanged",case["inputUnchanged"] is True,"execution")
            if "sources" in case:
                _source_sanity(ch,cid,case["sources"])
            if "queries" in case:
                count={"sources":len(case["sources"]),"queries":len(case["queries"]),"sourceQueryPairs":len(case["sources"])*len(case["queries"])}
                ch.check(cid+"/counts",case["counts"]==count,"execution",recomputed=count)
                for key,val in _totals(case["sources"]).items():
                    ch.close(cid+"/raw-total-"+key,case["totals"][key],val)
        _audit_measure(ch,cases,diagnostics)
        _audit_kernel(ch,cases["kernel-analytic"],diagnostics)
        _audit_fields(ch,cases,diagnostics)
        if not static_only:
            _audit_temperature(ch,cases,diagnostics)
            _audit_time(ch,cases,diagnostics)
    except Exception as exc:
        ch.check("audit-exception",False,"execution",exceptionType=type(exc).__name__,message=str(exc))
    execution=all(r["passed"] for r in ch.rows if r["kind"]=="execution")
    physical=all(r["passed"] for r in ch.rows if r["kind"]=="physical")
    reference=all(r["passed"] for r in ch.rows if r["kind"]=="reference")
    return {"phase":"P5c","schemaVersion":1,"status":"passed" if execution and physical and reference else "failed",
            "staticOnly":bool(static_only),"executionValid":execution,"physicalContractPassed":physical and execution and reference,
            "referenceValid":reference,"caseCount":len(case_records),"checks":ch.rows,"diagnostics":diagnostics,
            "interpretation":"Standard direct-sum core correctness only; no MAC, boundary, combustion, long-time or novelty claim."}


def _main():
    parser=argparse.ArgumentParser()
    parser.add_argument("input",type=Path,help="cases.json or containing run directory")
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--static-only",action="store_true")
    parser.add_argument("--fault-injections",action="store_true",help="Append six copied-evidence fault checks; requires all 21 cases")
    parser.add_argument("--source-dir",type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument("--freeze",type=Path,help="Optional external frozen source SHA mapping")
    args=parser.parse_args()
    if args.out.exists():
        raise FileExistsError("audit output already exists; immutable evidence is never overwritten")
    path=args.input/"cases.json" if args.input.is_dir() else args.input
    def reject_constant(value):
        raise ValueError("nonfinite JSON constant: "+value)
    data=json.loads(path.read_text(encoding="utf-8-sig"),parse_constant=reject_constant)
    result=audit_cases(data["cases"],args.static_only)
    result["rawSha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
    result["auditorSha256"]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    provenance=Checks()
    provenance.check("raw-schema",data.get("phase")=="P5c" and data.get("schemaVersion")==1,"execution")
    manifest_path=path.parent/"manifest.json"
    if manifest_path.exists():
        manifest=json.loads(manifest_path.read_text(encoding="utf-8-sig"),parse_constant=reject_constant)
        provenance.check("manifest-schema",manifest.get("phase")=="P5c" and manifest.get("schemaVersion")==1,"execution")
        provenance.check("manifest-raw-sha",manifest["raw"]["sha256"]==result["rawSha256"],"execution")
        provenance.check("manifest-raw-size",manifest["raw"]["bytes"]==path.stat().st_size,"execution")
        provenance.check("manifest-case-coverage",[c["id"] for c in manifest["cases"]]==[c["id"] for c in data["cases"]],"execution")
        for raw,entry in zip(data["cases"],manifest["cases"]):
            encoded=json.dumps(raw,ensure_ascii=False,allow_nan=False,separators=(",",":")).encode("utf-8")
            provenance.check("record-sha/"+raw["id"],entry["recordSha256"]==hashlib.sha256(encoded).hexdigest() and entry["family"]==raw["family"],"execution")
        expected_names={"core.py","run.py","test_core.py","audit.py","PROTOCOL.md"}
        hashes=manifest["sourceHashes"]
        provenance.check("source-coverage",set(hashes)==expected_names,"execution")
        provenance.check("source-start-end",manifest.get("sourcesUnchanged") is True and hashes==manifest.get("sourceHashesAfter"),"execution")
        for name in sorted(expected_names):
            source=args.source_dir/name
            digest=hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else None
            provenance.check("source-sha/"+name,hashes.get(name)==digest,"execution",actualSha256=digest)
        if args.freeze:
            freeze=json.loads(args.freeze.read_text(encoding="utf-8-sig"),parse_constant=reject_constant)
            provenance.check("external-freeze",freeze.get("sourceHashes",freeze)==hashes,"execution")
            result["freezeSha256"]=hashlib.sha256(args.freeze.read_bytes()).hexdigest()
        result["manifestSha256"]=hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    else:
        provenance.check("manifest-present",False,"execution",reason="CLI saved-data audit requires manifest.json next to cases.json")
    result["provenanceChecks"]=provenance.rows
    if not all(row["passed"] for row in provenance.rows):
        result.update(executionValid=False,physicalContractPassed=False,status="failed")
    if args.fault_injections:
        if args.static_only:
            raise ValueError("fault suite requires complete 21-case evidence")
        result["faultInjections"]=fault_injections(data["cases"])
        if result["faultInjections"]["status"]!="passed":
            result.update(executionValid=False,physicalContractPassed=False,status="failed")
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("status","executionValid","physicalContractPassed","referenceValid","caseCount")},ensure_ascii=False))
    return 0 if result["status"]=="passed" else 1


if __name__=="__main__":
    raise SystemExit(_main())
