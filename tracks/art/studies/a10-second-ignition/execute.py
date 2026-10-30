"""One supervised A10 recording; preparation is inert unless --execute."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
import traceback

HERE=Path(__file__).resolve().parent
NODE='C:/Users/seanzjxiao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
MODULE='C:/Users/seanzjxiao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright'
BROWSER='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'

def write_new(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--execute',action='store_true');args=parser.parse_args()
    command=[NODE,str(HERE/'record.mjs'),'--execute']
    if not args.execute:
        print(json.dumps(dict(execution=False,command=command,recording_attempts=1,
            browser_seconds=360,worker_seconds=400,supervisor_seconds=420,
            expected_sequence='load once; ignite; 10+10+10 s; same-place ignite; 1 s; no reset')))
        return 0
    if (HERE/'run-01').exists() or (HERE/'supervisor.json').exists():raise FileExistsError('Existing A10 output; no retry')
    write_new(HERE/'attempt.json',dict(schema='a10-attempt-v1',command=command,maximum_recordings=1))
    began=time.perf_counter();process=None
    receipt=dict(schema='a10-supervisor-v1',command=command,total_budget_seconds=420,
        work_wait_seconds=400,termination_reserve_seconds=20,timed_out=False,errors=[])
    env=dict(os.environ,PLAYWRIGHT_MODULE=MODULE,BROWSER_EXECUTABLE=BROWSER)
    def terminate_own_tree():
        receipt['termination_attempted']=True
        remaining=420-(time.perf_counter()-began)
        if remaining<=0:
            receipt['errors'].append('No total-budget remainder for termination')
            return
        try:
            stopped=subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],
                capture_output=True,text=True,timeout=min(15,remaining),
                creationflags=subprocess.CREATE_NO_WINDOW)
            receipt['termination']={k:getattr(stopped,k) for k in ('returncode','stdout','stderr')}
        except BaseException as error:receipt['errors'].append('termination: '+repr(error))
        remaining=420-(time.perf_counter()-began)
        if remaining>0:
            try:receipt['exit_code']=process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:receipt['errors'].append('process remained live at total budget')
    try:
        with (HERE/'execution.stdout.log').open('xb') as stdout,(HERE/'execution.stderr.log').open('xb') as stderr:
            process=subprocess.Popen(command,stdout=stdout,stderr=stderr,env=env,
                creationflags=subprocess.CREATE_NO_WINDOW)
            receipt['pid']=process.pid
            try:receipt['exit_code']=process.wait(timeout=max(.001,400-(time.perf_counter()-began)))
            except subprocess.TimeoutExpired:
                receipt['timed_out']=True
                terminate_own_tree()
    except BaseException as error:
        receipt['errors'].append(repr(error));receipt['traceback']=traceback.format_exc()
    finally:
        if process is not None and process.poll() is None and not receipt.get('termination_attempted'):
            terminate_own_tree()
        receipt['worker_launched']=process is not None
        receipt['poll_exit_code']=process.poll() if process is not None else None
        receipt['still_live']=process is not None and process.poll() is None
        receipt['requires_cleanup']=receipt['still_live']
        receipt['parent_terminal_check_seconds']=time.perf_counter()-began
        result_path=HERE/'run-01/result.json'
        if result_path.exists():
            try:
                result=json.loads(result_path.read_bytes());receipt['worker_status']=result.get('status')
                receipt['resources_closed']=result.get('resourcesClosed',{})
                receipt['requires_cleanup'] |= any(receipt['resources_closed'].get(k) is not True for k in ('context','browser','server'))
                receipt['workflow_completed']=result.get('workflowCompleted') is True
                receipt['sources_unchanged']=result.get('sourcesUnchanged') is True
            except BaseException as error:receipt['errors'].append('readback: '+repr(error))
        receipt['success']=bool(process is not None and receipt['poll_exit_code']==0 and
            not receipt['timed_out'] and not receipt['errors'] and not receipt['requires_cleanup'] and
            receipt.get('worker_status')=='completed_workflow_and_media' and
            receipt.get('workflow_completed') and receipt.get('sources_unchanged') and
            receipt['parent_terminal_check_seconds']<=420)
        receipt['timing_limit']='Final receipt/stdout writing excluded; parent poll is not a proof about every descendant.'
        receipt['elapsed_before_receipt_write_seconds']=time.perf_counter()-began
        write_new(HERE/'supervisor.json',receipt)
        print(json.dumps(receipt,ensure_ascii=False))
    return 0 if receipt['success'] else 1

if __name__=='__main__':raise SystemExit(main())
