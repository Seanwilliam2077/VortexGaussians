"""Freeze final inputs once, before the sole dynamic attempt."""
import datetime,hashlib,json,subprocess
from pathlib import Path
r=Path.cwd();outer=r.parent.parent;h=r/'tracks/tog/tasks/t42-firewoods-sequential-workflow'
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()=='9343f9e957595b6bba1abcccd382a9cc6c8852b1'
assert not (outer/'outputs/t42-firewoods-sequential-workflow/run-01').exists()
def identity(p):
 b=p.read_bytes();return {'path':p.relative_to(outer).as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
source=(r/'demo/index.html').read_bytes();candidate=(h/'local/site/demo/index.html').read_bytes();adapter=(h/'adapter.js').read_bytes()
insertion=b'// T42 INSPECTION BEGIN\n'+adapter+b'\n// T42 INSPECTION END\n'
assert candidate.count(insertion)==1 and candidate.replace(insertion,b'')==source
assert hashlib.sha256(source).hexdigest()=='e9d808c434bdd8ce91482f60502f03f5d08c56b71c082eb704c53275ff9f57d0'
read_log={a:json.loads((h/'local'/f'{a}-reads.json').read_bytes()) for a in ['root','camera']}
counts={a:sum(e['displayed_lines'] for e in log) for a,log in read_log.items()}
assert counts=={'root':516,'camera':260}
ledger={'counts':counts,'total':sum(counts.values()),'cap':800,'entries':read_log}
with (h/'source-read-ledger.json').open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(ledger,indent=2)+'\n')
names=['prepare.mjs','preparation-history.json','stage.mjs','adapter-tail.js','adapter.js','capture.mjs','supervise.py','audit_saved.py','recipe.json','PROTOCOL.md','source-read-ledger.json','freeze.py']
files=[h/n for n in names]+[h/'local/site/demo/index.html',h/'local/prepare-v1.mjs',r/'demo/index.html',r/'research/lib/runtime.mjs',
 r/'tracks/validation/t42-preexecution-review.md',outer/'work/real-asset-static-staging/adapter.js',outer/'work/real-asset-static-staging/run.mjs']
files += [outer/'work/real-asset-ingest'/n for n in ['foreground.ply','cameras.json','source-photo.png','cfg_args.txt','manifest.json']]
result={'schema':'t42-final-pre-execution-freeze-v1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'parent_commit':'9343f9e957595b6bba1abcccd382a9cc6c8852b1','original_source_sha256':hashlib.sha256(source).hexdigest(),
 'candidate_reverses_exactly':True,'original_displayed_source_lines':776,'two_offline_input_preparations_disclosed':True,'scientific_attempts_before_freeze':0,
 'files':[identity(p) for p in files]}
with (h/'freeze.json').open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(result,indent=2)+'\n')
print(json.dumps({'freeze':identity(h/'freeze.json'),'inputs':len(files),'source_lines':776,'browser_launches':0}))
