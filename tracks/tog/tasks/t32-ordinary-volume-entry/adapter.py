"""T31 field-to-ray geometry and ordinary bounding-sphere BVH.

This module performs no work on import. Padding and nextafter are engineering
safeguards, not a floating-point enclosure certificate. Gaussian support is
infinite: only query's explicitly charged nodes may be omitted.
"""

import math


def _count(counters, name, value=1):
    counters[name] = counters.get(name, 0) + value


def _finite(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite real number")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite")
    return value


def _vector(value, label):
    if len(value) != 3:
        raise ValueError(f"{label} must have three components")
    return tuple(_finite(x, label) for x in value)


def _dot(a, b):
    return math.fsum(a[k] * b[k] for k in range(3))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _unit(value):
    length = math.hypot(*value)
    if not math.isfinite(length) or length <= 0:
        raise ValueError("Cannot normalize this vector")
    return tuple(x / length for x in value)


def _primitive(primitives, index):
    if isinstance(index, bool) or not isinstance(index, int):
        raise ValueError("Source index must be an integer")
    if not 0 <= index < len(primitives):
        raise ValueError("Source index out of range")
    p = primitives[index]
    source = p["source_index"]
    if isinstance(source, bool) or not isinstance(source, int) or source != index:
        raise ValueError("Source indices must equal original list positions")
    center = _vector(p["mu"], "primitive center")
    h = _finite(p["h"], "primitive h")
    k = _finite(p["k"], "primitive k")
    color = _vector(p["color"], "primitive color")
    if h <= 0 or k < 0 or any(c < 0 for c in color):
        raise ValueError("Need h > 0, k >= 0 and nonnegative HDR color")
    return center, h, k, color


def _ray(ray):
    origin = _vector(ray["origin"], "ray origin")
    direction = _vector(ray["direction"], "ray direction")
    if abs(math.hypot(*direction) - 1.0) > 1e-12:
        raise ValueError("Ray direction must already be unit length")
    a, b = _finite(ray["a"], "ray a"), _finite(ray["b"], "ray b")
    if not 0 <= a < b:
        raise ValueError("Need finite 0 <= a < b")
    return origin, direction, a, b


def build_bvh(primitives, counters):
    """Return a preorder node array; left/right are node ids or None."""
    data = [_primitive(primitives, i) for i in range(len(primitives))]
    _count(counters, "bvh_input_primitives", len(data))
    nodes = []

    def build(ids):
        ordered = sorted(ids)
        lo = [min(data[i][0][axis] for i in ordered) for axis in range(3)]
        hi = [max(data[i][0][axis] for i in ordered) for axis in range(3)]
        center = [math.fsum((lo[a] / 2, hi[a] / 2)) for a in range(3)]
        raw_radius = max(math.dist(center, data[i][0]) for i in ordered)
        _count(counters, "bvh_build_center_distances", len(ordered))
        radius = math.nextafter(raw_radius + 1e-12 * (1 + raw_radius), math.inf)
        raw_sum = math.fsum(data[i][2] for i in ordered)
        sum_k = math.nextafter(raw_sum, math.inf) if raw_sum > 0 else 0.0
        max_h = math.nextafter(max(data[i][1] for i in ordered), math.inf)
        if not all(math.isfinite(x) for x in (*center, radius, sum_k, max_h)):
            raise ValueError("Nonfinite BVH aggregate")
        node_id = len(nodes)
        node = {"id": node_id, "source_ids": ordered, "center": center,
                "radius": radius, "sum_k": sum_k, "max_h": max_h,
                "left": None, "right": None}
        nodes.append(node)
        _count(counters, "bvh_build_nodes")
        _count(counters, "bvh_build_sum_terms", len(ordered))
        if len(ordered) <= 8:
            _count(counters, "bvh_build_leaves")
        else:
            # Half extents avoid overflow in hi - lo; first axis wins a tie.
            extents = [hi[a] / 2 - lo[a] / 2 for a in range(3)]
            axis = max(range(3), key=lambda a: extents[a])
            split = sorted(ordered, key=lambda i: (data[i][0][axis], i))
            middle = len(split) // 2
            node["left"] = build(split[:middle])
            node["right"] = build(split[middle:])
        return node_id

    root = build(list(range(len(data)))) if data else None
    return {"nodes": nodes, "root": root}


def camera(params, yaw, width, height):
    """Reconstruct the T31 fixed-target camera; yaw is measured in pi units."""
    if any(isinstance(x, bool) or not isinstance(x, int) or x <= 0
           for x in (width, height)):
        raise ValueError("Image dimensions must be positive integers")
    dist = _finite(params["camDist"], "camDist")
    elev = _finite(params["camElev"], "camElev")
    fov = _finite(params["fov"], "fov")
    angle = _finite(_finite(yaw, "yaw") * math.pi, "yaw angle")
    if dist <= 0 or abs(elev) >= math.pi / 2 or not 0 < fov < math.pi:
        raise ValueError("Invalid T31 camera range")
    target = (0.0, 1.05, 0.0)
    offset = (dist * math.cos(elev) * math.sin(angle),
              dist * math.sin(elev), dist * math.cos(elev) * math.cos(angle))
    origin = tuple(target[a] + offset[a] for a in range(3))
    back = _unit(tuple(origin[a] - target[a] for a in range(3)))
    right = _unit((back[2], 0.0, -back[0]))
    up = _cross(back, right)
    forward = tuple(-x for x in back)
    return {"origin": list(origin), "forward": list(forward),
            "right": list(right), "up": list(up), "width": width,
            "height": height, "tan_half_fov": math.tan(fov / 2)}


def make_ray(cam, i, j):
    """Top-down pixel-center ray with projection-plane clips in ray units."""
    width, height = cam["width"], cam["height"]
    if (any(isinstance(x, bool) or not isinstance(x, int) for x in (i, j))
            or not 0 <= i < width or not 0 <= j < height):
        raise ValueError("Pixel index out of range")
    sx = (2 * (i + 0.5) / width - 1) * (width / height) * cam["tan_half_fov"]
    sy = (1 - 2 * (j + 0.5) / height) * cam["tan_half_fov"]
    direction = _unit(tuple(math.fsum((cam["forward"][a],
                                       sx * cam["right"][a],
                                       sy * cam["up"][a])) for a in range(3)))
    cosine = _dot(direction, cam["forward"])
    if not math.isfinite(cosine) or cosine <= 0:
        raise ValueError("Invalid forward camera ray")
    ray = {"origin": list(cam["origin"]), "direction": list(direction),
           "a": 0.05 / cosine, "b": 50.0 / cosine}
    _ray(ray)
    return ray


def geometric_pixels(cam, primitives):
    """Fixed grid plus eight index-selected center projections, never radiance."""
    width, height = cam["width"], cam["height"]
    if (width, height) != (256, 192):
        raise ValueError("The fixed geometric subset is defined at 256 x 192")
    selected = {}

    def add(i, j, tag):
        selected.setdefault((i, j), []).append(tag)

    for y in range(6):
        for x in range(8):
            add(16 + 32 * x, 16 + 32 * y, f"grid:{x}:{y}")
    for m in range(8) if primitives else ():
        index = m * (len(primitives) - 1) // 7
        center = _vector(primitives[index]["mu"], "sample center")
        delta = tuple(center[a] - cam["origin"][a] for a in range(3))
        depth = _dot(delta, cam["forward"])
        if not 0.05 <= depth <= 50.0:
            continue
        ndc_x = _dot(delta, cam["right"]) / (depth * cam["tan_half_fov"] * width / height)
        ndc_y = _dot(delta, cam["up"]) / (depth * cam["tan_half_fov"])
        pixel_x, pixel_y = (ndc_x + 1) * width / 2, (1 - ndc_y) * height / 2
        if not (0 <= pixel_x < width and 0 <= pixel_y < height):
            continue
        # floor(pixel coordinate) is the nearest pixel center (upper tie).
        add(math.floor(pixel_x), math.floor(pixel_y), f"source:{index}:sample:{m}")
    return [{"i": i, "j": j, "tags": selected[(i, j)]}
            for i, j in sorted(selected, key=lambda ij: (ij[1], ij[0]))]


def project(primitives, ids, ray, counters):
    """Convert selected 3D primitives to full-line 1D masses, without support clips."""
    origin, direction, a, b = _ray(ray)
    source_ids = list(ids)
    if len(set(source_ids)) != len(source_ids):
        raise ValueError("Duplicate projected source id")
    mu, sd, weight, colors = [], [], [], []
    for index in source_ids:
        center, h, k, color = _primitive(primitives, index)
        delta = tuple(center[axis] - origin[axis] for axis in range(3))
        z = _dot(delta, direction)
        perpendicular = math.hypot(*_cross(delta, direction))
        if not math.isfinite(z) or not math.isfinite(perpendicular):
            raise ValueError("Nonfinite projected geometry")
        if k == 0:
            q = 0.0
            _count(counters, "projection_zero_k_skips")
        else:
            ratio = perpendicular / h
            q = k * math.exp(-0.5 * ratio * ratio)
            _count(counters, "projection_exp")
            if q == 0:
                _count(counters, "projection_underflow_weights")
        if not math.isfinite(q) or q < 0:
            raise ValueError("Nonfinite or negative projected optical mass")
        mu.append(z)
        sd.append(h)
        weight.append(q)
        colors.append(list(color))
        _count(counters, "projected_primitives")
    _count(counters, "projection_calls")
    return {"a": a, "b": b, "mu": mu, "sd": sd, "weight": weight,
            "color": colors, "background_term": [0.0, 0.0, 0.0],
            "source_ids": source_ids}


def query(tree, ray, mass_budget, counters):
    """Charge conservative full-line node masses in deterministic left-first DFS."""
    origin, direction, _, _ = _ray(ray)
    budget = _finite(mass_budget, "mass budget")
    if budget < 0:
        raise ValueError("Mass budget must be nonnegative")
    nodes, root = tree["nodes"], tree["root"]
    kept, omitted, omitted_nodes = [], [], []
    charge = 0.0
    stack = [] if root is None else [root]
    _count(counters, "bvh_queries")
    while stack:
        node = nodes[stack.pop()]
        _count(counters, "bvh_node_visits")
        if node["sum_k"] == 0:
            bound = 0.0
            _count(counters, "bvh_zero_mass_nodes")
        else:
            delta = tuple(node["center"][a] - origin[a] for a in range(3))
            perpendicular = math.hypot(*_cross(delta, direction))
            padding = 1e-12 * (1 + math.hypot(*delta))
            distance = max(0.0, perpendicular - node["radius"] - padding)
            ratio = distance / node["max_h"]
            raw_bound = node["sum_k"] * math.exp(-0.5 * ratio * ratio)
            # Even underflowed positive-mass nodes receive a positive charge.
            bound = math.nextafter(raw_bound, math.inf)
            _count(counters, "bvh_bound_exp")
        proposed = charge if bound == 0 else math.nextafter(math.fsum((charge, bound)), math.inf)
        if proposed <= budget:
            charge = proposed
            omitted.extend(node["source_ids"])
            omitted_nodes.append({"node_id": node["id"], "mass_bound": bound})
            _count(counters, "bvh_pruned_nodes")
            _count(counters, "bvh_omitted_primitives", len(node["source_ids"]))
        elif node["left"] is None:
            kept.extend(node["source_ids"])
            _count(counters, "bvh_kept_leaves")
            _count(counters, "bvh_kept_primitives", len(node["source_ids"]))
        else:
            stack.append(node["right"])
            stack.append(node["left"])
    return {"kept_ids": sorted(kept), "omitted_ids": sorted(omitted),
            "omitted_nodes": omitted_nodes, "mass_bound": charge}
