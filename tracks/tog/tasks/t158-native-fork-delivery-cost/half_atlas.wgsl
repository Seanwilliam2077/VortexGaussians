@group(0) @binding(0) var fast: texture_3d<f32>;
@group(0) @binding(1) var slow: texture_storage_3d<rgba16float, write>;

@compute @workgroup_size(8, 8, 4)
fn main(@builtin(global_invocation_id) id: vec3<u32>) {
    if (any(id >= textureDimensions(fast))) { return; }
    let coord = vec3<i32>(id);
    let a = textureLoad(fast, coord, 0);
    textureStore(slow, coord, vec4<f32>(a.x, a.y * 0.5, a.z, a.w));
}
