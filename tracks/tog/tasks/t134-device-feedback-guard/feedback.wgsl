@group(0) @binding(0) var<storage, read> first: array<i32>;
@group(0) @binding(1) var<storage, read> second: array<i32>;
@group(0) @binding(2) var<storage, read_write> result: atomic<u32>;
var<workgroup> group_flags: atomic<u32>;

// Five disqualifying facts per axis, combined by OR across the entire grid.
const NEGATIVE_AREA: u32 = 1u;
const NONZERO_AREA: u32 = 2u;
const NONZERO_IMPULSE: u32 = 4u;
const DIFFERENT_SUPPORT: u32 = 8u;
const DIFFERENT_TRIPLE: u32 = 16u;
const DIFFERENT_SOURCE: u32 = 1u << 15u;

fn axis_flags(base: u32, axis: u32) -> u32 {
    let a = first[base + axis];
    let b = second[base + axis];
    let p = first[base + 9u + axis];
    let q = second[base + 9u + axis];
    var flags = 0u;
    if min(a, b) < 0 { flags |= NEGATIVE_AREA; }
    if (a != 0 || b != 0) { flags |= NONZERO_AREA; }
    if (p != 0 || q != 0) { flags |= NONZERO_IMPULSE; }
    if ((a > 0) != (b > 0)) { flags |= DIFFERENT_SUPPORT; }
    if (a != b || p != q || first[base + 3u + axis] != second[base + 3u + axis]) {
        flags |= DIFFERENT_TRIPLE;
    }
    return flags << (axis * 5u);
}

fn publish(flags: u32, lane: u32) {
    if flags != 0u { atomicOr(&group_flags, flags); }
    workgroupBarrier();
    if lane == 0u {
        let merged = atomicLoad(&group_flags);
        if merged != 0u { atomicOr(&result, merged); }
    }
}

@compute @workgroup_size(64)
fn compare_axis(@builtin(global_invocation_id) id: vec3<u32>,
                @builtin(local_invocation_index) lane: u32,
                @builtin(num_workgroups) groups: vec3<u32>) {
    var flags = 0u;
    for (var i = id.x; i < arrayLength(&first) / 13u; i += groups.x * 64u) {
        let base = 13u * i;
        for (var axis = 0u; axis < 3u; axis++) {
            flags |= axis_flags(base, axis);
        }
        if (first[base + 6u] != second[base + 6u] || first[base + 7u] != second[base + 7u] ||
            first[base + 8u] != second[base + 8u] || first[base + 12u] != second[base + 12u]) {
            flags |= DIFFERENT_SOURCE;
        }
    }
    publish(flags, lane);
}

@compute @workgroup_size(64)
fn compare_raw(@builtin(global_invocation_id) id: vec3<u32>,
               @builtin(local_invocation_index) lane: u32,
               @builtin(num_workgroups) groups: vec3<u32>) {
    var changed = 0u;
    for (var i = id.x; i < arrayLength(&first); i += groups.x * 64u) {
        if first[i] != second[i] { changed = 1u; }
    }
    publish(changed, lane);
}
