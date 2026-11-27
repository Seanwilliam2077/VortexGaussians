@group(0) @binding(0) var atlas: texture_3d<f32>;
@group(0) @binding(1) var<storage, read_write> errors: array<atomic<u32>>;

@compute @workgroup_size(8, 8, 4)
fn main(@builtin(global_invocation_id) id: vec3<u32>) {
    if (any(id >= textureDimensions(atlas))) { return; }
    let progress = textureLoad(atlas, vec3<i32>(id), 0).y;
    let nonnegative_unit = bitcast<u32>(progress) < 0x3f800000u;
    // In this interval every stored value is an integer multiple of 2^-24.
    var fails = !nonnegative_unit;
    if (nonnegative_unit && progress < 0.0001220703125) {
        fails = (u32(progress * 16777216.0) & 1u) != 0u;
    }
    if (fails) { atomicAdd(&errors[0], 1u); }
}
