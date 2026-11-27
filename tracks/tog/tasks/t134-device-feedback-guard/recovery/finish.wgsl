@group(0) @binding(0) var<storage, read> partials: array<u32>;
@group(0) @binding(1) var<storage, read_write> result: array<u32>;
@group(1) @binding(0) var<uniform> counts: vec4<u32>;
var<workgroup> lanes: array<u32, 64>;

@compute @workgroup_size(64)
fn main(@builtin(local_invocation_index) lane: u32) {
    var flags = 0u;
    for (var i = lane; i < counts.x; i += 64u) {
        flags |= partials[i];
    }
    lanes[lane] = flags;
    workgroupBarrier();
    for (var distance = 32u; distance > 0u; distance = distance >> 1u) {
        if lane < distance { lanes[lane] |= lanes[lane + distance]; }
        workgroupBarrier();
    }
    if lane == 0u { result[0] = lanes[0]; }
}
