"""Check the published Bonsai stop and analytical native footprint bound without a checkpoint download."""
import json
from math import dist, isclose, sqrt
from pathlib import Path


def verify():
    here = Path(__file__).resolve().parent
    record = json.loads((here/"STATIC.json").read_bytes())
    acquisition = json.loads((here/"ACQUISITION.json").read_bytes())
    assert acquisition["status"] == "complete"
    assert sum(m["compressed"] for m in acquisition["members"]) <= acquisition["transfer"]["normal_bytes"] <= 262000000
    assert record["hashes"] == {m["local_filename"]:m["sha256"] for m in acquisition["members"]}
    assert record["status"] == "closed_coincident_primitive"
    assert record["material_count"] == 1244819 and record["camera_ids"] == [0,146]
    first, second = record["rays"]
    assert first["id"] == second["id"] == 867267
    for ray in (first,second):
        assert 0 <= ray["prior_opacity"] < .5 <= ray["crossing_opacity"] <= 1
        assert ray["contributors"] >= ray["front_to_back_rank"] > 0
    diag = record["diagnosis"]
    width, height = diag["quarter_view_size"]
    center_x = diag["quarter_projected_mean"][0]
    distance_outside = max(0., -.5-center_x, center_x-(width-.5))
    conservative_radius = sqrt(2)*max(width,height)/2
    assert distance_outside == diag["center_horizontal_distance_outside_viewport"]
    assert conservative_radius == diag["any_quad_vertex_horizontal_displacement_upper_bound"]
    assert distance_outside > conservative_radius and diag["outside_even_native_bounding_quad"]
    ray_separation = dist(*diag["source_points_on_the_two_rays_at_shared_depth"])
    assert ray_separation > 0 and isclose(ray_separation,diag["source_distance_between_these_points"])
    assert diag["reprojection_max_abs_px"]<1e-5
    assert record["native_simulations"] == record["native_renders"] == record["performance_trials"] == 0
    return record["status"], ray_separation, distance_outside, conservative_radius


if __name__ == "__main__":
    print(*verify())
