@group(0) @binding(0) var<storage, read> a: array<i32>;
@group(0) @binding(1) var<storage, read> b: array<i32>;
@group(0) @binding(2) var<storage, read_write> partials: array<u32>;
var<workgroup> lanes: array<u32, 64>;

fn facts(cell: u32) -> u32 {
    let base = 13u * cell;
    var flags = 0u;
    for (var k = 0u; k < 3u; k++) {
        let aa = a[base + k];
        let ab = b[base + k];
        let ma = a[base + k + 9u];
        let mb = b[base + k + 9u];
        var axis = 0u;
        if min(aa, ab) < 0 { axis |= 1u; }
        if (aa != 0 || ab != 0) { axis |= 2u; }
        if (ma != 0 || mb != 0) { axis |= 4u; }
        if ((aa > 0) != (ab > 0)) { axis |= 8u; }
        if (aa != ab || ma != mb || a[base + k + 3u] != b[base + k + 3u]) { axis |= 16u; }
        flags |= axis << (5u * k);
    }
    if (a[base + 6u] != b[base + 6u] || a[base + 7u] != b[base + 7u] ||
        a[base + 8u] != b[base + 8u] || a[base + 12u] != b[base + 12u]) { flags |= 1u << 15u; }
    return flags;
}

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) id: vec3<u32>, @builtin(local_invocation_index) lane: u32,
        @builtin(workgroup_id) group: vec3<u32>, @builtin(num_workgroups) counts: vec3<u32>) {
    let words = arrayLength(&a);
    let count = select(words / 13u, words, RAW_ONLY);
    var flags = 0u;
    for (var i = id.x; i < count; i += 64u * counts.x) {
        if RAW_ONLY {
            if a[i] != b[i] { flags = 1u; }
        } else {
            flags |= facts(i);
        }
    }
    lanes[lane] = flags;
    workgroupBarrier();
    for (var distance = 32u; distance > 0u; distance = distance >> 1u) {
        if lane < distance { lanes[lane] |= lanes[lane + distance]; }
        workgroupBarrier();
    }
    if lane == 0u { partials[group.x] = lanes[0]; }
}
