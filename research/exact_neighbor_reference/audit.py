"""Independent P6 all-pairs audit; never imports producer JavaScript code.

Only the compact-support gas-surface heat operator is evaluated here. There is
no full-frame, VPM, combustion, or novelty claim. Formal schema is frozen with
the producer before any formal execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

EPS = np.finfo(np.float64).eps
BOUNDARY_ULPS = 8
TEMPERATURE_ATOL = 1e-9
ENERGY_RTOL = 1e-12
SCALINGS = [(500, 10, 25), (5000, 50, 50), (50000, 100, 250)]
PATTERNS = ["smooth", "hotpatch", "checkerboard"]
PARAMS = {"h":.3,"beta":4,"dt":1/60,"safety":.9,"maxSubsteps":100000}
METHODS = ["allpairs-rebuild","hash-rebuild","hash-cached"]
ORDER = [METHODS,[METHODS[1],METHODS[2],METHODS[0]],
         [METHODS[2],METHODS[0],METHODS[1]],
         [METHODS[2],METHODS[1],METHODS[0]],
         [METHODS[0],METHODS[2],METHODS[1]]]
SOURCE_FILES = ["design.mjs","core.mjs","run.mjs","test.mjs","PROTOCOL.md",
                "audit.py","p4-thermal-reference.mjs"]
P4_REFERENCE_SHA = "73b367b9009c5fd36c92100eb8e40ac82ac2ab66e10e2b61acb395949f58aefe"


def definitions():
    return [{"id":f"s{n}-{pattern}","surfaceCount":n,"gasCount":600,
             "surfaceShape":[ny,nz],"pattern":pattern,"steps":1,"dt":1/60}
            for n,ny,nz in SCALINGS for pattern in PATTERNS]


def energy(temperature, capacity):
    return math.fsum(float(t)*float(c) for t,c in zip(temperature,capacity))


def geometry(surface_count):
    """Independently reconstruct the approved mid-point material quadrature."""
    matches=[row for row in SCALINGS if row[0]==surface_count]
    if len(matches)!=1:
        raise ValueError("unregistered surface resolution")
    _,ny,nz=matches[0]
    surface=np.array([[side,.1+(iy+.5)*.8/ny,-.4+(iz+.5)*.8/nz]
                      for side in (-.2,.2) for iy in range(ny) for iz in range(nz)],dtype=float)
    gas=np.array([[-.2+(ix+.5)*.4/10,.1+(iy+.5)*.8/10,-.4+(iz+.5)*.8/6]
                  for ix in range(10) for iy in range(10) for iz in range(6)],dtype=float)
    return {"surfacePosition":surface,"gasPosition":gas,
            "surfaceMeasure":np.full(surface_count,1.28/surface_count),
            "gasMeasure":np.full(600,.256/600),
            "surfaceCapacity":np.full(surface_count,(1.28/surface_count)*2),
            "gasCapacity":np.full(600,(.256/600)*3)}


def temperatures(pattern,surface,gas):
    if pattern=="smooth":
        ts=320+40*(surface[:,1]-.1)/.8+20*(surface[:,2]+.4)/.8
        tg=600+80*(gas[:,0]+.2)/.4+60*(gas[:,1]-.1)/.8-40*(gas[:,2]+.4)/.8
    elif pattern=="hotpatch":
        ts=np.full(len(surface),300.)
        r2=(gas[:,0]*gas[:,0]+(gas[:,1]-.5)*(gas[:,1]-.5))+gas[:,2]*gas[:,2]
        tg=np.where(r2<.12*.12,900.,300.)
    elif pattern=="checkerboard":
        def checker(p):
            cells=(np.floor((p[:,0]+.017)/.125)+np.floor((p[:,1]+.031)/.125))+np.floor((p[:,2]+.047)/.125)
            return 300+500*np.mod(cells,2)
        ts,tg=checker(surface),checker(gas)
    else:
        raise ValueError("unregistered temperature pattern")
    return ts,tg


def hash_candidates(surface,gas,h):
    """Independent bucket population count; no producer search code or neighbors."""
    cells=np.floor(gas/h).astype(np.int64)
    populations={}
    for cell in cells:
        key=tuple(int(x) for x in cell)
        populations[key]=populations.get(key,0)+1
    total=0; cache={}
    for cell in np.floor(surface/h).astype(np.int64):
        key=tuple(int(v) for v in cell)
        if key not in cache:
            cache[key]=sum(populations.get((key[0]+dx,key[1]+dy,key[2]+dz),0)
                           for dx in (-1,0,1) for dy in (-1,0,1) for dz in (-1,0,1))
        total+=cache[key]
    return {"candidatePairsPerPass":total,"distanceEvaluations":2*total,
            "indexedGasNodes":len(gas),"occupiedBuckets":len(populations),
            "bucketLookups":27*len(cache),"candidateCacheCells":len(cache),
            "candidateCacheEntries":sum(cache.values()),"candidateCacheHits":2*len(surface)-len(cache)}


def pair_chunks(surface,gas,area,volume,h,beta,chunk_size=256):
    """All pairs, with explicit left-associated squares and no spatial search."""
    normalization=3/(math.pi*h*h*h)
    for start in range(0,len(surface),chunk_size):
        stop=min(start+chunk_size,len(surface))
        delta=surface[start:stop,None,:]-gas[None,:,:]
        radius=np.sqrt((delta[:,:,0]*delta[:,:,0]+delta[:,:,1]*delta[:,:,1])+delta[:,:,2]*delta[:,:,2])
        inside=radius<h
        band=np.abs(radius-h)<=BOUNDARY_ULPS*EPS*np.maximum(h,radius)
        conductance=((beta*area[start:stop,None])*volume[None,:])*(normalization*np.maximum(0.,1-radius/h))
        conductance=np.where(inside,conductance,0.)
        yield start,stop,inside,band,conductance


def allpairs_graph(surface,gas,area,volume,surface_capacity,gas_capacity,h,beta):
    ns,ng=len(surface),len(gas)
    sum_s=np.zeros(ns); sum_g=np.zeros(ng)
    degree_s=np.zeros(ns,dtype=np.int64); degree_g=np.zeros(ng,dtype=np.int64)
    strict_s=np.zeros(ns,dtype=np.int64); strict_g=np.zeros(ng,dtype=np.int64)
    boundary_s=np.zeros(ns,dtype=np.int64); boundary_g=np.zeros(ng,dtype=np.int64)
    boundary_pairs=0; boundary_weight=0.; boundary_max_g=0.; topology_fragments=[]
    for start,stop,inside,band,G in pair_chunks(surface,gas,area,volume,h,beta):
        sum_s[start:stop]=np.sum(G,axis=1)
        sum_g+=np.sum(G,axis=0)
        degree_s[start:stop]=np.sum(inside,axis=1)
        degree_g+=np.sum(inside,axis=0)
        # np.nonzero traverses rows then columns, independently constructing CSR.
        topology_fragments.append(np.nonzero(inside)[1].astype("<u4"))
        strict=inside & ~band
        strict_s[start:stop]=np.sum(strict,axis=1)
        strict_g+=np.sum(strict,axis=0)
        boundary_s[start:stop]=np.sum(band,axis=1)
        boundary_g+=np.sum(band,axis=0)
        boundary_pairs+=int(np.sum(band))
        boundary_weight+=math.fsum(G[band])
        boundary_max_g=max(boundary_max_g,float(np.max(G[band])) if np.any(band) else 0.)
    max_rate=max(float(np.max(sum_s/surface_capacity)),float(np.max(sum_g/gas_capacity)))
    offsets=np.zeros(ns+1,dtype="<u4")
    if int(np.sum(degree_s))>0xffffffff: raise ValueError("independent CSR exceeds uint32")
    offsets[1:]=np.cumsum(degree_s,dtype=np.uint64)
    topology_hash=hashlib.sha256(offsets.tobytes())
    for fragment in topology_fragments: topology_hash.update(fragment.tobytes())
    return {"surfaceSumG":sum_s,"gasSumG":sum_g,"surfaceDegree":degree_s,"gasDegree":degree_g,
            "surfaceStrictDegree":strict_s,"gasStrictDegree":strict_g,
            "surfaceBoundaryPairs":boundary_s,"gasBoundaryPairs":boundary_g,
            "edgeCount":int(np.sum(degree_s)),"strictEdgeCount":int(np.sum(strict_s)),
            "boundaryPairs":boundary_pairs,"boundaryConductance":boundary_weight,
            "boundaryMaxConductance":boundary_max_g,"maxRate":max_rate,"topologySHA256":topology_hash.hexdigest(),
            "boundaryDefinition":"abs(r-h) <= 8 * float64_epsilon * max(h,r); diagnostic only; exact topology SHA remains required even in this band"}


def allpairs_step(surface,gas,area,volume,surface_capacity,gas_capacity,Ts,Tg,h,beta,dt,safety,graph=None):
    if graph is None:
        graph=allpairs_graph(surface,gas,area,volume,surface_capacity,gas_capacity,h,beta)
    count=max(1,math.ceil(dt*graph["maxRate"]/safety))
    sub_dt=dt/count
    ts,tg=np.asarray(Ts,float).copy(),np.asarray(Tg,float).copy()
    before_s,before_g=energy(ts,surface_capacity),energy(tg,gas_capacity)
    net_s,net_g=0.,0.
    for _ in range(count):
        ds=np.zeros(len(ts)); dg=np.zeros(len(tg))
        for start,stop,inside,band,G in pair_chunks(surface,gas,area,volume,h,beta):
            Q=sub_dt*G*(tg[None,:]-ts[start:stop,None])
            ds[start:stop]=np.sum(Q,axis=1)
            dg-=np.sum(Q,axis=0)
        # Every pair flux has been computed using the same old temperature state.
        ts=ts+ds/surface_capacity
        tg=tg+dg/gas_capacity
        net_s+=math.fsum(ds); net_g+=math.fsum(dg)
    after_s,after_g=energy(ts,surface_capacity),energy(tg,gas_capacity)
    return {"surfaceTemperature":ts,"gasTemperature":tg,"substeps":count,"substepDt":sub_dt,
            "maxCfl":sub_dt*graph["maxRate"],"edgeEvaluations":count*graph["edgeCount"],
            "energyBefore":{"surface":before_s,"gas":before_g,"total":before_s+before_g},
            "energyAfter":{"surface":after_s,"gas":after_g,"total":after_s+after_g},
            "netSurface":net_s,"netGas":net_g,"energyResidual":(after_s+after_g)-(before_s+before_g)}


class Checks:
    def __init__(self):
        self.rows=[]

    def check(self,name,passed,**details):
        self.rows.append({"name":name,"passed":bool(passed),**details})

    def close(self,name,actual,expected,atol=1e-12,rtol=1e-12):
        a,b=np.asarray(actual,float),np.asarray(expected,float)
        if a.shape!=b.shape or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
            self.check(name,False,reason="shape or finite values",actualShape=list(a.shape),expectedShape=list(b.shape)); return
        err=np.abs(a-b); lim=atol+rtol*np.maximum(np.abs(a),np.abs(b))
        ratio=np.divide(err,lim,out=np.zeros_like(err),where=lim>0)
        self.check(name,bool(np.all(err<=lim)),maxAbsError=float(np.max(err)) if err.size else 0.,
                   maxToleranceRatio=float(np.max(ratio)) if err.size else 0.,
                   exactMismatches=int(np.sum((lim==0)&(err!=0))))


def _json(path):
    def invalid(value):
        raise ValueError("nonfinite JSON constant "+value)
    return json.loads(Path(path).read_text(encoding="utf-8-sig"),parse_constant=invalid)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def float64_sha(values):
    return sha256(np.asarray(values,dtype="<f8").tobytes(order="C"))


def property_lexeme(text,name):
    """Extract a top-level JSON value without reformatting floating-point text."""
    decoder=json.JSONDecoder()
    def skip(i):
        while i<len(text) and text[i].isspace(): i+=1
        return i
    i=skip(0)
    if text[i]!="{": raise ValueError("raw case must be a JSON object")
    i+=1; found=[]
    while True:
        i=skip(i)
        if text[i]=="}": break
        key,i=decoder.raw_decode(text,i); i=skip(i)
        if text[i]!=":": raise ValueError("invalid object separator")
        start=skip(i+1); _,end=decoder.raw_decode(text,start)
        if key==name: found.append(text[start:end])
        i=skip(end)
        if text[i]=="}": break
        if text[i]!=",": raise ValueError("invalid object separator")
        i+=1
    if len(found)!=1: raise ValueError(f"expected one top-level {name}")
    return found[0]


def compact_lexeme(text):
    """Remove formatting whitespace only; keep every number and string lexeme."""
    out=[]; quoted=False; escaped=False
    for char in text:
        if quoted:
            out.append(char)
            if escaped: escaped=False
            elif char=="\\": escaped=True
            elif char=='"': quoted=False
        elif char=='"': quoted=True; out.append(char)
        elif not char.isspace(): out.append(char)
    if quoted: raise ValueError("unterminated JSON string")
    return "".join(out)


def _finite_tree(value):
    if isinstance(value,float): return math.isfinite(value)
    if isinstance(value,dict): return all(_finite_tree(v) for v in value.values())
    if isinstance(value,list): return all(_finite_tree(v) for v in value)
    return True


def _relative_check(checks,name,actual,expected,scale):
    a,b=np.asarray(actual,float),np.asarray(expected,float)
    valid=a.shape==b.shape and np.all(np.isfinite(a)) and np.all(np.isfinite(b))
    error=float(np.max(np.abs(a-b))) if valid and a.size else (0. if valid else None)
    checks.check(name,valid and error<=ENERGY_RTOL*scale,
                 maxAbsoluteError=error,scale=float(scale),relativeTolerance=ENERGY_RTOL)


def audit_fixture(raw,definition,text,checks):
    prefix=definition["id"]
    checks.check(prefix+":case-schema",raw.get("version")==1 and raw.get("id")==prefix
                 and raw.get("definition")==definition and raw.get("params")==PARAMS
                 and raw.get("executionValid") is True and raw.get("crossMethodExact") is True)
    checks.check(prefix+":all-json-finite",_finite_tree(raw))
    authored=raw["input"]; ns=definition["surfaceCount"]; n=ns+600
    nodes=authored["nodes"]
    if authored.get("surfaceCount")!=ns or len(nodes)!=n: raise ValueError("node coverage mismatch")
    _,ny,nz=next(row for row in SCALINGS if row[0]==ns)
    ids=[f"s-{side}-{iy}-{iz}" for side in range(2) for iy in range(ny) for iz in range(nz)]
    ids += [f"g-{ix}-{iy}-{iz}" for ix in range(10) for iy in range(10) for iz in range(6)]
    checks.check(prefix+":ids-kind-order",[v["id"] for v in nodes]==ids
                 and [v["kind"] for v in nodes]==["surface"]*ns+["gas"]*600)
    expected=geometry(ns)
    p=np.asarray([v["position"] for v in nodes],float)
    measure=np.asarray([v["measure"] for v in nodes],float)
    density=np.asarray([v["capacityPerMeasure"] for v in nodes],float)
    capacity=np.asarray([v["capacity"] for v in nodes],float)
    temperature=np.asarray([v["temperature"] for v in nodes],float)
    checks.close(prefix+":fixture-position",p,np.vstack([expected["surfacePosition"],expected["gasPosition"]]),atol=2e-15,rtol=0.)
    checks.close(prefix+":fixture-measure",measure,np.r_[expected["surfaceMeasure"],expected["gasMeasure"]],atol=0.,rtol=1e-14)
    checks.close(prefix+":fixture-capacity-density",density,np.r_[np.full(ns,2),np.full(600,3)],atol=0.,rtol=0.)
    checks.close(prefix+":fixture-capacity",capacity,measure*density,atol=0.,rtol=1e-14)
    ts,tg=temperatures(definition["pattern"],expected["surfacePosition"],expected["gasPosition"])
    checks.close(prefix+":fixture-temperature",temperature,np.r_[ts,tg],atol=1e-12,rtol=0.)
    input_hash=sha256(compact_lexeme(property_lexeme(text,"input")).encode("utf-8"))
    checks.check(prefix+":input-preserved-lexical-sha",input_hash==raw.get("inputSHA256")==raw.get("inputSHA256After")
                 and raw.get("inputUnchanged") is True)
    checks.check(prefix+":positive-measures-capacities",bool(np.all(measure>0) and np.all(capacity>0)
                 and np.all(temperature>=0)))
    return {"surface":p[:ns],"gas":p[ns:],"area":measure[:ns],"volume":measure[ns:],
            "surfaceCapacity":capacity[:ns],"gasCapacity":capacity[ns:],
            "surfaceTemperature":temperature[:ns],"gasTemperature":temperature[ns:],"inputSHA256":input_hash}


def audit_small_edges(raw_graph,fixture,reference,prefix,checks):
    surface,gas=fixture["surface"],fixture["gas"]
    ns,ng=len(surface),len(gas); edges=np.asarray(raw_graph["edges"],float)
    if edges.shape!=(raw_graph["edgeCount"],3): raise ValueError("small edge coverage")
    i=edges[:,0].astype(np.int64); j=edges[:,1].astype(np.int64)-ns
    valid=bool(np.all(edges[:,0]==i) and np.all(edges[:,1]==j+ns)
               and np.all((i>=0)&(i<ns)) and np.all((j>=0)&(j<ng)))
    checks.check(prefix+":edge-integer-bounds",valid)
    if not valid: raise ValueError("invalid edge indices")
    code=i*ng+j
    checks.check(prefix+":edge-canonical-order",bool(np.all(code[1:]>code[:-1])))
    actual=np.zeros((ns,ng),bool); actual[i,j]=True
    weights=np.zeros((ns,ng),float); weights[i,j]=edges[:,2]
    boundary_mismatches=0; offband_mismatches=0; maximum_g_error=0.
    for start,stop,inside,band,G in pair_chunks(surface,gas,fixture["area"],fixture["volume"],PARAMS["h"],PARAMS["beta"]):
        mismatch=actual[start:stop]!=inside
        offband_mismatches+=int(np.sum(mismatch & ~band)); boundary_mismatches+=int(np.sum(mismatch & band))
        maximum_g_error=max(maximum_g_error,float(np.max(np.abs(weights[start:stop]-G))))
        checks.close(prefix+f":edge-conductance-{start}",weights[start:stop],G,atol=1e-15,rtol=1e-12)
    checks.check(prefix+":edge-offband-topology",offband_mismatches==0,
                 offBandMismatches=offband_mismatches,boundaryMismatches=boundary_mismatches)
    rows=np.zeros(ns+1,dtype="<u4"); rows[1:]=np.cumsum(np.bincount(i,minlength=ns),dtype=np.uint64)
    digest=hashlib.sha256()
    for array in (rows,j.astype("<u4"),edges[:,2].astype("<f8")): digest.update(array.tobytes())
    checks.check(prefix+":saved-csr-binary-sha",digest.hexdigest()==raw_graph["sha256"])
    return {"storedEdges":len(edges),"offBandTopologyMismatches":offband_mismatches,
            "boundaryTopologyMismatches":boundary_mismatches,"maxConductanceError":maximum_g_error}


def audit_timing(method,prefix,checks):
    repeats=method["repeats"]; keys=["indexBuildMs","countPassMs","fillAndDegreeMs","buildMs",
                                  "buildSetupMs","exchangeMs","totalWithSetupMs","applicationMs"]
    checks.check(prefix+":five-trials",len(repeats)==5 and [r.get("repeat") for r in repeats]==list(range(5)))
    if len(repeats)!=5: raise ValueError("missing timing trials")
    rows=[]
    for k,row in enumerate(repeats):
        name=prefix+f":trial{k}"; t=row["timing"]
        checks.check(name+":order",row.get("orderIndex")==ORDER[k].index(method["id"]))
        checks.check(name+":finite-nonnegative",all(isinstance(t.get(key),(int,float))
                     and not isinstance(t.get(key),bool) and math.isfinite(t[key]) and t[key]>=0 for key in keys))
        checks.check(name+":unchanged-graph-temperature-ledger",row.get("graphSHA256")==method["graph"]["sha256"]
                     and row.get("topologySHA256")==method["graph"]["topologySHA256"]
                     and row.get("temperatureSHA256")==method["temperatureSHA256"] and row.get("ledger")==method["ledger"])
        checks.close(name+":total-identity",t["totalWithSetupMs"],t["buildSetupMs"]+t["exchangeMs"],atol=1e-8,rtol=1e-12)
        checks.close(name+":build-stages",t["buildMs"],t["indexBuildMs"]+t["countPassMs"]+t["fillAndDegreeMs"],atol=1e-8,rtol=1e-12)
        checks.check(name+":build-contained",t["buildMs"]<=t["buildSetupMs"]+1e-8)
        expected=t["exchangeMs"] if method["id"]=="hash-cached" else t["totalWithSetupMs"]
        checks.close(name+":application-scope",t["applicationMs"],expected,atol=0.,rtol=0.)
        rows.append({"repeat":k,"orderIndex":row["orderIndex"],**{key:t[key] for key in keys}})
    for key in ("applicationMs","buildSetupMs","exchangeMs","totalWithSetupMs"):
        values=sorted(row["timing"][key] for row in repeats)
        expected={"median":values[2],"p95FloorIndex":values[3],"min":values[0],"max":values[4]}
        checks.check(prefix+":summary-"+key,method["timingSummary"][key]==expected)
    return {"method":method["id"],"trials":rows,"summary":method["timingSummary"],
            "interpretation":"Five within-process fresh-state trials, not independent process repetitions; no full-system speed or confidence claim."}


def audit_case(raw,definition,text,checks):
    case_id=definition["id"]
    f=audit_fixture(raw,definition,text,checks); ns=len(f["surface"]); ng=len(f["gas"]); n=ns+ng
    ref=allpairs_graph(f["surface"],f["gas"],f["area"],f["volume"],f["surfaceCapacity"],f["gasCapacity"],.3,4)
    step=allpairs_step(f["surface"],f["gas"],f["area"],f["volume"],f["surfaceCapacity"],f["gasCapacity"],
                      f["surfaceTemperature"],f["gasTemperature"],.3,4,1/60,.9,ref)
    ref_T=np.r_[step["surfaceTemperature"],step["gasTemperature"]]
    capacity=np.r_[f["surfaceCapacity"],f["gasCapacity"]]
    initial=np.r_[f["surfaceTemperature"],f["gasTemperature"]]
    ref_sum=np.r_[ref["surfaceSumG"],ref["gasSumG"]]
    ref_degree=np.r_[ref["surfaceDegree"],ref["gasDegree"]]
    strict_degree=np.r_[ref["surfaceStrictDegree"],ref["gasStrictDegree"]]
    band_degree=np.r_[ref["surfaceBoundaryPairs"],ref["gasBoundaryPairs"]]
    e_scale=max(1.,abs(step["energyBefore"]["total"]))
    hash_work=hash_candidates(f["surface"],f["gas"],.3)
    methods=raw["methods"]
    checks.check(case_id+":method-coverage",[m.get("id") for m in methods]==METHODS)
    if len(methods)!=3: raise ValueError("missing method")
    method_rows=[]; timing_rows=[]
    for method in methods:
        name=case_id+":"+method["id"]; graph=method["graph"]; ledger=method["ledger"]
        neighbor=np.asarray(graph["neighborCount"],float); sum_g=np.asarray(graph["sumG"],float)
        if neighbor.shape!=(n,) or sum_g.shape!=(n,): raise ValueError("node graph coverage")
        checks.check(name+":neighbor-integer",bool(np.all(neighbor==np.floor(neighbor)) and np.all(neighbor>=0)))
        checks.check(name+":independent-exact-topology-sha",graph.get("topologySHA256")==ref["topologySHA256"],
                     expected=ref["topologySHA256"],actual=graph.get("topologySHA256"),boundaryIsNotExemption=True)
        checks.check(name+":exact-neighbor-count",bool(np.array_equal(neighbor,ref_degree)))
        checks.check(name+":offband-neighbor-count",bool(np.all(neighbor>=strict_degree)
                     and np.all(neighbor<=strict_degree+band_degree)),exactCountMismatches=int(np.sum(neighbor!=ref_degree)))
        checks.check(name+":edge-count-and-incidence",graph["edgeCount"]==ref["edgeCount"]
                     and int(np.sum(neighbor[:ns]))==graph["edgeCount"]==int(np.sum(neighbor[ns:])),
                     expectedStrictEdgeCount=ref["strictEdgeCount"],expectedCanonicalEdgeCount=ref["edgeCount"],boundaryPairs=ref["boundaryPairs"])
        degree_error=np.abs(sum_g-ref_sum); degree_scale=np.maximum(1.,np.abs(ref_sum))
        checks.check(name+":degree-conductance",bool(np.all(degree_error<=1e-12*degree_scale)),
                     maxAbsoluteError=float(np.max(degree_error)),maxScaledError=float(np.max(degree_error/degree_scale)))
        checks.close(name+":max-rate",graph["maxRate"],ref["maxRate"],atol=1e-12,rtol=1e-12)
        checks.close(name+":internal-max-rate",graph["maxRate"],float(np.max(sum_g/capacity)),atol=0.,rtol=0.)
        work=graph["work"]; expected_work={"candidatePairsPerPass":ns*ng,"distanceEvaluations":2*ns*ng,
            "indexedGasNodes":0,"occupiedBuckets":0,"bucketLookups":0,"candidateCacheCells":0,
            "candidateCacheEntries":0,"candidateCacheHits":0} if method["id"]=="allpairs-rebuild" else hash_work
        for key,value in expected_work.items(): checks.check(name+":work-"+key,work.get(key)==value,expected=value,actual=work.get(key))
        checks.check(name+":work-edge-boundary",work["conductanceEvaluations"]==graph["edgeCount"]
                     and work["boundaryPairs"]==ref["boundaryPairs"])
        checks.close(name+":boundary-conductance",work["boundaryConductance"],ref["boundaryConductance"],atol=1e-15,rtol=1e-12)
        memory=graph["memory"]; is_hash=method["id"]!="allpairs-rebuild"
        expected_memory={"graphTypedArrayBytes":4*(ns+1)+12*graph["edgeCount"]+12*n,
                         "candidateScratchBytes":4*ng,"candidateCacheTypedArrayBytes":4*expected_work["candidateCacheEntries"],
                         "indexEntries":ng if is_hash else 0,"indexBuckets":hash_work["occupiedBuckets"] if is_hash else 0,
                         "indexHeapBytes":None}
        checks.check(name+":memory-payload",all(memory.get(key)==value for key,value in expected_memory.items()))
        edges=audit_small_edges(graph,f,ref,name,checks) if ns==500 else None
        if ns!=500: checks.check(name+":large-edges-omitted",graph.get("edges") is None)
        final=np.asarray(method["finalTemperatures"],float)
        checks.close(name+":independent-synchronous-temperature",final,ref_T,atol=TEMPERATURE_ATOL,rtol=0.)
        checks.check(name+":temperature-binary-sha",float64_sha(final)==method["temperatureSHA256"])
        checks.check(name+":maximum-principle",bool(np.all(np.isfinite(final))
                     and np.min(final)>=np.min(initial)-TEMPERATURE_ATOL and np.max(final)<=np.max(initial)+TEMPERATURE_ATOL),
                     initialRange=[float(np.min(initial)),float(np.max(initial))],finalRange=[float(np.min(final)),float(np.max(final))])
        checks.check(name+":ledger-discrete-schedule",ledger["dt"]==1/60 and ledger["safety"]==.9
                     and ledger["substeps"]==step["substeps"] and ledger["edgeEvaluations"]==ledger["substeps"]*graph["edgeCount"]
                     and ledger["workspaceTypedArrayBytes"]==16*n)
        for key in ("substepDt","maxCfl"):
            checks.close(name+":ledger-"+key,ledger[key],step[key],atol=1e-12,rtol=1e-12)
        checks.close(name+":ledger-rate",ledger["maxRate"],graph["maxRate"],atol=0.,rtol=0.)
        checks.check(name+":cfl-stability",ledger["maxCfl"]<=.9+1e-12 and 1<=ledger["substeps"]<=100000)
        actual_after={"surface":energy(final[:ns],capacity[:ns]),"gas":energy(final[ns:],capacity[ns:])}
        actual_after["total"]=actual_after["surface"]+actual_after["gas"]
        for part in ("surface","gas","total"):
            _relative_check(checks,name+":energy-before-"+part,ledger["Ebefore"][part],step["energyBefore"][part],e_scale)
            _relative_check(checks,name+":energy-after-actual-"+part,ledger["Eafter"][part],actual_after[part],e_scale)
            _relative_check(checks,name+":energy-after-reference-"+part,ledger["Eafter"][part],step["energyAfter"][part],e_scale)
        changes={part:actual_after[part]-step["energyBefore"][part] for part in ("surface","gas","total")}
        for part in ("Surface","Gas"):
            low=part.lower()
            _relative_check(checks,name+":flux-reference-"+low,ledger["net"+part],step["net"+part],e_scale)
            _relative_check(checks,name+":debit-credit-"+low,changes[low],ledger["net"+part],e_scale)
            _relative_check(checks,name+":energy-change-"+low,ledger["energyChange"+part],changes[low],e_scale)
        _relative_check(checks,name+":opposite-flux",ledger["netSurface"]+ledger["netGas"],0.,e_scale)
        _relative_check(checks,name+":actual-energy-conservation",changes["total"],0.,e_scale)
        _relative_check(checks,name+":energy-residual-ledger",ledger["energyResidual"],changes["total"],e_scale)
        timing_rows.append(audit_timing(method,name,checks))
        method_rows.append({"id":method["id"],"edgeCount":graph["edgeCount"],"maxRate":graph["maxRate"],
            "substeps":ledger["substeps"],"maxCfl":ledger["maxCfl"],"graphSHA256":graph["sha256"],
            "topologySHA256":graph["topologySHA256"],
            "temperatureSHA256":method["temperatureSHA256"],"maxTemperatureError":float(np.max(np.abs(final-ref_T))),
            "relativeEnergyDrift":abs(changes["total"])/e_scale,"relativeOppositeFluxError":abs(ledger["netSurface"]+ledger["netGas"])/e_scale,
            "maxDegreeScaledError":float(np.max(degree_error/degree_scale)),"work":work,"memory":memory,
            "workspaceTypedArrayBytes":ledger["workspaceTypedArrayBytes"],"smallEdgeAudit":edges,"timingSummary":method["timingSummary"]})
    baseline=methods[0]
    checks.check(case_id+":actual-cross-method-exact",all(m["graph"]["sha256"]==baseline["graph"]["sha256"]
                 and m["graph"]["topologySHA256"]==baseline["graph"]["topologySHA256"]
                 and m["temperatureSHA256"]==baseline["temperatureSHA256"] and m["ledger"]==baseline["ledger"]
                 and m["finalTemperatures"]==baseline["finalTemperatures"] and m["graph"]["sumG"]==baseline["graph"]["sumG"]
                 and m["graph"]["neighborCount"]==baseline["graph"]["neighborCount"] for m in methods))
    return {"id":case_id,"surfaceCount":ns,"gasCount":ng,"pattern":definition["pattern"],"inputSHA256":f["inputSHA256"],
        "coverage":{"allPairsEnumeratedForGraph":ns*ng,"allPairsEnumeratedForHeat":ns*ng*step["substeps"],
                    "finalTemperaturesPerMethod":n,"methods":3,"inProcessTrials":15},
        "reference":{"edgeCount":ref["edgeCount"],"strictEdgeCount":ref["strictEdgeCount"],"maxRate":ref["maxRate"],
                     "topologySHA256":ref["topologySHA256"],
                     "substeps":step["substeps"],"boundaryPairs":ref["boundaryPairs"],"boundaryConductance":ref["boundaryConductance"],
                     "boundaryMaxConductance":ref["boundaryMaxConductance"],"boundaryDefinition":ref["boundaryDefinition"]},
        "methods":method_rows,"timing":timing_rows}


def source_hashes(source_dir):
    return {name:sha256((Path(source_dir)/name).read_bytes()) for name in SOURCE_FILES}


def audit_run(run_dir,source_dir,freeze_path):
    run_dir=Path(run_dir); source_dir=Path(source_dir); checks=Checks()
    manifest_path=run_dir/"manifest.json"; manifest_start_sha=sha256(manifest_path.read_bytes()); manifest=_json(manifest_path)
    freeze_start_sha=sha256(Path(freeze_path).read_bytes())
    frozen=_json(freeze_path); frozen=frozen.get("sourceHashes",frozen)
    before=source_hashes(source_dir)
    checks.check("exact-source-coverage",list(manifest["sourceHashes"])==SOURCE_FILES and set(frozen)==set(SOURCE_FILES))
    checks.check("frozen-sources-before",before==frozen==manifest["sourceHashes"]==manifest.get("sourceHashesAfter"))
    checks.check("p4-reference-pin",before["p4-thermal-reference.mjs"]==P4_REFERENCE_SHA)
    checks.check("formal-manifest",manifest.get("phase")=="P6-exact-neighbor-cost" and manifest.get("version")==1
                 and manifest.get("formal") is True and manifest.get("status")=="completed-pending-independent-audit"
                 and manifest.get("protocolComplete") is True and manifest.get("executionValid") is True
                 and manifest.get("sourcesUnchanged") is True and manifest.get("independentAudit")=="pending")
    planned=definitions(); checks.check("exact-planned-fixtures",manifest.get("planned")==planned and manifest.get("params")==PARAMS)
    checks.check("exact-case-coverage",[r.get("id") for r in manifest["cases"]]==[d["id"] for d in planned])
    timing=manifest["timing"]
    checks.check("timing-protocol",timing.get("repeats")==5 and timing.get("warmupsPerMethodPerCase")==1 and timing.get("order")==ORDER
                 and timing.get("inputPacking")=="outside" and timing.get("inputTemperatureReset")=="outside"
                 and timing.get("exchangeScratchAllocation")=="inside" and timing.get("buildAllocation")=="inside buildSetupMs"
                 and timing.get("hashesAndSerialization")=="outside")
    checks.check("little-endian-record",manifest.get("host",{}).get("endianness")=="LE")
    results=[]; filenames=[]
    for definition,record in zip(planned,manifest["cases"]):
        name=definition["id"]; filename=name+".json"
        checks.check(name+":raw-path",record.get("path")==filename)
        path=run_dir/filename; filenames.append(filename)
        data=path.read_bytes()
        checks.check(name+":raw-file-authentication",len(data)==record.get("bytes") and sha256(data)==record.get("sha256"))
        try:
            raw=_json(path); text=data.decode("utf-8-sig")
            results.append(audit_case(raw,definition,text,checks))
        except (KeyError,TypeError,ValueError,OverflowError,IndexError) as error:
            checks.check(name+":complete-independent-audit",False,error=f"{type(error).__name__}: {error}")
    checks.check("all-nine-independent-results",len(results)==9)
    checks.check("no-unlisted-case-files",sorted(p.name for p in run_dir.glob("s*-*.json"))==sorted(filenames))
    after=source_hashes(source_dir); checks.check("source-stable-during-audit",after==before==frozen)
    checks.check("manifest-stable-during-audit",sha256(manifest_path.read_bytes())==manifest_start_sha)
    checks.check("freeze-stable-during-audit",sha256(Path(freeze_path).read_bytes())==freeze_start_sha)
    for record in manifest["cases"]:
        path=run_dir/record["path"]
        checks.check(record["id"]+":raw-stable-during-audit",sha256(path.read_bytes())==record["sha256"])
    failed=[row for row in checks.rows if not row["passed"]]
    return {"phase":"P6-exact-neighbor-cost","status":"passed" if not failed else "failed",
        "independentCorrectnessPassed":not failed,"executionEvidenceValid":not failed,
        "sourceHashes":before,"sourceHashesAfter":after,"freezeSHA256":freeze_start_sha,
        "manifestSHA256":manifest_start_sha,"host":manifest["host"],"measurementContract":timing,
        "interpretation":"Standard exact compact-support heat exchange only. Timing trials repeat within one Node process; no new-method, rendering, full-frame speed, continuum accuracy, or independent-process claim.",
        "tolerances":{"temperatureAbsoluteK":TEMPERATURE_ATOL,"energyRelative":ENERGY_RTOL,
                      "energyScale":"max(1 J, abs(initial energy))","degreeRelative":1e-12,
                      "degreeScale":"max(1 W/K, abs(reference degree))","supportBoundaryUlps":BOUNDARY_ULPS,
                      "boundaryQualification":"Diagnostic band only; exact independent topology SHA and all numerical tolerances remain mandatory. A mismatch is not excused as roundoff."},
        "counts":{"expectedCases":9,"auditedCases":len(results),"methods":sum(len(r["methods"]) for r in results),
                  "inProcessTimingTrials":sum(r["coverage"]["inProcessTrials"] for r in results),
                  "allPairsForGraph":sum(r["coverage"]["allPairsEnumeratedForGraph"] for r in results),
                  "allPairsForHeat":sum(r["coverage"]["allPairsEnumeratedForHeat"] for r in results),
                  "finalTemperatureComponentsAcrossMethods":sum(3*r["coverage"]["finalTemperaturesPerMethod"] for r in results)},
        "cases":results,"checks":checks.rows,"failedChecks":failed}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run",type=Path)
    parser.add_argument("--source-dir",type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument("--freeze",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args(argv)
    if args.out.exists(): parser.error("audit output already exists; use a fresh path")
    report=audit_run(args.run,args.source_dir,args.freeze)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"counts":report["counts"],"failedChecks":len(report["failedChecks"])}))
    return 0 if report["independentCorrectnessPassed"] else 1


if __name__=="__main__":
    sys.exit(main())

