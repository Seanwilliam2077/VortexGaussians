"""CPU image metrics, independent of Torch and of target-generation recipes."""
import numpy as np


def crop(a, roi):
    x0, y0, x1, y1 = roi
    return a[..., y0:y1, x0:x1]


def compare(actual, reference, relative, absolute, signal_min):
    rms = np.sqrt(np.mean((actual-reference)**2, axis=(-2, -1)))
    signal = np.sqrt(np.mean(reference**2, axis=(-2, -1)))
    rel = np.divide(rms, signal, out=np.full_like(rms, np.inf), where=signal > 0)
    passed = (rms <= absolute) & (rel <= relative) & (signal >= signal_min)
    return {"absoluteRMS": rms.tolist(), "relativeRMS": [float(x) if np.isfinite(x) else None for x in rel],
            "referenceRMS": signal.tolist(), "passedFrames": passed.tolist(), "passed": bool(passed.all())}


def motion(actual, approved, roi):
    a, b = crop(approved, roi), crop(actual, roi)
    x = np.arange(roi[0], roi[2], dtype=np.float64)+.5
    ma, mb = a.sum((-2, -1)), b.sum((-2, -1))
    if np.any(ma <= 0) or np.any(mb <= 0):
        return {"defined": False, "reason": "zero alpha mass; centroid undefined"}
    ca = (a*x).sum((-2, -1))/ma
    cb = (b*x).sum((-2, -1))/mb
    return {"defined": True, "shiftPixels": (cb-ca).tolist(), "alphaRatio": (mb/ma).tolist(),
            "approvedSignal": np.sqrt(np.mean(a*a, axis=(-2, -1))).tolist(),
            "actualSignal": np.sqrt(np.mean(b*b, axis=(-2, -1))).tolist()}


def evaluate(frames, approved, target, spec):
    task, gates = spec["task"], spec["task"]["quality"]
    rows = np.asarray(task["frames"], dtype=np.int64)-16
    actual, reference = np.asarray(frames, dtype=np.float64)[rows], np.asarray(approved, dtype=np.float64)[rows]
    if frames.shape != (25, 64, 64) or approved.shape != frames.shape:
        raise ValueError("Full frames/approved must have shape (25,64,64)")
    expected = (len(rows), task["edit_roi"][3]-task["edit_roi"][1], task["edit_roi"][2]-task["edit_roi"][0])
    if target.shape != expected:
        raise ValueError("Target must contain declared frame IDs and edit ROI: " + str(expected))
    for value in (actual, reference, target):
        if not np.isfinite(value).all() or np.any(value < 0) or np.any(value > 1):
            raise ValueError("Alpha inputs must be finite and in [0,1]; no clipping is performed")
    protected = [compare(crop(actual, roi), crop(reference, roi), gates["protect_relative"], gates["protect_absolute"], gates["signal_min"])
                 for roi in task["protected_rois"]]
    edit = compare(crop(actual, task["edit_roi"]), target, gates["edit_relative"], gates["edit_absolute"], gates["signal_min"])
    diagnostics = {name: motion(actual, reference, task["motion_diagnostics"][name+"_roi"]) for name in ("upper", "lower")}
    report = {"frameIds": task["frames"], "protected": protected, "edit": edit,
              "pixelQualityPassed": edit["passed"] and all(p["passed"] for p in protected),
              "motionDiagnostics": diagnostics, "semanticGate": {"status": "not_defined", "passed": None},
              "limitation": "Alpha centroids are not material paths; pixel agreement is not verified artist intent or physical truth."}
    if task["semantic_gate"] == "r22_frozen_negative":
        upper, lower = diagnostics["upper"], diagnostics["lower"]
        if upper["defined"] and lower["defined"]:
            u, l, ratio = (np.asarray(upper["shiftPixels"]), np.asarray(lower["shiftPixels"]), np.asarray(upper["alphaRatio"]))
            hits = (u >= 2) & ((u-l) >= 1) & (ratio >= .8) & (ratio <= 1.2)
            signal = all(min(r[k]) >= .01 for r in diagnostics.values() for k in ("approvedSignal", "actualSignal"))
            report["semanticGate"] = {"status": "frozen_R22", "passed": bool(signal and hits.sum() >= 8),
                                      "passedFrames": hits.tolist(), "frameCount": int(hits.sum()), "maximumUpperShift": float(u.max()),
                                      "thresholdPixels": 2, "minimumBendPixels": 1, "minimumFrames": 8, "signalPassed": signal}
        else:
            report["semanticGate"] = {"status": "frozen_R22", "passed": False, "reason": "undefined centroid"}
    return report
