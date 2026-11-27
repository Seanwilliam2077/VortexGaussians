"""Verify the original native scalar contract under the T147 receipt schema."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
if __name__ == "__main__":
    script = HERE.parent / "t145-bonsai-crop-choice/verify.py"
    spec = importlib.util.spec_from_file_location("original_scalar_verifier", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main(HERE,"t147-bonsai-embedded-scalar-scissor-v1")
