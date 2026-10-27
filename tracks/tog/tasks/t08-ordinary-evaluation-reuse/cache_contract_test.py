"""Tiny CPU-only tests of new cache risks; no smoke model or GPU operations."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def main():
    os.environ["MKL_THREADING_LAYER"] = "SEQUENTIAL"
    dll = Path(sys.prefix)/"Library/bin"
    handle = None
    if dll.is_dir():
        os.environ["PATH"] = str(dll)+os.pathsep+os.environ.get("PATH", "")
        handle = os.add_dll_directory(str(dll))
    import torch
    torch.set_num_threads(4)
    assert not torch.cuda.is_initialized()
    spec = importlib.util.spec_from_file_location("cache_contract", HERE/"evaluation_cache.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    class Model:
        pass
    model = Model(); model.static = torch.tensor([1.], dtype=torch.float64)
    inputs = {"v0":torch.tensor([2.],dtype=torch.float64)}
    x = torch.tensor([.25], dtype=torch.float64, requires_grad=True)
    output = {k:x*factor for k,factor in (("frames",2), ("velocity",3), ("density",4))}
    identity = lambda: m.fixed_identity(torch, model, inputs, "pinned-contract")
    cache = m.EvaluationCache(torch, identity)
    assert cache.store(x, output, identity())
    saved, reason = cache.lookup(x)
    checks = {"exact_hit": reason == "hit", "no_graph_retained": all(v.grad_fn is None and not v.requires_grad for v in saved.values())}
    checks["wrong_x_miss"] = cache.lookup(x+.01)[1] == "returned_x_mismatch"
    with torch.no_grad():
        output["frames"].add_(9)
    checks["detached_clone_isolation"] = torch.equal(saved["frames"], torch.tensor([.5],dtype=torch.float64))
    inputs["v0"].add_(1)
    checks["input_version_miss"] = cache.lookup(x)[1] == "model_or_input_identity_mismatch"
    assert cache.store(x, output, identity())
    model.static.add_(1)
    checks["model_version_miss"] = cache.lookup(x)[1] == "model_or_input_identity_mismatch"
    cache.invalidate("rollback")
    checks["rollback_invalidates"] = cache.lookup(x)[1] == "empty" and cache.payload_bytes == 0
    cache.store(torch.tensor([0.],dtype=torch.float64), output, identity())
    checks["signed_zero_miss"] = cache.lookup(torch.tensor([-0.],dtype=torch.float64))[1] == "returned_x_mismatch"
    checks["final_slot_reservation"] = (m.closure_slot_available(117,120) and not m.closure_slot_available(118,120)
        and m.acceptance_slot_available(118,120) and not m.acceptance_slot_available(119,120)
        and m.final_slot_available(119,120) and not m.final_slot_available(120,120))
    assert all(checks.values()) and not torch.cuda.is_initialized()
    report = {"scope":"Tiny new-cache contract checks only; not numerical smoke-model qualification",
        "passed":True,"checks":checks,"torch":torch.__version__,"CUDAInitialized":False,
        "cacheSourceSHA256":hashlib.sha256((HERE/"evaluation_cache.py").read_bytes()).hexdigest()}
    with (HERE/"cache-contract-test.json").open("x",encoding="utf-8") as f:json.dump(report,f,indent=2);f.write("\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
