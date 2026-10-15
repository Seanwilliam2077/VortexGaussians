"""Independent P7 audit. No producer import and no physical replay claim beyond
the five preregistered steps of each completed arm. Every archived state,
observable, conditional decision, and reported timing is separately checked.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

CONFIG={"h":.12,"beta":2,"safety":.9,"maxSubsteps":100000,"horizon":1,
        "displayN":64,"ambient":300,"Omega":math.pi/2,"U":.4}
DEFINITIONS=[
    {"id":"dev-ref128-r120","n":128,"rate":120,"role":"R0"},
    {"id":"dev-ref128-r240","n":128,"rate":240,"role":"R1"},
    {"id":"dev-ref256-r240","n":256,"rate":240,"role":"R2"},
    {"id":"dev-ref256-r480","n":256,"rate":480,"role":"R3","conditional":True},
    {"id":"dev-shared64-r120","n":64,"rate":120,"role":"shared"},
    {"id":"dev-proxy16-r120","n":16,"rate":120,"role":"proxy"},
]
SOURCE_FILES=["design.mjs","wrapper.mjs","metrics.mjs","run.mjs","test.mjs",
              "p6-core.mjs","PROTOCOL.md","audit.py"]
CORE_SHA256="8434987b77928c4346b73ecd9fee88cbbb4c7444d232f9cfd34c4f652019a5fc"
TIMING_ORDER=[["shared","proxy"] if k%2==0 else ["proxy","shared"] for k in range(6)]
TEMP_ATOL=1e-9
POSITION_ATOL=2e-14
ENERGY_RTOL=1e-12
SHARED_VISUAL_ALIAS_BYTES=8192*3*8


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    digest=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):
            digest.update(chunk)
    return digest.hexdigest()


def f64_sha(values):
    return sha(np.asarray(values,dtype="<f8").tobytes(order="C"))


def read_json(path):
    def bad(value): raise ValueError("nonfinite JSON token "+value)
    return json.loads(Path(path).read_text(encoding="utf-8-sig"),parse_constant=bad)


def property_lexeme(text,name):
    decoder=json.JSONDecoder()
    def skip(i):
        while i<len(text) and text[i].isspace(): i+=1
        return i
    i=skip(0)
    if text[i]!="{": raise ValueError("expected JSON object")
    i+=1; found=[]
    while True:
        i=skip(i)
        if text[i]=="}": break
        key,i=decoder.raw_decode(text,i); i=skip(i)
        if text[i]!=":": raise ValueError("bad object separator")
        start=skip(i+1); _,end=decoder.raw_decode(text,start)
        if key==name: found.append(text[start:end])
        i=skip(end)
        if text[i]=="}": break
        if text[i]!=",": raise ValueError("bad object separator")
        i+=1
    if len(found)!=1: raise ValueError("duplicate or missing property "+name)
    return found[0]


def compact_lexeme(text):
    result=[]; quoted=False; escaped=False
    for char in text:
        if quoted:
            result.append(char)
            if escaped: escaped=False
            elif char=="\\": escaped=True
            elif char=='"': quoted=False
        elif char=='"': quoted=True; result.append(char)
        elif not char.isspace(): result.append(char)
    if quoted: raise ValueError("unterminated JSON string")
    return "".join(result)


class Checks:
    def __init__(self): self.rows=[]

    def check(self,name,passed,**details):
        self.rows.append({"name":name,"passed":bool(passed),**details})

    def close(self,name,actual,expected,atol=1e-12,rtol=1e-10):
        a,b=np.asarray(actual,float),np.asarray(expected,float)
        if a.shape!=b.shape or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
            self.check(name,False,reason="shape or finite values",actualShape=list(a.shape),expectedShape=list(b.shape)); return
        error=np.abs(a-b); limit=atol+rtol*np.maximum(np.abs(a),np.abs(b))
        self.check(name,bool(np.all(error<=limit)),maxAbsoluteError=float(np.max(error)) if error.size else 0.,
                   absoluteTolerance=atol,relativeTolerance=rtol)


def source_hashes(source_dir):
    return {name:file_sha(Path(source_dir)/name) for name in SOURCE_FILES}


def authored_geometry(n):
    surface=np.array([[.25,.1+(j+.5)*.6/n,-.3+(k+.5)*.6/n]
                      if panel==0 else [-.3+(k+.5)*.6/n,.1+(j+.5)*.6/n,.25]
                      for panel in range(2) for j in range(n) for k in range(n)],float)
    gas=np.array([[.2+(ix-1.5)*.05,.1+(iy-.5)*.05,(iz-1.5)*.05]
                  for ix in range(4) for iy in range(2) for iz in range(4)],float)
    return surface,gas


def path_positions(origins,time):
    c,s=math.cos(math.pi/2*time),math.sin(math.pi/2*time)
    out=np.empty_like(origins)
    out[:,0]=origins[:,0]*c-origins[:,2]*s
    out[:,1]=origins[:,1]+.4*time
    out[:,2]=origins[:,0]*s+origins[:,2]*c
    return out


def display_map(temperatures,n):
    """Independent tensor interpolation, retaining declared lerp arithmetic."""
    values=np.asarray(temperatures,float)[:2*n*n].reshape(2,n,n)
    if n==64: return values.reshape(-1).copy()
    q=(np.arange(64,dtype=float)+.5)*n/64-.5
    lower=np.floor(np.clip(q,0,n-1)).astype(int)
    fraction=np.where(q<=0,0.,np.where(q>=n-1,0.,q-lower))
    upper=np.minimum(lower+1,n-1)
    fj=fraction[:,None]; fk=fraction[None,:]
    a0=(1-fk)*values[:,lower[:,None],lower[None,:]]+fk*values[:,lower[:,None],upper[None,:]]
    a1=(1-fk)*values[:,upper[:,None],lower[None,:]]+fk*values[:,upper[:,None],upper[None,:]]
    return ((1-fj)*a0+fj*a1).reshape(-1)


def thermal_energy(temperatures,capacity,ns):
    # NumPy's pairwise reductions are independent of producer's scalar Kahan loop.
    product=np.asarray(temperatures)*capacity
    surface=float(np.sum(product[:ns])); gas=float(np.sum(product[ns:]))
    return {"surface":surface,"gas":gas,"total":surface+gas}


def observation(temperatures,capacity,n,step,rate):
    ns=2*n*n; surface=np.asarray(temperatures[:ns]).reshape(2,n,n)
    heat=(surface-300)*capacity[:ns].reshape(2,n,n)
    regions=heat.reshape(2,4,n//4,4,n//4).sum(axis=(2,4)).reshape(32)
    return {"step":step,"time":step/rate,"panelHeat":heat.sum(axis=(1,2)),"regionHeat":regions,
            "display":display_map(temperatures,n),"gasTemperatures":np.asarray(temperatures[ns:]).copy(),
            "actualPeakRise":float(np.max(surface-300)),"minimum":float(np.min(temperatures)),
            "maximum":float(np.max(temperatures)),"energy":thermal_energy(temperatures,capacity,ns)}


def _ratio(numerator,denominator):
    if denominator>0: return float(numerator/denominator)
    return 0. if numerator==0 else None


def compare_observations(candidate,reference):
    if len(candidate)!=121 or len(reference)!=121: raise ValueError("121 common observations required")
    panel_a=np.array([r["panelHeat"] for r in candidate]); panel_b=np.array([r["panelHeat"] for r in reference])
    region_a=np.array([r["regionHeat"] for r in candidate]); region_b=np.array([r["regionHeat"] for r in reference])
    display_a=np.array([r["display"] for r in candidate]); display_b=np.array([r["display"] for r in reference])
    gas_a=np.array([r["gasTemperatures"] for r in candidate]); gas_b=np.array([r["gasTemperatures"] for r in reference])
    dp=panel_a-panel_b; dr=region_a-region_b; dd=display_a-display_b; dg=gas_a-gas_b
    pd=float(np.max(np.abs(panel_b))); rd=float(np.max(np.abs(region_b)))
    # All display sites carry the same explicit physical area, which cancels.
    display_rms=np.sqrt(np.mean(dd*dd,axis=1))
    reference_rise=display_b-300
    denom=float(np.max(np.sqrt(np.mean(reference_rise*reference_rise,axis=1))))
    peak=float(np.max(reference_rise))
    pn=float(np.max(np.abs(dp))); rn=float(np.max(np.abs(dr))); dn=float(np.max(display_rms))
    primary={"panel":_ratio(pn,pd),"regional":_ratio(rn,rd),"display":float(dn/denom) if denom>0 else None}
    return {"primary":primary,"panelDenominator":pd,"regionDenominator":rd,"displayDenominator":denom,
            "maxReferenceDisplayRise":peak,"panelNumerator":pn,"regionNumerator":rn,"displayNumerator":dn,
            "peakNormalizedDisplayDiagnostic":_ratio(dn,peak),
            "panelErrorByPanel":np.max(np.abs(dp),axis=0).tolist(),
            "regionErrorByRegion":np.max(np.abs(dr),axis=0).tolist(),
            "peakAbsoluteError":float(np.max(np.abs(dd))),"gasMaxAbsoluteError":float(np.max(np.abs(dg))),
            "gasRmsError":float(np.sqrt(np.mean(dg*dg))),
            "timeSeries":[{"time":k/120,"panelDifference":dp[k].tolist(),"regionDifference":dr[k].tolist(),
                           "displayRms":float(display_rms[k]),"displayNormalizedRms":_ratio(display_rms[k],denom)} for k in range(121)],
            "valid":all(v is not None and math.isfinite(v) for v in primary.values())}


def passes(comparison,tolerance):
    return comparison["valid"] and all(value<=tolerance for value in comparison["primary"].values())


def reference_decision(comparisons):
    if not all(key in comparisons for key in ("R0_R1","R1_R2","R0_R2")):
        return {"status":"INCOMPLETE","accepted":False,"needR3":False}
    if not passes(comparisons["R1_R2"],.005):
        return {"status":"REFERENCE_INVALID","accepted":False,"needR3":False}
    if passes(comparisons["R0_R1"],.005) and passes(comparisons["R0_R2"],.005):
        return {"status":"REFERENCE_ACCEPTED","accepted":True,"selectedRole":"R2","needR3":False}
    if not all(key in comparisons for key in ("R2_R3","R1_R3")):
        return {"status":"R3_REQUIRED","accepted":False,"needR3":True}
    if passes(comparisons["R2_R3"],.005) and passes(comparisons["R1_R3"],.005):
        return {"status":"REFERENCE_ACCEPTED","accepted":True,"selectedRole":"R3","needR3":False}
    return {"status":"REFERENCE_INVALID","accepted":False,"needR3":False}


def signal_check(observations):
    peak=max(float(np.max(o["display"]-300)) for o in observations)
    rms=max(float(np.sqrt(np.mean((o["display"]-300)**2))) for o in observations)
    panel=max(float(np.max(np.abs(o["panelHeat"]))) for o in observations)
    regional=max(float(np.max(np.abs(o["regionHeat"]))) for o in observations)
    return {"passed":peak>=1 and rms>0 and panel>0 and regional>0,"peakDisplayRise":peak,"maximumRmsDisplayRise":rms,
            "panelDenominator":panel,"regionDenominator":regional}


def allpairs_replay(surface,gas,area,volume,capacity,old,dt,chunk_size=2048):
    """One independent complete old-state step; no producer spatial search."""
    ns,ng=len(surface),len(gas); n=ns+ng
    sum_g=np.zeros(n); counts=np.zeros(ns,dtype=np.int64); fragments=[]; weights=[]
    normalization=3/(math.pi*.12*.12*.12); edge_count=0; boundary_count=0
    for start in range(0,ns,chunk_size):
        stop=min(start+chunk_size,ns)
        delta=surface[start:stop,None,:]-gas[None,:,:]
        r=np.sqrt((delta[:,:,0]*delta[:,:,0]+delta[:,:,1]*delta[:,:,1])+delta[:,:,2]*delta[:,:,2])
        inside=r<.12
        G=((2*area[start:stop,None])*volume[None,:])*(normalization*np.maximum(0.,1-r/.12))
        G=np.where(inside,G,0.)
        sum_g[start:stop]=G.sum(axis=1); sum_g[ns:]+=G.sum(axis=0)
        counts[start:stop]=inside.sum(axis=1)
        row,col=np.nonzero(inside); fragments.append(col.astype("<u4")); weights.append((start,stop,G))
        edge_count+=len(col)
        boundary_count+=int(np.sum(np.abs(r-.12)<=8*np.finfo(float).eps*np.maximum(.12,r)))
    offsets=np.zeros(ns+1,dtype="<u4"); offsets[1:]=np.cumsum(counts,dtype=np.uint64)
    digest=hashlib.sha256(offsets.tobytes())
    for fragment in fragments: digest.update(fragment.tobytes())
    max_rate=float(np.max(sum_g/capacity)); substeps=max(1,math.ceil(dt*max_rate/.9)); sub_dt=dt/substeps
    T=np.asarray(old,float).copy(); flux_s=0.; flux_g=0.
    for _ in range(substeps):
        change=np.zeros(n)
        for start,stop,G in weights:
            Q=sub_dt*G*(T[None,ns:]-T[start:stop,None])
            change[start:stop]=Q.sum(axis=1); change[ns:]-=Q.sum(axis=0)
        flux_s+=float(np.sum(change[:ns])); flux_g+=float(np.sum(change[ns:])); T+=change/capacity
    return {"temperature":T,"edgeCount":edge_count,"maxRate":max_rate,"substeps":substeps,
            "substepDt":sub_dt,"maxCfl":sub_dt*max_rate,"topologySHA256":digest.hexdigest(),
            "sumConductance":float(np.sum(sum_g[:ns])),"netSurface":flux_s,"netGas":flux_g,
            "boundaryPairs":boundary_count,"allPairs":ns*ng}


def check_comparison(actual,expected,prefix,checks):
    checks.check(prefix+":valid",actual.get("valid")==expected["valid"])
    for name in ("primary","panelDenominator","regionDenominator","displayDenominator","maxReferenceDisplayRise",
                 "panelNumerator","regionNumerator","displayNumerator","panelErrorByPanel","regionErrorByRegion","peakNormalizedDisplayDiagnostic",
                 "peakAbsoluteError","gasMaxAbsoluteError","gasRmsError"):
        if isinstance(expected[name],dict):
            for key,value in expected[name].items():
                if value is None: checks.check(prefix+":"+name+":"+key,actual[name][key] is None)
                else: checks.close(prefix+":"+name+":"+key,actual[name][key],value)
        else: checks.close(prefix+":"+name,actual[name],expected[name])
    checks.check(prefix+":timeseries-coverage",len(actual["timeSeries"])==121)
    for a,b in zip(actual["timeSeries"],expected["timeSeries"]):
        checks.check(prefix+f":time-{b['time']}",a["time"]==b["time"])
        for key in ("panelDifference","regionDifference","displayRms","displayNormalizedRms"):
            if b[key] is None: checks.check(prefix+":"+key,a[key] is None)
            else: checks.close(prefix+":"+key,a[key],b[key])


def audit_fixture(raw,definition,text,checks):
    name=definition["id"]; n=definition["n"]; ns=2*n*n; count=ns+32
    checks.check(name+":case-schema",raw.get("phase")=="P7" and raw.get("version")==1 and raw.get("id")==name
                 and raw.get("definition")==definition and raw.get("config")==CONFIG and raw.get("executionValid") is True)
    data=raw["input"]; nodes=data["nodes"]
    if data.get("surfaceCount")!=ns or len(nodes)!=count: raise ValueError("authored node coverage mismatch")
    ids=[f"p{p}-j{j}-k{k}" for p in range(2) for j in range(n) for k in range(n)]
    ids += [f"g-ix{x}-iy{y}-iz{z}" for x in range(4) for y in range(2) for z in range(4)]
    checks.check(name+":node-ids-kinds",[v["id"] for v in nodes]==ids
                 and [v["kind"] for v in nodes]==["surface"]*ns+["gas"]*32)
    surface,origins=authored_geometry(n)
    positions=np.asarray([v["position"] for v in nodes],float)
    measure=np.asarray([v["measure"] for v in nodes],float)
    density=np.asarray([v["capacityPerMeasure"] for v in nodes],float)
    capacity=np.asarray([v["capacity"] for v in nodes],float)
    initial=np.asarray([v["temperature"] for v in nodes],float)
    checks.close(name+":authored-positions",positions,np.vstack([surface,origins]),atol=2e-15,rtol=0.)
    checks.close(name+":gas-origins",data["gasInitialPositions"],origins,atol=2e-15,rtol=0.)
    checks.close(name+":authored-measure",measure,np.r_[np.full(ns,.36/(n*n)),np.full(32,.05**3)],atol=0.,rtol=1e-14)
    checks.close(name+":authored-capacity-density",density,np.r_[np.full(ns,2),np.full(32,30)],atol=0.,rtol=0.)
    checks.close(name+":authored-capacity",capacity,measure*density,atol=0.,rtol=1e-14)
    checks.close(name+":authored-temperature",initial,np.r_[np.full(ns,300),np.full(32,600)],atol=0.,rtol=0.)
    lexical=sha(compact_lexeme(property_lexeme(text,"input")).encode("utf-8"))
    checks.check(name+":input-sha-before-after",lexical==raw.get("inputSHA256")==raw.get("inputSHA256After") and raw.get("inputUnchanged") is True)
    checks.check(name+":display-area-weights",raw.get("displayAreaWeights")=={"kind":"uniform","count":8192,"weight":.36/4096,"totalArea":.72})
    return {"positions":positions,"surface":positions[:ns],"origins":np.asarray(data["gasInitialPositions"],float),
            "measure":measure,"capacity":capacity,"initial":initial,"ns":ns,"count":count,"inputSHA256":lexical}


def surface_cell_counts(surface):
    cells,counts=np.unique(np.floor(surface/.12).astype(np.int64),axis=0,return_counts=True)
    return [(tuple(int(v) for v in cell),int(count)) for cell,count in zip(cells,counts)]


def independent_hash_work(surface_cells,gas,ns):
    buckets={}
    for row in np.floor(gas/.12).astype(np.int64):
        key=tuple(int(v) for v in row); buckets[key]=buckets.get(key,0)+1
    candidate_pairs=0; cache_entries=0
    for (x,y,z),multiplicity in surface_cells:
        neighbors=sum(buckets.get((x+dx,y+dy,z+dz),0) for dx in (-1,0,1) for dy in (-1,0,1) for dz in (-1,0,1))
        candidate_pairs+=multiplicity*neighbors; cache_entries+=neighbors
    return {"candidatePairsPerPass":candidate_pairs,"distanceEvaluations":2*candidate_pairs,
            "indexedGasNodes":32,"occupiedBuckets":len(buckets),"bucketLookups":27*len(surface_cells),
            "candidateCacheCells":len(surface_cells),"candidateCacheEntries":cache_entries,
            "candidateCacheHits":2*ns-len(surface_cells)}


def persistent_memory(n):
    ns=2*n*n; count=ns+32; mapped=n!=64
    fields={"packedPositionBytes":24*count,"packedSurfacePositionBytes":24*ns,"packedGasPositionBytes":24*32,
            "measureBytes":8*count,"capacityBytes":8*count,"currentTemperatureBytes":8*count,"originBytes":24*32,
            "displayOwnedBytes":8192*8 if mapped else 0,"mappingBytes":64*(4+8) if mapped else 0,
            "displayAliasesCurrentState":not mapped,"initialAliasesCurrentState":True,"unknownHeapBytes":None}
    fields["persistentBytes"]=48*count+24*32+fields["displayOwnedBytes"]+fields["mappingBytes"]
    return fields


def check_energy(checks,name,actual,expected,scale):
    checks.close(name,actual,expected,atol=ENERGY_RTOL*scale,rtol=0.)


def check_observation(actual,expected,name,scale,checks):
    checks.check(name+":time",actual["step"]==expected["step"] and actual["time"]==expected["time"])
    for key in ("display","gasTemperatures","actualPeakRise","minimum","maximum"):
        checks.close(name+":"+key,actual[key],expected[key],atol=TEMP_ATOL,rtol=0.)
    for key in ("panelHeat","regionHeat"):
        checks.close(name+":"+key,actual[key],expected[key],atol=ENERGY_RTOL*scale,rtol=0.)
    for key in ("surface","gas","total"):
        check_energy(checks,name+":energy-"+key,actual["energy"][key],expected["energy"][key],scale)


def check_endpoint(actual,T,display,positions,step,rate,name,checks):
    expected={"temperatureSHA256":f64_sha(T),"displaySHA256":f64_sha(display),"positionSHA256":f64_sha(positions),
              "step":step,"time":step/rate}
    checks.check(name,all(actual.get(k)==v for k,v in expected.items()))


def check_actual_geometry(frame,origins,step,rate,name,checks):
    checks.check(name+":integer-time-schedule",frame.get("step")==step and frame.get("time")==step/rate
                 and frame.get("acceptedTime")==step/rate and frame.get("geometryTime")== (step-1)/rate)
    gas=np.asarray(frame["geometryGasPositions"],float); accepted=np.asarray(frame["acceptedGasPositions"],float)
    expected_gas=path_positions(origins,(step-1)/rate); expected_accepted=path_positions(origins,step/rate)
    checks.close(name+":actual-prestep-gas-path",gas,expected_gas,atol=POSITION_ATOL,rtol=0.)
    checks.close(name+":actual-accepted-gas-path",accepted,expected_accepted,atol=POSITION_ATOL,rtol=0.)
    if gas.shape!=(32,3) or accepted.shape!=(32,3): raise ValueError("gas position shape")
    error=max(float(np.max(np.abs(gas-expected_gas))),float(np.max(np.abs(accepted-expected_accepted))))
    return gas,accepted,error


def check_physical_replay(f,frame,old,new,rate,name,scale,checks):
    ns=f["ns"]; graph=frame["graph"]; ledger=frame["ledger"]
    gas=np.asarray(frame["geometryGasPositions"],float)
    reference=allpairs_replay(f["surface"],gas,f["measure"][:ns],f["measure"][ns:],f["capacity"],old,1/rate)
    checks.close(name+":independent-full-temperature-replay",new,reference["temperature"],atol=TEMP_ATOL,rtol=0.)
    checks.check(name+":independent-topology",graph["topologySHA256"]==reference["topologySHA256"] and graph["edgeCount"]==reference["edgeCount"])
    checks.check(name+":independent-substeps",ledger["substeps"]==reference["substeps"])
    for field in ("maxRate","maxCfl"):
        checks.close(name+":independent-"+field,ledger[field],reference[field],atol=1e-12,rtol=1e-12)
    checks.close(name+":independent-conductance-sum",graph["sumConductance"],reference["sumConductance"],atol=1e-10,rtol=1e-10)
    for field in ("netSurface","netGas"):
        check_energy(checks,name+":independent-"+field,ledger[field],reference[field],scale)
    checks.check(name+":independent-boundary-count",graph["work"]["boundaryPairs"]==reference["boundaryPairs"])
    return {"step":frame["step"],"geometryTime":frame["geometryTime"],"allPairs":reference["allPairs"],
            "edgeCount":reference["edgeCount"],"substeps":reference["substeps"],"maxRate":reference["maxRate"],
            "maxTemperatureErrorK":float(np.max(np.abs(new-reference["temperature"]))),
            "topologySHA256":reference["topologySHA256"],"boundaryPairs":reference["boundaryPairs"]}


def audit_arm(raw,definition,text,run_dir,checks):
    name=definition["id"]; n=definition["n"]; rate=definition["rate"]
    f=audit_fixture(raw,definition,text,checks); ns=f["ns"]; count=f["count"]; capacity=f["capacity"]
    history=raw["history"]; filename=name+".temperatures.f64.gz"; path=Path(run_dir)/filename
    checks.check(name+":history-schema",history.get("file")==filename and history.get("format")=="float64-le"
                 and history.get("vectorCount")==rate+1 and history.get("vectorLength")==count
                 and history.get("uncompressedBytes")==8*count*(rate+1) and history.get("roundtripVerified") is True
                 and history.get("gzipLevel")==1
                 and history.get("order")=="surface panel/j/k ascending, then gas ix/iy/iz ascending")
    compressed_before=file_sha(path)
    checks.check(name+":compressed-file-authentication",path.stat().st_size==history["compressedBytes"] and compressed_before==history["compressedSHA256"])
    frames=raw["frames"]; observed=raw["observations"]
    if len(frames)!=rate or len(observed)!=121: raise ValueError("incomplete native steps/common observations")
    selected={1,rate//4,rate//2,3*rate//4,rate}
    persistent=persistent_memory(n); memory=raw["memory"]
    checks.check(name+":persistent-array-ownership",all(memory.get(k)==v for k,v in persistent.items()))
    initial_energy=thermal_energy(f["initial"],capacity,ns); scale=max(1.,abs(initial_energy["total"]))
    cells=surface_cell_counts(f["surface"])
    computed=[]; replay_rows=[]; raw_digest=hashlib.sha256(); raw_bytes=0
    maximum_build=persistent["persistentBytes"]; maximum_exchange=maximum_build
    max_energy_drift=0.; max_temperature_replay_error=0.; max_position_error=0.
    previous=None; obs_index=0; last_positions=f["positions"]
    with gzip.open(path,"rb") as stream:
        for step in range(rate+1):
            data=stream.read(count*8)
            if len(data)!=count*8: raise ValueError("truncated temperature vector")
            raw_digest.update(data); raw_bytes+=len(data)
            T=np.frombuffer(data,dtype="<f8")
            checks.check(name+f":state-{step}-finite-extrema",bool(np.all(np.isfinite(T)) and np.min(T)>=300-TEMP_ATOL and np.max(T)<=600+TEMP_ATOL))
            current_energy=thermal_energy(T,capacity,ns)
            max_energy_drift=max(max_energy_drift,abs(current_energy["total"]-initial_energy["total"])/scale)
            check_energy(checks,name+f":state-{step}-total-energy",current_energy["total"],initial_energy["total"],scale)
            if step==0:
                checks.close(name+":initial-temperature-vector",T,f["initial"],atol=0.,rtol=0.)
                check_endpoint(raw["initialEndpoint"],T,display_map(T,n),f["positions"],0,rate,name+":initial-endpoint",checks)
            else:
                frame=frames[step-1]; key=name+f":step-{step}"
                gas,accepted,position_error=check_actual_geometry(frame,f["origins"],step,rate,key,checks)
                max_position_error=max(max_position_error,position_error)
                if step>1: checks.close(key+":position-continuity",gas,last_positions[ns:],atol=0.,rtol=0.)
                last_positions=np.vstack([f["surface"],accepted])
                graph=frame["graph"]; ledger=frame["ledger"]; work=graph["work"]; gm=graph["memory"]
                expected_work=independent_hash_work(cells,gas,ns)
                checks.check(key+":hash-search-work",all(work.get(k)==v for k,v in expected_work.items()))
                edge_count=graph["edgeCount"]
                checks.check(key+":graph-count-rate-domain",isinstance(edge_count,int) and 0<=edge_count<=ns*32
                             and math.isfinite(graph["maxRate"]) and graph["maxRate"]>=0 and work["conductanceEvaluations"]==edge_count)
                expected_graph_bytes=4*(ns+1)+12*edge_count+12*count
                expected_gm={"graphTypedArrayBytes":expected_graph_bytes,"candidateScratchBytes":32*4,
                    "candidateCacheTypedArrayBytes":4*expected_work["candidateCacheEntries"],"indexEntries":32,
                    "indexBuckets":expected_work["occupiedBuckets"],"indexHeapBytes":None}
                checks.check(key+":graph-memory",all(gm.get(k)==v for k,v in expected_gm.items()))
                maximum_build=max(maximum_build,persistent["persistentBytes"]+expected_graph_bytes+128+4*expected_work["candidateCacheEntries"])
                maximum_exchange=max(maximum_exchange,persistent["persistentBytes"]+expected_graph_bytes+16*count)
                expected_substeps=max(1,math.ceil((1/rate)*graph["maxRate"]/.9))
                checks.check(key+":cfl-schedule",ledger["dt"]==1/rate and ledger["safety"]==.9
                             and ledger["maxRate"]==graph["maxRate"] and ledger["substeps"]==expected_substeps
                             and 1<=expected_substeps<=100000 and ledger["edgeEvaluations"]==expected_substeps*edge_count
                             and ledger["workspaceTypedArrayBytes"]==16*count)
                checks.close(key+":substep-dt",ledger["substepDt"],(1/rate)/expected_substeps,atol=0.,rtol=0.)
                checks.close(key+":max-cfl",ledger["maxCfl"],ledger["substepDt"]*graph["maxRate"],atol=0.,rtol=0.)
                checks.check(key+":cfl-limit",ledger["maxCfl"]<=.9+1e-12)
                previous_energy=thermal_energy(previous,capacity,ns)
                for part in ("surface","gas","total"):
                    check_energy(checks,key+":ledger-before-"+part,ledger["Ebefore"][part],previous_energy[part],scale)
                    check_energy(checks,key+":ledger-after-"+part,ledger["Eafter"][part],current_energy[part],scale)
                for part,camel in (("surface","Surface"),("gas","Gas")):
                    change=current_energy[part]-previous_energy[part]
                    check_energy(checks,key+":debit-credit-"+part,ledger["net"+camel],change,scale)
                    check_energy(checks,key+":energy-change-"+part,ledger["energyChange"+camel],change,scale)
                check_energy(checks,key+":opposite-exchange",ledger["netSurface"]+ledger["netGas"],0.,scale)
                check_energy(checks,key+":actual-energy-residual",ledger["energyResidual"],current_energy["total"]-previous_energy["total"],scale)
                if step in selected:
                    replay=check_physical_replay(f,frame,previous,T,rate,key,scale,checks)
                    max_temperature_replay_error=max(max_temperature_replay_error,replay["maxTemperatureErrorK"])
                    replay_rows.append(replay)
                else: checks.check(key+":unrequested-topology-hash",graph["topologySHA256"] is None)
            if step%(rate//120)==0:
                current=observation(T,capacity,n,step,rate)
                check_observation(observed[obs_index],current,name+f":observation-{obs_index}",scale,checks)
                computed.append(current); obs_index+=1
            previous=T.copy()
        checks.check(name+":history-exact-end",stream.read(1)==b"")
    checks.check(name+":history-uncompressed-authentication",raw_digest.hexdigest()==history["uncompressedSHA256"] and raw_bytes==history["uncompressedBytes"])
    checks.check(name+":history-stable",file_sha(path)==compressed_before)
    check_endpoint(raw["finalEndpoint"],previous,display_map(previous,n),last_positions,rate,rate,name+":final-endpoint",checks)
    expected_memory={**persistent,"maximumBuildPhaseBytes":maximum_build,"maximumExchangePhaseBytes":maximum_exchange,
                     "maximumAlgorithmOwnedArrayBytes":max(maximum_build,maximum_exchange)}
    checks.check(name+":maximum-array-payload",all(memory.get(k)==v for k,v in expected_memory.items()))
    checks.check(name+":five-physical-replays",[r["step"] for r in replay_rows]==sorted(selected))
    summary={"id":name,"role":definition["role"],"n":n,"rate":rate,"history":history,"inputSHA256":f["inputSHA256"],
        "memory":memory,"initialEndpoint":raw["initialEndpoint"],"finalEndpoint":raw["finalEndpoint"],
        "allStatesAudited":rate+1,"allStateTemperatureComponents":(rate+1)*count,"commonObservationsAudited":121,
        "physicalReplayCoverage":"Exactly the five preregistered steps, not a physical replay of the complete trajectory.",
        "physicalReplays":replay_rows,"maxTemperatureReplayErrorK":max_temperature_replay_error,
        "maxAnalyticPositionErrorM":max_position_error,"maxRelativeEnergyDrift":max_energy_drift,
        "responseCurves":[{"step":o["step"],"time":o["time"],"panelHeat":o["panelHeat"].tolist(),
            "regionHeat":o["regionHeat"].tolist(),"displayRmsRise":float(np.sqrt(np.mean((o["display"]-300)**2))),
            "displayPeakRise":float(np.max(o["display"]-300)),"actualPeakRise":o["actualPeakRise"],"energy":o["energy"]} for o in computed]}
    return summary,computed


def cost_decision(blocks,shared_memory,proxy_memory):
    if len(blocks)!=6: return {"complete":False,"passed":False}
    ratios=[b["proxy"]/b["shared"] for b in blocks]
    ordered=sorted(ratios); median=(ordered[2]+ordered[3])/2
    adjusted={key:shared_memory[key]-SHARED_VISUAL_ALIAS_BYTES
              for key in ("persistentBytes","maximumAlgorithmOwnedArrayBytes")}
    persistent_passed=proxy_memory["persistentBytes"]<=adjusted["persistentBytes"]
    maximum_passed=proxy_memory["maximumAlgorithmOwnedArrayBytes"]<=adjusted["maximumAlgorithmOwnedArrayBytes"]
    cost_passed=median<=.8 and sum(r<1 for r in ratios)>=5
    memory_passed=persistent_passed and maximum_passed
    return {"complete":True,"ratios":ratios,"medianRatio":median,"minRatio":ordered[0],"maxRatio":ordered[-1],
            "fasterBlocks":sum(r<1 for r in ratios),"costPassed":cost_passed,"memoryPassed":memory_passed,
            "memory":{"actual":{"shared":shared_memory,"proxy":proxy_memory},"adjustmentValid":True,
                      "sharedOptimisticVisualAliasAllowanceBytes":SHARED_VISUAL_ALIAS_BYTES,"adjustedShared":adjusted,
                      "persistentPassed":persistent_passed,"maximumPassed":maximum_passed},"passed":cost_passed and memory_passed}


def check_subset(actual,expected,name,checks):
    if isinstance(expected,dict):
        if not isinstance(actual,dict): checks.check(name,False,reason="missing object"); return
        for key,value in expected.items():
            if key not in actual: checks.check(name+":"+key,False,reason="missing field")
            else: check_subset(actual[key],value,name+":"+key,checks)
    elif isinstance(expected,list):
        if not isinstance(actual,list) or len(actual)!=len(expected): checks.check(name,False,reason="list coverage"); return
        for i,(a,b) in enumerate(zip(actual,expected)): check_subset(a,b,name+f":{i}",checks)
    elif isinstance(expected,bool) or expected is None or isinstance(expected,str):
        checks.check(name,type(actual) is type(expected) and actual==expected)
    elif isinstance(expected,int): checks.check(name,actual==expected)
    else: checks.close(name,actual,expected)


def audit_timing(timing,arms,checks):
    checks.check("timing:completed-coverage",timing.get("status")=="completed" and timing.get("order")==TIMING_ORDER
                 and len(timing["warmups"])==2 and len(timing["runs"])==12 and len(timing["blocks"])==6)
    checks.check("timing:warmup-roles",[r["role"] for r in timing["warmups"]]==["shared","proxy"])
    checks.check("timing:authored-inputs-unchanged",timing.get("authoredInputsUnchanged") is True)
    for warmup in timing["warmups"]:
        checks.check("timing:warmup-endpoint-"+warmup["role"],warmup["endpoint"]==arms[warmup["role"]]["finalEndpoint"])
    expected_order=[(block,role) for block,roles in enumerate(TIMING_ORDER) for role in roles]
    checks.check("timing:alternating-block-order",[(r["block"],r["role"]) for r in timing["runs"]]==expected_order)
    lookup={}; stages=("setupMs","analyticPathMs","graphBuildMs","exchangeMs","mappingMs","validationMs")
    for row in timing["runs"]:
        name=f"timing:{row['block']}:{row['role']}"; role=row["role"]; whole=row["wholeTrajectoryMs"]
        checks.check(name+":positive-duration",isinstance(whole,(int,float)) and math.isfinite(whole) and whole>0)
        checks.check(name+":finite-stage-durations",all(k in row["stages"] and math.isfinite(row["stages"][k]) and row["stages"][k]>=0 for k in stages))
        checks.check(name+":id",row["id"]==arms[role]["id"])
        checks.check(name+":endpoint-exact",row["endpoint"]==arms[role]["finalEndpoint"])
        checks.check(name+":memory-exact",row["memory"]==arms[role]["memory"])
        checks.check(name+":validation-scope",row.get("validationScope")=="O(1) ledger/CFL/cumulative-energy checks; native P6 per-node checks remain in exchangeMs; no extra archival extrema scan")
        initial_energy=arms[role]["responseCurves"][0]["energy"]["total"]
        check_energy(checks,name+":initial-energy",row["initialEnergy"],initial_energy,max(1.,abs(initial_energy)))
        checks.close(name+":enclosing-interval",sum(row["stages"].values())+row["unattributedMs"],whole,atol=1e-7,rtol=1e-12)
        checks.check(name+":unattributed-domain",math.isfinite(row["unattributedMs"]) and row["unattributedMs"]>=-1e-7)
        lookup[(row["block"],role)]=whole
    blocks=[{"block":k,"shared":lookup[(k,"shared")],"proxy":lookup[(k,"proxy")]} for k in range(6)]
    checks.check("timing:blocks-match-trajectories",timing["blocks"]==blocks)
    sm,pm=arms["shared"]["memory"],arms["proxy"]["memory"]
    checks.check("memory:optimistic-shared-alias-is-substantiated",sm["packedSurfacePositionBytes"]==SHARED_VISUAL_ALIAS_BYTES
                 and sm["packedPositionBytes"]>=SHARED_VISUAL_ALIAS_BYTES
                 and min(sm["persistentBytes"],sm["maximumAlgorithmOwnedArrayBytes"])>=SHARED_VISUAL_ALIAS_BYTES)
    decision=cost_decision(blocks,sm,pm)
    check_subset(timing["screen"],decision,"timing:screen",checks)
    return {"status":"completed","order":TIMING_ORDER,"runs":timing["runs"],"blocks":blocks,"screen":decision,
            "interpretation":"Six paired blocks within one Node process; CPU to display-temperature buffer, not independent processes, GPU rendering or whole-frame latency."}


def audit_run(run_dir,source_dir,freeze_path):
    run_dir=Path(run_dir); source_dir=Path(source_dir); freeze_path=Path(freeze_path); checks=Checks()
    manifest_path=run_dir/"manifest.json"; manifest_start=file_sha(manifest_path); freeze_start=file_sha(freeze_path)
    manifest=read_json(manifest_path); frozen=read_json(freeze_path); frozen=frozen.get("sourceHashes",frozen)
    source_before=source_hashes(source_dir)
    checks.check("source:coverage",set(frozen)==set(SOURCE_FILES) and list(manifest["sourceHashes"])==SOURCE_FILES)
    checks.check("source:frozen-before-after",source_before==frozen==manifest["sourceHashes"]==manifest.get("sourceHashesAfter")
                 and manifest.get("sourcesUnchanged") is True)
    checks.check("source:immutable-p6-core",source_before["p6-core.mjs"]==CORE_SHA256)
    checks.check("manifest:completed-formal",manifest.get("phase")=="P7" and manifest.get("version")==1 and manifest.get("formal") is True
                 and manifest.get("status")=="completed-pending-independent-audit" and manifest.get("protocolComplete") is True
                 and manifest.get("executionValid") is True and manifest.get("independentAudit")=="pending")
    checks.check("manifest:plan-config",manifest.get("planned")==DEFINITIONS and manifest.get("config")==CONFIG)
    checks.check("manifest:timing-order",manifest["timing"].get("order")==TIMING_ORDER)
    contract=manifest.get("timingContract",{})
    checks.check("manifest:timing-contract",contract.get("freshStatePairedBlocks")==6 and contract.get("warmupsPerArm")==1
                 and contract.get("clock")=="performance.now CPU wall time; no renderer/GPU"
                 and contract.get("gc")=="forced before each trajectory outside enclosing interval; incidental GC inside included")
    records=manifest["cases"]; roles=[r["role"] for r in records]
    checks.check("manifest:unique-case-ids",len(set(r["id"] for r in records))==len(records) and len(set(roles))==len(roles))
    checks.check("manifest:mandatory-references-first",roles[:3]==["R0","R1","R2"])
    definitions_by_role={d["role"]:d for d in DEFINITIONS}; arms={}; observations={}; files=[]; authenticated=[]
    for record in records:
        role=record["role"]
        if role not in definitions_by_role:
            checks.check("manifest:registered-role",False,role=role); continue
        definition=definitions_by_role[role]; name=definition["id"]; filename=name+".json"; path=run_dir/filename
        checks.check(name+":record-identity",record.get("id")==name and record.get("file")==filename)
        before_hash=file_sha(path); files.append(filename); authenticated.append((path,before_hash))
        checks.check(name+":raw-file-authentication",path.stat().st_size==record["bytes"] and before_hash==record["sha256"])
        try:
            text=path.read_text(encoding="utf-8-sig"); raw=read_json(path)
            checks.check(name+":history-manifest-link",record.get("history")==raw["history"])
            history_path=run_dir/(name+".temperatures.f64.gz")
            authenticated.append((history_path,file_sha(history_path)))
            summary,obs=audit_arm(raw,definition,text,run_dir,checks)
            arms[role]=summary; observations[role]=obs
        except (ValueError,TypeError,KeyError,IndexError,OverflowError,EOFError) as error:
            checks.check(name+":complete-arm-audit",False,error=f"{type(error).__name__}: {error}")
    checks.check("manifest:no-unlisted-quality-files",sorted(p.name for p in run_dir.glob("dev-*.json"))==sorted(files))
    checks.check("manifest:no-unlisted-history-files",sorted(p.name for p in run_dir.glob("dev-*.temperatures.f64.gz"))
                 ==sorted(name[:-5]+".temperatures.f64.gz" for name in files))
    comparisons={}; reference={"status":"AUDIT_INCOMPLETE","accepted":False}; quality={"status":"not-run"}; timing={"status":"not-run"}; decision="EXECUTION_INVALID"
    if all(role in observations for role in ("R0","R1","R2")):
        for key in ("R0_R1","R1_R2","R0_R2"):
            a,b=key.split("_"); comparisons[key]=compare_observations(observations[a],observations[b])
        initial_reference=reference_decision(comparisons); expected_roles=["R0","R1","R2"]
        if initial_reference["needR3"]:
            expected_roles.append("R3"); checks.check("reference:required-R3-present","R3" in observations)
            if "R3" in observations:
                for key in ("R2_R3","R1_R3"):
                    a,b=key.split("_"); comparisons[key]=compare_observations(observations[a],observations[b])
        else: checks.check("reference:no-untriggered-R3","R3" not in observations)
        reference=reference_decision(comparisons)
        for key,value in reference.items(): checks.check("reference:decision-"+key,manifest["reference"].get(key)==value)
        checks.check("reference:comparison-coverage",set(manifest["reference"]["comparisons"])==set(comparisons))
        for key,value in comparisons.items(): check_comparison(manifest["reference"]["comparisons"][key],value,"reference:"+key,checks)
        if not reference["accepted"]:
            decision="REFERENCE_INVALID"
            quality={"status":"skipped","reason":decision}
        else:
            signal=signal_check(observations[reference["selectedRole"]]); reference["signal"]=signal
            check_subset(manifest["reference"]["signal"],signal,"reference:signal",checks)
            if not signal["passed"]:
                decision="INSUFFICIENT_SIGNAL"; quality={"status":"skipped","reason":decision}
            else:
                expected_roles += ["shared","proxy"]
                checks.check("quality:both-candidates-present",all(role in observations for role in ("shared","proxy")))
                if all(role in observations for role in ("shared","proxy")):
                    quality={"status":"completed"}
                    for role in ("shared","proxy"):
                        comparison=compare_observations(observations[role],observations[reference["selectedRole"]])
                        quality[role]={"comparison":comparison,"passed":passes(comparison,.02)}
                        check_comparison(manifest["quality"][role]["comparison"],comparison,"quality:"+role,checks)
                        checks.check("quality:gate-"+role,manifest["quality"][role]["passed"]==quality[role]["passed"])
                    if not quality["proxy"]["passed"]: decision="PROXY_QUALITY_STOP"
                    elif not quality["shared"]["passed"]: decision="SHARED_QUALITY_STOP"
                    else:
                        timing=audit_timing(manifest["timing"],arms,checks)
                        decision="PROXY_STRICT_FIRST_SCREEN" if timing["screen"]["passed"] else "QUALITY_PASS_NO_STRICT_DOMINANCE"
        checks.check("manifest:conditional-case-coverage",roles==expected_roles,expectedRoles=expected_roles,actualRoles=roles)
        expected_ids=[definitions_by_role[role]["id"] for role in expected_roles]
        expected_skipped=[{"id":d["id"],"reason":"reference rule did not request optional temporal refinement" if d["role"]=="R3" else quality.get("reason")}
                          for d in DEFINITIONS if d["id"] not in expected_ids]
        checks.check("manifest:completed-required-identities",manifest.get("completedIds")==expected_ids and manifest.get("requiredExecutedIds")==expected_ids)
        checks.check("manifest:explicit-skipped-arms",manifest.get("skipped")==expected_skipped)
        checks.check("quality:execution-status",manifest["quality"]["status"]==quality["status"])
        if quality["status"]=="skipped": checks.check("quality:skip-reason",manifest["quality"].get("reason")==quality["reason"])
        if timing["status"]!="completed":
            timing={"status":"skipped","reason":decision}
            checks.check("timing:correctly-skipped",manifest["timing"].get("status")=="skipped" and manifest["timing"].get("reason")==decision
                         and not manifest["timing"].get("runs") and not manifest["timing"].get("blocks") and not manifest["timing"].get("warmups"))
        checks.check("manifest:scientific-decision",manifest.get("decision")==decision)
    else: checks.check("audit:references-complete",False)
    after=source_hashes(source_dir)
    checks.check("source:stable-during-audit",source_before==after==frozen)
    checks.check("manifest:stable-during-audit",file_sha(manifest_path)==manifest_start)
    checks.check("freeze:stable-during-audit",file_sha(freeze_path)==freeze_start)
    for path,before_hash in authenticated: checks.check(path.name+":stable-during-audit",file_sha(path)==before_hash)
    failed=[r for r in checks.rows if not r["passed"]]
    reference["comparisons"]=comparisons
    summaries=[arms[role] for role in roles if role in arms]
    return {"phase":"P7","status":"passed" if not failed else "failed","independentAuditPassed":not failed,
        "sourceHashes":source_before,"sourceHashesAfter":after,"freezeSHA256":freeze_start,"manifestSHA256":manifest_start,
        "scientificDecision":decision,"reference":reference,"quality":quality,"timing":timing,"cases":summaries,
        "counts":{"completedArms":len(summaries),"allStatesAudited":sum(a["allStatesAudited"] for a in summaries),
                  "stateTemperatureComponents":sum(a["allStateTemperatureComponents"] for a in summaries),
                  "commonObservations":sum(a["commonObservationsAudited"] for a in summaries),
                  "independentPhysicalSteps":sum(len(a["physicalReplays"]) for a in summaries),
                  "independentPhysicalPairs":sum(r["allPairs"] for a in summaries for r in a["physicalReplays"]),
                  "timedTrajectories":len(timing.get("runs",[]))},
        "tolerances":{"newTemperatureAbsoluteK":TEMP_ATOL,"analyticGasPositionAbsoluteM":POSITION_ATOL,
                      "energyRelative":ENERGY_RTOL,"rateAbsolute":1e-12,"rateRelative":1e-12,
                      "referencePrimary":.005,"candidatePrimary":.02},
        "scope":"All native-rate states/energies and common display/response observations audited. Only five fixed steps per arm independently replay the physical operator. Prescribed paths, no VPM, renderer, full-frame or novelty claim.",
        "checks":checks.rows,"failedChecks":failed}


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
    print(json.dumps({"status":report["status"],"decision":report["scientificDecision"],"counts":report["counts"],"failedChecks":len(report["failedChecks"])}))
    return 0 if report["independentAuditPassed"] else 1


if __name__=="__main__":
    sys.exit(main())
