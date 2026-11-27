"""Explicit workgroup and final reductions for resident Blackbody feedback pairs."""
from pathlib import Path
import struct
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from device_guard import classify


class ResidentGuard:
    def __init__(self, gpu):
        import wgpu
        self.gpu = gpu
        self.result = gpu.buffer(4, "feedback decision")
        self.staging = gpu.buffer(4, "feedback readback", wgpu.BufferUsage.MAP_READ | wgpu.BufferUsage.COPY_DST)
        self.partials = None
        source = str(HERE / "partial.wgsl")
        bindings = ["rbuf", "rbuf", "buf"]
        self.raw = gpu.kernel(source, bindings, defines={"RAW_ONLY": True}, workgroup=(64, 1, 1))
        self.axis = gpu.kernel(source, bindings, defines={"RAW_ONLY": False}, workgroup=(64, 1, 1))
        self.finish = gpu.kernel(str(HERE / "finish.wgsl"), ["rbuf", "buf"], workgroup=(64, 1, 1))

    def compare(self, first, second, *, raw_only=False):
        if first.size != second.size or first.size <= 0 or first.size % 52:
            raise ValueError("Expected equal nonempty buffers of complete 13-word cells")
        items = first.size // (4 if raw_only else 52)
        groups = min((items + 63) // 64, 65535)
        if self.partials is None or self.partials.size < groups * 4:
            if self.partials is not None:
                self.partials.destroy()
            self.partials = self.gpu.buffer(groups * 4, "feedback partials")
        kernel = self.raw if raw_only else self.axis
        with self.gpu.batch() as batch:
            batch.run(kernel, [first, second, self.partials], None, groups=(groups, 1, 1))
            batch.run(self.finish, [self.partials, self.result], struct.pack("<4I", groups, 0, 0, 0),
                      groups=(1, 1, 1))
            batch.copy_buffer(self.result, self.staging)
        self.staging.buf.map_sync("READ")
        try:
            flags, = struct.unpack("<I", self.staging.buf.read_mapped(copy=False))
        finally:
            self.staging.buf.unmap()
        if raw_only:
            return "split" if flags else "raw"
        return classify(flags)
