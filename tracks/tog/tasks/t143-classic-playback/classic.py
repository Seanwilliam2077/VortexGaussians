"""Observe the original neutral classic draw while deferring a single unused pipeline."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"t138-dxc-module-labels"))
import run_labels
from run_labels import render

LIMIT=420


class DeferredCaustics:
    def __init__(self, key, create):
        self.key=key
        self.create=create
        self.native=None

    def materialize(self):
        if self.native is None:
            self.native=self.create()
            render.require(self.native.key==self.key,"Materialized a different native pipeline")
        return self.native


@contextmanager
def instrument(gpu_type, batch_type, load_wgsl, shader_key, out):
    begin=time.perf_counter()
    keys=render.observe.KEYS
    original_kernel=gpu_type.kernel
    original_run=batch_type.run

    def event(action,entry,**fields):
        row=dict(action=action,entry=entry,key=keys[entry],elapsed_s=time.perf_counter()-begin,**fields)
        with (out/"STAGE.ndjson").open("a",encoding="utf8") as stream:
            stream.write(json.dumps(row,allow_nan=False)+"\n")
            stream.flush()
            os.fsync(stream.fileno())

    def kernel(gpu, source_file, bindings, entry="main", defines=None, workgroup=(8,8,4), quiet=False):
        if source_file!="stage.wgsl" or entry!="caustics":
            k=original_kernel(gpu,source_file,bindings,entry,defines,workgroup,quiet)
            if source_file=="stage.wgsl" and entry=="main":
                render.require(k.key==keys[entry],"Unexpected native classic key")
                event("native_pipeline_returned",entry)
            return k
        # Copy mutable arguments before the original constructor returns.
        bindings=list(bindings)
        defines=dict(defines or {})
        workgroup=tuple(workgroup)
        code=load_wgsl(source_file,defines)
        key=shader_key(code,entry,bindings,workgroup)
        source_hash=hashlib.sha256(code.encode()).hexdigest()
        render.require(key==keys[entry] and source_hash==render.observe.SOURCE_SHA,"Deferred descriptor changed")
        event("descriptor_deferred",entry,source=source_file,source_sha256=source_hash,
              bindings=bindings,defines=defines,workgroup=workgroup,quiet=bool(quiet))

        def create():
            event("materialization_started",entry)
            actual=original_kernel(gpu,source_file,bindings,entry,defines,workgroup,quiet)
            event("native_pipeline_returned",entry)
            return actual
        return DeferredCaustics(key,create)

    def run(batch,kernel,resources,uniforms,size=None,groups=None):
        if isinstance(kernel,DeferredCaustics):
            kernel=kernel.materialize()
        key=getattr(kernel,"key",None)
        entry=next((name for name,value in keys.items() if value==key),None)
        if entry is None:
            return original_run(batch,kernel,resources,uniforms,size,groups)
        grid=[int(v) for v in (groups or kernel.groups_for(size))]
        event("batch_run_started",entry,groups=grid,resources=len(resources))
        answer=original_run(batch,kernel,resources,uniforms,size,groups)
        event("batch_run_returned",entry,groups=grid,resources=len(resources))
        return answer

    with patch.object(gpu_type,"kernel",kernel),patch.object(batch_type,"run",run):
        yield


def worker(source,out,cache):
    sys.path.insert(0,str(source))
    from blackbody.engine.gpu import GPU,Batch,load_wgsl,shader_key
    with instrument(GPU,Batch,load_wgsl,shader_key,out):
        return run_labels.worker(source,out,cache)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--worker-cache",type=Path)
    a=parser.parse_args()
    source,out=a.source.resolve(),a.out.resolve()
    if a.worker_cache is not None:
        sys.exit(worker(source,out,a.worker_cache.resolve()))
    sys.exit(render.observe.supervise(source,out,limit=LIMIT,worker_script=__file__))
