"""Apply the frozen T111 independent ledger reduction to the registered camera IDs."""
import hashlib
from prepare import HERE, write

worker = HERE.parent/"t111-playground-shot-choice/reference.py"
src = worker.read_bytes()
if hashlib.sha256(src).hexdigest() != "2a3d13bb417fe286a65700f47ef91d80a46ab72b41e04ff3c81414a4de8fe8d7":
    raise ValueError("Unexpected reference implementation")
module = {"__name__": "t121_native_reducer"}
exec(compile(src, str(worker), "exec"), module)
if __name__ == "__main__":
    result = module["build"]()
    result["schema"] = "t121-independent-native-reference-v1"
    write(HERE/"REFERENCE.json", result)
    print("Independent 90-frame curves", [(q["arm"], q["camera"], q["first_frame"]) for q in result["queries"]])
