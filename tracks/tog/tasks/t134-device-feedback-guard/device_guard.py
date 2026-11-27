"""Compare two resident Blackbody cloth buffers on a single existing native GPU."""
from pathlib import Path
from struct import unpack


SHADER = Path(__file__).with_name("feedback.wgsl").resolve()
DIFFERENT_SOURCE = 1 << 15
DIFFERENT_TRIPLES = sum(16 << (5 * axis) for axis in range(3))


def classify(flags):
    """Decode the globally reduced facts, keeping raw equality as the first option."""
    if not flags & (DIFFERENT_SOURCE | DIFFERENT_TRIPLES):
        return "raw"
    if flags & DIFFERENT_SOURCE:
        return "split"
    for axis in range(3):
        facts = (flags >> (5 * axis)) & 31
        negative = bool(facts & 1)
        absent_area = not facts & 2
        zero_impulse_same_support = not facts & (4 | 8)
        same_inputs = not facts & 16
        if negative or not (absent_area or zero_impulse_same_support or same_inputs):
            return "split"
    return "axis"


class FeedbackGuard:
    """Use sequentially on the owning GPU queue. Host readback synchronizes each decision."""

    def __init__(self, gpu):
        import wgpu
        self.gpu = gpu
        self.result = gpu.buffer(4, "feedback comparison")
        self.staging = gpu.buffer(4, "feedback decision readback", wgpu.BufferUsage.MAP_READ | wgpu.BufferUsage.COPY_DST)
        bindings = ["rbuf", "rbuf", "buf"]
        self.axis = gpu.kernel(str(SHADER), bindings, "compare_axis", workgroup=(64, 1, 1))
        self.raw = gpu.kernel(str(SHADER), bindings, "compare_raw", workgroup=(64, 1, 1))

    def compare(self, first, second, *, raw_only=False):
        if first.size != second.size or first.size <= 0 or first.size % (13 * 4):
            raise ValueError("Expected equal nonempty buffers of complete 13-word cells")
        items = first.size // (4 if raw_only else 52)
        # Each lane handles a grid-stride loop beyond WebGPU's standard dispatch limit.
        groups = min((items + 63) // 64, 65535)
        kernel = self.raw if raw_only else self.axis
        with self.gpu.batch() as batch:
            batch.clear_buffer(self.result)
            batch.run(kernel, [first, second, self.result], None, groups=(groups, 1, 1))
            batch.copy_buffer(self.result, self.staging)
        self.staging.buf.map_sync("READ")
        try:
            flags, = unpack("<I", self.staging.buf.read_mapped(copy=False))
        finally:
            self.staging.buf.unmap()
        if raw_only:
            return "split" if flags else "raw"
        return classify(flags)
