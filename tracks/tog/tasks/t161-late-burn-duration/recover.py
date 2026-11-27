"""Recover a late burn duration from recorded native first-debit events."""
import argparse
import hashlib
import json
from pathlib import Path
import zlib

import numpy as np


HERE = Path(__file__).resolve().parent
SLOW = HERE.parent / "t160-burning-plateau" / "evidence"
FAST = HERE.parent / "t151-surface-preignition" / "evidence"
EVENT = np.dtype([("texel", "<u4"), ("first", "<u2"), ("fuel", "<u2")])
FAST_RATE = np.float32(1 / 5)
SLOW_RATE = np.float32(1 / 10)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_arm(folder, name):
    meta = json.loads((folder / f"{name}.json").read_bytes())
    if meta["status"] != "complete" or meta["frames"] != 36:
        raise ValueError(f"{name} trajectory was not completed through frame 36")
    paths = [folder / f"{name}{suffix}" for suffix in (".jsonl", "-atlas.zlib", ".json", "-scene.json")]
    rows = [json.loads(line) for line in paths[0].read_bytes().splitlines()]
    updates = [row for row in rows if row["kind"] == "update"]
    assert [row["index"] for row in updates] == list(range(meta["updates"]))
    states = {}
    state_rows = {}
    previous = None
    with paths[1].open("rb") as handle:
        for row in rows:
            if "atlas" not in row:
                continue
            info = row["atlas"]
            assert info["dtype"] == "<f2" and info["shape"][-1] == 4
            assert handle.tell() == info["offset"]
            delta = np.frombuffer(zlib.decompress(handle.read(info["size"])), dtype="u1")
            raw = delta if previous is None else previous ^ delta
            assert sha(raw) == info["sha256"]
            n = row["index"]
            assert n not in states
            states[n] = raw.view("<u2").reshape(*info["shape"]).reshape(-1, 4)
            state_rows[n] = row
            previous = raw
        assert not handle.read(1)
    digests = {p.name: sha(p.read_bytes()) for p in paths}
    return meta, updates, states, state_rows, digests


def half_word(x):
    return np.maximum(x, 0).astype("<f2").view("<u2")


def transition(words, rate, dt):
    x = words.view("<f2").astype("<f4")
    separate = half_word(x - rate * dt)
    # The product of two binary32 inputs is exact in binary64. Neighbors
    # of the binary64 difference bracket the exact fused expression.
    difference = x.astype("<f8") - float(rate) * float(dt)
    fused_lo = half_word(np.nextafter(difference, -np.inf).astype("<f4"))
    fused_hi = half_word(np.nextafter(difference, np.inf).astype("<f4"))
    ambiguous = (separate != fused_lo) | (separate != fused_hi)
    return separate, ambiguous


def sparse_history(states, updates):
    count = len(updates)
    assert count < 65535 and sorted(states) == list(range(count + 1))
    initial = states[0]
    assert len(initial) < 2**32
    has_event = np.zeros(len(initial), dtype=bool)
    eligible = initial[:, 2].view("<f2") > 0.5
    initial_fuel = initial[:, 0].view("<f2")[eligible]
    assert initial_fuel.size and initial_fuel.min() >= 0.75 and initial_fuel.max() <= 1.25
    assert not initial[:, [1,3]].any()
    batches = []
    steps = np.array([r["dt_f32"] for r in updates], dtype="<f4")
    lower = 0.75
    first_guard_failure = first_slow_mismatch = None
    source_transitions = source_ambiguous = 0
    for i, (row, dt) in enumerate(zip(updates, steps)):
        assert float(dt) == row["dt_f32"] and row["rate_f32"] == float(SLOW_RATE)
        assert dt == np.float32(row["dt"]) and 0 < dt <= np.float32(1 / 24)
        if lower is not None:
            next_lower = np.nextafter(lower - float(FAST_RATE) * float(dt) - 2**-10 - 2**-20, -np.inf)
            lower = float(next_lower) if next_lower > float(np.float32(0.15)) else None
            if lower is None:
                first_guard_failure = i
        assert row["lower_after"] == lower
        source = states[i]
        values = source.view("<f2")
        assert np.isfinite(values).all()
        assert not (values[:, 1] < 0).any() and not values[:,3].any()
        burning = (values[:, 2] > 0.5) & (values[:, 1] >= 1) & (values[:, 0] > 0)
        assert not np.any(has_event & ~burning)
        new = np.flatnonzero(burning & ~has_event)
        assert np.array_equal(source[new,0], initial[new,0])
        if len(new):
            batch = np.empty(len(new), dtype=EVENT)
            batch["texel"], batch["first"], batch["fuel"] = new, i, source[new, 0]
            batches.append(batch)
            has_event[new] = True
        predicted = source[:, 0].copy()
        next_words, ambiguous = transition(source[burning, 0], SLOW_RATE, dt)
        predicted[burning] = next_words
        source_transitions += int(burning.sum())
        source_ambiguous += int(ambiguous.sum())
        wrong = np.flatnonzero(predicted != states[i+1][:,0])
        if len(wrong) and first_slow_mismatch is None:
            idx = int(wrong[0])
            first_slow_mismatch = dict(boundary=i+1, texel=idx, cpu=int(predicted[idx]), native=int(states[i+1][idx,0]))
    all_events = np.concatenate(batches) if batches else np.empty(0, dtype=EVENT)
    return all_events, steps, dict(guard_first_rejected_input=first_guard_failure, final_lower_bound=lower,
            slow_transition_count=source_transitions, slow_fma_ambiguous=source_ambiguous,
            first_slow_native_mismatch=first_slow_mismatch)


def query(source, events, dts, n):
    active = events[events["first"] < n]
    keys = (active["first"].astype("<u4") << 16) | active["fuel"]
    groups, members = np.unique(keys, return_inverse=True)
    born = groups >> 16
    original = (groups & 65535).astype("<u2")
    words = original.copy()
    times32 = np.zeros(len(groups), dtype="<f4")
    times64 = np.zeros(len(groups), dtype="<f8")
    ambiguous = 0
    first_ambiguous = None
    for i, dt in enumerate(dts[:n]):
        mask = born <= i
        if not np.any(mask):
            continue
        changed, uncertain = transition(words[mask], FAST_RATE, dt)
        if np.any(uncertain) and first_ambiguous is None:
            g = np.flatnonzero(mask)[np.flatnonzero(uncertain)[0]]
            first_ambiguous = dict(input=i, dt=float(dt), initial_word=int(original[g]), first=int(born[g]),
                                   input_word=int(words[g]))
        words[mask] = changed
        ambiguous += int(uncertain.sum())
        times32[mask] += dt
        times64[mask] += float(dt)
    starting = original.view("<f2")
    elapsed64 = half_word(starting.astype("<f8") - float(FAST_RATE) * times64)
    elapsed32 = half_word(starting.astype("<f4") - FAST_RATE * times32)
    at = active["texel"]
    slow = source[at,0].view("<f2").astype("<f4")
    x0 = active["fuel"].view("<f2").astype("<f4")
    ratio = half_word(x0 - (FAST_RATE / SLOW_RATE) * (x0 - slow))
    estimates = dict(step_replay=words[members], elapsed64=elapsed64[members], elapsed32=elapsed32[members],
                     single_frame_ratio=ratio)
    work = dict(lit_texels=len(active), cohorts=len(groups), scalar_updates_ungrouped=int((n-active["first"].astype(int)).sum()),
                scalar_updates_grouped=int((n-born.astype(int)).sum()), scatter_writes=len(active),
                fma_ambiguous_group_transitions=ambiguous, first_fma_ambiguity=first_ambiguous)
    return at, estimates, work


def witness(n, idx, channel, predicted, expected, source, events):
    event = events[events["texel"] == idx]
    value = dict(boundary=n, texel=int(idx), channel="xyzw"[channel], native_word=int(expected),
                 predicted_word=int(predicted), primary_word=int(source[idx, channel]))
    if len(event):
        value.update(first_native_debit=int(event["first"][0]), initial_fuel_word=int(event["fuel"][0]))
    return value


def reconstruct_atlas(primary_atlas, event_path, dt_path, boundary):
    """Construct a 5 s atlas using only a 10 s endpoint, first-debit events and dt."""
    if primary_atlas.dtype != np.dtype("<f2") or primary_atlas.shape[-1] != 4:
        raise ValueError("Expected the native binary16 RGBA atlas")
    if Path(event_path).stat().st_size % EVENT.itemsize or Path(dt_path).stat().st_size % 4:
        raise ValueError("Truncated native event or step packet")
    events = np.fromfile(event_path, dtype=EVENT)
    dts = np.fromfile(dt_path, dtype="<f4")
    if not 0 <= boundary <= len(dts):
        raise ValueError("Invalid native update boundary")
    values = np.ascontiguousarray(primary_atlas).copy()
    target = values.view("<u2").reshape(-1, 4)
    if len(events) and (events['texel'].max() >= len(target) or events['first'].max() >= len(dts)
                        or len(np.unique(events['texel'])) != len(events)):
        raise ValueError("Incompatible event indices")
    initial = events['fuel'].view('<f2')
    if not np.isfinite(initial).all() or np.any((initial < 0.75) | (initial > 1.25)):
        raise ValueError("Unexpected initial curtain fuel")
    lower = 0.75
    for dt in dts[:boundary]:
        if not 0 < dt <= np.float32(1/24):
            raise ValueError("Unsupported native substep")
        lower = np.nextafter(lower - float(FAST_RATE)*float(dt) - 2**-10 - 2**-20, -np.inf)
        if lower <= np.float32(.15):
            raise ValueError("Burning plateau no longer certified")
    active = events[events["first"] < boundary]
    if not len(active):
        return values
    keys = (active["first"].astype("<u4") << 16) | active["fuel"]
    groups, members = np.unique(keys, return_inverse=True)
    born = groups >> 16
    fuel = (groups & 65535).astype("<u2")
    for i, dt in enumerate(dts[:boundary]):
        mask = born <= i
        if not mask.any():
            continue
        changed, uncertain = transition(fuel[mask], FAST_RATE, dt)
        if uncertain.any():
            raise ValueError("Sibling half word depends on shader contraction")
        fuel[mask] = changed
    target[active["texel"], 0] = fuel[members]
    return values


def score(out, write):
    primary_meta, primary_steps, primary, primary_rows, primary_hashes = read_arm(SLOW, "extended")
    # No 5 s data enters the event packet. Its contents can be extracted at authoring time,
    # before a second duration has been specified.
    sparse, steps, audit = sparse_history(primary, primary_steps)
    event_path, dt_path = out / "first-debit.bin", out / "dt-f32.bin"
    packets = [(event_path, sparse.tobytes()), (dt_path, steps.tobytes())]
    if write:
        out.mkdir(parents=True, exist_ok=True)
        for path, blob in packets:
            path.write_bytes(blob)
    for path, blob in packets:
        assert path.read_bytes() == blob
    fast_meta, fast_steps, oracle, oracle_rows, fast_hashes = read_arm(FAST, "default")
    assert primary_meta["pin"] == fast_meta["pin"] and primary_meta["adapter"] == fast_meta["adapter"]
    primary_scene = json.loads((SLOW / "extended-scene.json").read_bytes())
    fast_scene = json.loads((FAST / "default-scene.json").read_bytes())
    assert primary_scene["sections"]["spread"]["burn_time"] == 10
    assert fast_scene["sections"]["spread"]["burn_time"] == 5
    primary_scene["sections"]["spread"]["burn_time"] = 5
    assert primary_scene == fast_scene
    first_unaligned = next((i for i, (a, b) in enumerate(zip(primary_steps, fast_steps))
                              if any(a[k] != b[k] for k in ("index", "frame", "substep", "dt", "forcing"))), None)
    aligned = min(len(primary_steps), len(fast_steps)) if first_unaligned is None else first_unaligned
    common = sorted(n for n in set(primary).intersection(oracle) if n <= aligned)
    method_names = ("step_replay", "elapsed64", "elapsed32", "single_frame_ratio")
    first_wrong = {m: None for m in method_names}
    public_mismatch = None
    results = []
    active_unique = np.unique(sparse["texel"])
    assert len(active_unique) == len(sparse)
    for n in common:
        source, reference = primary[n], oracle[n]
        assert source.shape == reference.shape
        assert (primary_rows[n]["frame"], primary_rows[n]["substep"]) == (oracle_rows[n]["frame"], oracle_rows[n]["substep"])
        at, candidates, work = query(source, sparse, steps, n)
        positive = ((source[:,1].view("<f2") >= 1) & (source[:,2].view("<f2") > .5)
                    & (source[:,0].view("<f2") >= np.float16(.1501)))
        row = dict(index=n, frame=oracle_rows[n]["frame"], substep=oracle_rows[n]["substep"],
                   native_scalar_difference=int(np.count_nonzero(source[:,0] != reference[:,0])),
                   primary_positive_plateau_texels=int(positive.sum()), work=work, comparisons={})
        for method, changed_words in candidates.items():
            target = source.copy()
            target[at, 0] = changed_words
            errors = target != reference
            differences = int(errors.sum())
            row["comparisons"][method] = dict(different_words=differences, different_texels=int(errors.any(axis=1).sum()),
                                             atlas_sha256=sha(target))
            if differences and first_wrong[method] is None:
                i, c = np.argwhere(errors)[0]
                first_wrong[method] = witness(n, i, c, target[i,c], reference[i,c], source, sparse)
        row["oracle_sha256"] = oracle_rows[n]["atlas"]["sha256"]
        # Verify the standalone endpoint consumer as used by T162.
        raw_shape = primary_rows[n]["atlas"]["shape"]
        try:
            public = reconstruct_atlas(source.view("<f2").reshape(raw_shape), event_path, dt_path, n)
            if sha(public) != row["comparisons"]["step_replay"]["atlas_sha256"] and public_mismatch is None:
                public_mismatch = dict(boundary=n, stage="differs_from_scalar_recovery")
        except ValueError as exc:
            if public_mismatch is None:
                public_mismatch = dict(boundary=n, stage=str(exc))
        results.append(row)
    totals = {m: dict(exact_boundaries=sum(r["comparisons"][m]["different_words"] == 0 for r in results),
                      total_mismatching_words=sum(r["comparisons"][m]["different_words"] for r in results),
                      first_failure=first_wrong[m]) for m in method_names}
    work_totals = {k: sum(r["work"][k] for r in results) for k in
                   ("scalar_updates_ungrouped", "scalar_updates_grouped", "scatter_writes", "fma_ambiguous_group_transitions")}
    native_positive = [r["index"] for r in results if r["native_scalar_difference"] and r["primary_positive_plateau_texels"]]
    success = (len(common) == len(oracle) and aligned == len(primary_steps) == len(fast_steps)
               and results and results[-1]["frame"] == 36 and native_positive
               and audit["guard_first_rejected_input"] is None and not audit["slow_fma_ambiguous"]
               and audit["first_slow_native_mismatch"] is None and not work_totals["fma_ambiguous_group_transitions"]
               and not totals["step_replay"]["total_mismatching_words"] and public_mismatch is None)
    size = primary[0].nbytes
    return dict(status="pass" if success else "not_qualified", shape=primary_rows[0]["atlas"]["shape"],
                source_rate=float(SLOW_RATE), demanded_rate=float(FAST_RATE), source_pin=primary_meta["pin"],
                input_sha256={**primary_hashes, **fast_hashes}, source_updates=len(primary_steps), oracle_updates=len(fast_steps),
                first_unaligned_input=first_unaligned, aligned_updates=aligned, available_oracle_boundaries=len(oracle),
                comparable_boundaries=common, positive_divergent_boundary_indices=native_positive,
                standalone_first_implementation_error=public_mismatch, source_audit=audit,
                packet=dict(events=len(sparse), event_bytes=sparse.nbytes, event_sha256=sha(sparse),
                            dt_bytes=steps.nbytes, dt_sha256=sha(steps), total_bytes=sparse.nbytes+steps.nbytes,
                            source_endpoint_bytes=size, sibling_materialization_bytes=size,
                            source_history_full_atlas_decoded_bytes=sum(v.nbytes for v in primary.values()),
                            offline_event_scan_texels=(size//8)*len(steps)),
                all_separate_request_work=work_totals, last_request_work=results[-1]["work"] if results else None,
                summary=totals, boundaries=results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=HERE / "evidence")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    report = score(args.out, args.write)
    output = args.out / "SCORE.json"
    if args.write:
        output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf8")
    else:
        assert json.loads(output.read_bytes()) == report
    print(report["status"], len(report["comparable_boundaries"]), report["packet"]["total_bytes"], report["last_request_work"])
