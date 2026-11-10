"""Static-only T81 freeze. Never launches a browser or scientific worker."""
import ast
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path.cwd()
HERE=ROOT/'tracks/tog/tasks/t81-firewoods-capacity-causality'
OUTER=ROOT.parent.parent
NODE=Path('C:/Program Files/nodejs/node.exe')
EDGE=Path('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe')
PLAYWRIGHT=Path('C:/Users/seanzjxiao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright')


def identity(path):
    raw=path.read_bytes()
    try: label=path.relative_to(OUTER).as_posix()
    except ValueError: label=path.as_posix()
    return {'path':label,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def main():
    if (HERE/'invocation.json').exists(): raise RuntimeError('T81 attempt consumed; no refreeze')
    # Existing candidate is never silently replaced when implementation changes.
    subprocess.run([str(NODE),str(HERE/'stage.mjs')],cwd=ROOT,check=True)
    for name in ['adapter.js','stage.mjs','capture.mjs']:
        subprocess.run([str(NODE),'--check',str(HERE/name)],cwd=ROOT,check=True)
    for name in ['prepare.py','run_once.py','audit_saved.py']:
        ast.parse((HERE/name).read_text(encoding='utf-8'),filename=name)
    historical=json.loads((ROOT/'tracks/tog/tasks/t42-firewoods-sequential-workflow/freeze.json').read_text())
    matched=[]
    for item in historical['files']:
        got=identity(OUTER/item['path'])
        if got!=item: raise RuntimeError('T42 historical frozen input differs: '+item['path'])
        matched.append(item['path'])
    node_version=subprocess.check_output([str(NODE),'--version'],text=True).strip()
    browser_version=subprocess.check_output(['powershell','-NoProfile','-Command',
        "(Get-Item -LiteralPath 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe').VersionInfo.FileVersion"],text=True).strip()
    playwright_version=json.loads((PLAYWRIGHT/'package.json').read_text())['version']
    files=[HERE/name for name in ['BRIEF.md','IMPLEMENTATION.md','adapter.js','stage.mjs','capture.mjs',
                                 'run_once.py','prepare.py','audit_saved.py','staging.json','local/site/demo/index.html']]
    files += [ROOT/'demo/index.html',ROOT/'research/lib/runtime.mjs',
              ROOT/'tracks/tog/tasks/t42-firewoods-sequential-workflow/recipe.json',
              ROOT/'tracks/tog/tasks/t42-firewoods-sequential-workflow/adapter.js',
              ROOT/'tracks/tog/tasks/t42-firewoods-sequential-workflow/freeze.json',
              OUTER/'work/real-asset-ingest/foreground.ply',NODE,EDGE,PLAYWRIGHT/'package.json',PLAYWRIGHT/'index.js']
    freeze={'schema':'t81-static-preexecution-freeze-v1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'parent_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'files':[identity(p) for p in files],
        'runtime':{'node_executable':str(NODE),'node_version':node_version,'browser_executable':str(EDGE),
                   'browser_version':browser_version,'playwright_module':str(PLAYWRIGHT),'playwright_version':playwright_version,
                   'preparation_python':sys.version,'runtime_identity_scope':'Executable hashes plus Playwright version/entry/package; not every browser or Node dependency DLL.'},
        'budget':{'worker_seconds':600,'external_seconds':660,'max_output_bytes':64*1024*1024,'native_steps':1440,'browsers':1,'arms':4,'steps_per_arm':360},
        'arms':[{'id':'per-layer-AB','policy':'per-layer','B':True},{'id':'per-layer-A','policy':'per-layer','B':False},
                {'id':'global-AB','policy':'global','B':True},{'id':'global-A','policy':'global','B':False}],
        'historical_T42_file_identities_checked':matched,'static_checks':{'exact_patch_reversal':True,'node_syntax':True,'python_ast':True},
        'scientific_executions_before_freeze':0,'ready_scope':'Prepared for independent static review; this receipt does not itself authorize execution.',
        'external_asset_not_republished':True}
    (HERE/'freeze.json').write_text(json.dumps(freeze,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'frozen_files':len(files),'historical_files_verified':len(matched),'runtime':freeze['runtime'],'scientific_executions':0}))


if __name__=='__main__':main()
