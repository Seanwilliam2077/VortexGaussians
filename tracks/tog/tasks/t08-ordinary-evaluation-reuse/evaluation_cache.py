"""One detached evaluation, exact returned-x matching, no solver mathematics."""


def byte_equal(torch, left, right):
    if left.dtype != right.dtype or left.shape != right.shape or left.device != right.device:
        return False
    return torch.equal(left.detach().contiguous().reshape(-1).view(torch.uint8),
                       right.detach().contiguous().reshape(-1).view(torch.uint8))


def fixed_identity(torch, model, inputs, contract):
    """Snapshot immutable model/input identity and in-place mutation versions.

    x/q are deliberately excluded: L-BFGS mutates x and exact x is checked
    separately. The pinned core's model attributes are static between calls.
    """
    def identity(value):
        if isinstance(value, torch.Tensor):
            return ("tensor", id(value), value._version, tuple(value.shape), str(value.dtype), str(value.device))
        if isinstance(value, dict):
            return ("dict", tuple((key, identity(value[key])) for key in sorted(value)))
        if isinstance(value, (list, tuple)):
            return (type(value).__name__, tuple(identity(item) for item in value))
        if isinstance(value, (str, int, float, bool, type(None))):
            return (type(value).__name__, value)
        return (type(value).__name__, repr(value))
    return (contract, id(model), identity(vars(model)), identity(inputs))


class EvaluationCache:
    def __init__(self, torch, identity_fn):
        self.torch, self.identity_fn = torch, identity_fn
        self.entry = None
        self.invalidations = 0
        self.last_invalidation = "initial_empty"

    def store(self, x, output, identity_before):
        if self.identity_fn() != identity_before:
            self.invalidate("inputs_changed_during_closure")
            return False
        self.entry = {"identity": identity_before, "x": x.detach().clone(),
                      **{key: output[key].detach().clone() for key in ("frames", "velocity", "density")}}
        return True

    def lookup(self, returned_x):
        if self.entry is None:
            return None, "empty"
        if self.entry["identity"] != self.identity_fn():
            return None, "model_or_input_identity_mismatch"
        if not byte_equal(self.torch, returned_x, self.entry["x"]):
            return None, "returned_x_mismatch"
        return {key: self.entry[key] for key in ("frames", "velocity", "density")}, "hit"

    def invalidate(self, reason):
        self.entry = None
        self.invalidations += 1
        self.last_invalidation = reason

    @property
    def payload_bytes(self):
        return 0 if self.entry is None else sum(self.entry[k].numel()*self.entry[k].element_size()
                                              for k in ("x", "frames", "velocity", "density"))


def closure_slot_available(used, budget):
    return used < budget-2  # possible acceptance miss + mandatory final


def acceptance_slot_available(used, budget):
    return used < budget-1  # mandatory final


def final_slot_available(used, budget):
    return used < budget
