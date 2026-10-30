"""One read-only-source image extraction for A17. No simulation or media encoder."""
import argparse,bisect,datetime,hashlib,json,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'a16-reception-timing-record/run-01'
EXPECTED={'result.json': '05aa2f3e45da61ef86a2dc12cfed75d295ec539902d6824d04f2c60664942550', 'raw/frames.ndjson': '9888c5e9b949ff3a964a75939d5684cf08d19709b9f20bd5efef3f2f569029c0'}
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');args=ap.parse_args()
 if not args.execute:
  print(json.dumps({'execution':False,'integer_seconds':list(range(32)),'add_actual_stop':True,'attempts':1}));return 0
 out=HERE/'reading-01';out.mkdir(exist_ok=False);began=time.perf_counter()
 report={'createdUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'started','items':[],'sourceHashes':{},'noNewBrowserSimulationOrEncoding':True}
 try:
  source_bytes={n:(SOURCE/n).read_bytes() for n in EXPECTED}
  for n,b in source_bytes.items():
   report['sourceHashes'][n]=sha(b)
   if sha(b)!=EXPECTED[n]:raise ValueError('Source identity mismatch: '+n)
  r=json.loads(source_bytes['result.json']);rows=[json.loads(s) for s in source_bytes['raw/frames.ndjson'].splitlines()]
  if r['status']!='failed' or not r['recordingCompleted'] or r['mediaValidated']:raise ValueError('Unexpected A16 source status')
  ns=[int(x['receivedMonotonicNs']) for x in rows];first=ns[0];stop=int(r['captureStop']['receivedMonotonicNs']);end=stop-first
  if len(rows)!=1552 or len(rows)!=r['capture']['savedFrames'] or any(b<=a for a,b in zip(ns,ns[1:])) or stop<=ns[-1]:raise ValueError('Invalid capture sequence')
  if end//1000000000!=31:raise ValueError('Source span differs from fixed 0..31 plan')
  targets=[(f'wall-{i:03d}.jpg',i*1000000000) for i in range(32)]+[('wall-stop.jpg',end)]
  report.update(sourceStatus=r['status'],captureDurationNs=str(end),captureFrameCount=len(rows),policy='Last arrival at or before each fixed target; preserve repeated images',sourceArtifactHash=r['sourceBefore']['tracks/art/studies/a14-view-authored-object/index.html']['sha256'])
  total=0
  for filename,offset in targets:
   if time.perf_counter()-began>60:raise TimeoutError('Extraction budget exceeded')
   index=bisect.bisect_right(ns,first+offset)-1;row=rows[index]
   path=(SOURCE/row['file']).resolve()
   if not path.is_relative_to((SOURCE/'raw').resolve()):raise ValueError('Uncontained source path')
   raw=path.read_bytes();digest=sha(raw);total+=len(raw)
   if len(raw)!=row['bytes'] or digest!=row['sha256'] or total>16*1024*1024:raise ValueError('Source image identity/size mismatch')
   with (out/filename).open('xb') as f:f.write(raw)
   if sha((out/filename).read_bytes())!=digest:raise ValueError('Copy mismatch')
   report['items'].append({'file':filename,'targetOffsetNs':str(offset),'targetSeconds':offset/1e9,'sourceArrivalIndex':row['arrivalIndex'],'sourceFile':row['file'],'sourceReceivedMonotonicNs':row['receivedMonotonicNs'],'sourceOffsetNs':str(ns[index]-first),'sourceOffsetSeconds':(ns[index]-first)/1e9,'heldSinceLastArrivalSeconds':(first+offset-ns[index])/1e9,'bytes':len(raw),'sha256':digest,'actualStopTarget':filename=='wall-stop.jpg'})
  report['totalCopiedBytes']=total;report['sourcesUnchanged']=all(sha((SOURCE/n).read_bytes())==v for n,v in EXPECTED.items())
  if not report['sourcesUnchanged']:raise ValueError('Source changed during extraction')
  report['status']='completed_fixed_source_sequence'
 except Exception as e:
  report['status']='failed';report['failure']=repr(e)
 report['secondsBeforeFinalReceipt']=time.perf_counter()-began
 report['limitations']='Original JPEG arrivals at fixed targets, not continuous video viewing or exact compositor presentation timing. A16 remains failed; no movie is generated.'
 (out/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:report.get(k) for k in ['status','secondsBeforeFinalReceipt','totalCopiedBytes','failure']},ensure_ascii=False))
 return 0 if report['status']=='completed_fixed_source_sequence' else 1
if __name__=='__main__':raise SystemExit(main())
