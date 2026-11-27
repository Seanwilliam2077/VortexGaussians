"""Use unchanged native shader descriptors with filename-safe module labels for SDK DXC."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "t135-dxc-native-composite"))
import render


def worker(source, out, cache):
    from wgpu.backends.wgpu_native import GPUDevice

    create = GPUDevice.create_shader_module

    def module(device, **kwargs):
        original = kwargs.get("label", "")
        if ":" in original:
            submitted = original.replace(":", "_")
            kwargs["label"] = submitted
            row = {"original": original, "submitted": submitted,
                   "wgsl_sha256": hashlib.sha256(kwargs["code"].encode()).hexdigest()}
            with (out / "MODULES.ndjson").open("a", encoding="utf8") as stream:
                stream.write(json.dumps(row) + "\n")
        return create(device, **kwargs)

    with patch.object(GPUDevice, "create_shader_module", module):
        return render.run_worker(source, out, cache)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--worker-cache", type=Path)
    args = parser.parse_args()
    source, out = args.source.resolve(), args.out.resolve()
    if args.worker_cache is not None:
        sys.exit(worker(source, out, args.worker_cache))
    sys.exit(render.observe.supervise(source, out, limit=render.LIMIT, worker_script=__file__))
