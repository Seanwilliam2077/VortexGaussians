# T27 — local environment evidence and cost boundary

29 October 2026. One read-only [probe](probe_environment.py) ran in the already installed research Python environment. It completed in26.157 seconds under the150-second total cap; the sole installed-torch import/query used25.813 seconds under45 seconds. Two external executables actually ran: nvidia-smi and wsl. Missing executable locations were recorded without launching or installing replacements. There was no tensor, model, shader, native-extension compilation or training workload. CUDA queries may initialize driver/runtime state; this is not a zero-GPU-state-change claim.

## Observed resources

The public [summary](environment-summary.json) is derived from an ignored raw receipt whose byte count/hash is recorded there. It excludes user paths and full command/environment dumps.

| Item | Direct observation | Limit of inference |
|---|---|---|
| OS / Python | Windows11 AMD64; Python3.12.13;24 logical CPUs | Not the recipe's tested Linux/Python3.9 environment |
| Host RAM |67,773,509,632 bytes total;27,322,261,504 available at capture | Availability changes; not a training-memory measurement |
| Workspace disk |120,481,173,504 bytes free on429,497,774,080-byte volume | Archive extraction, environment/build and output peak storage remain unknown |
| GPU | RTX5070 Laptop GPU;8151MiB total and7891MiB free in driver query; driver595.71 | About8GB nominal capacity; no claim that the prescribed scene fits |
| Installed PyTorch |2.11.0+cu128; compiled CUDA12.8; CUDA available; one device; capability12.0 | Device discovery succeeds; no model/kernel/compiler or extension compatibility test |
| Tool locations | nvcc, cmake, ninja executable and cl not found in PATH/probed conventional locations; vswhere absent at its checked installer location | Not a full-disk absence proof or evidence that installation is impossible |
| WSL | Existing wsl executable returned1 and stated WSL is not installed | No distribution initialized or installation attempted |

Installed metadata identifies NumPy2.4.6, Pillow12.2.0, OpenCV5.0.0.93, tqdm4.68.1, matplotlib3.11.0 and ninja1.13.0. Ninja distribution metadata being present while its executable is not found by this process is a PATH/discovery distinction. torchvision, torchaudio, SciPy, plyfile, slangtorch, wandb, lpips and the named renderer/KNN/fused-SSIM distributions were not found in this selected environment's metadata. Distribution absence does not exclude an arbitrary manually installed source module elsewhere; no broad disk search occurred.

## Relation to the recipe

The [recipe audit](RECIPE_CONTRACT.md) records Python3.9.20, torch2.0.1/CUDA11.7 and SlangTorch1.3.7 in the published installer, plus native submodules and Bash/Unix environment hooks. Those requirements do not match this selected environment. T26 established that importing the renderer/native sort requests compilation/loading, so an available PyTorch device alone does not make the current setup ready.

No external CUDA/Slang/compiler compatibility documentation was fetched in this task. Therefore the CUDA11.7 versus12.8 and GPU-capability difference is a compatibility question, not a proven architecture impossibility or a reason to change dependency versions silently. Native-Windows support, a viable compiler/SDK route, package ABI compatibility and a minimal actual build remain unverified. WSL setup or an isolated environment would be new installation work, not a continuation of this completed probe.

## What cost can be stated now

The selected data archive advertises12,535,427,936 compressed bytes; see [data-source evidence](DATA_SOURCE.md). This is about12.54 decimalGB. The current disk snapshot exceeds that compressed amount, but no extracted-size, temporary-build, environment or checkpoint-size peak is known. No download bandwidth or duration was measured. No process load was used to infer training throughput.

Full expenditure for a subsequent qualification would include observation acquisition/verification/extraction, environment/compiler setup, extension builds/cache warmup, initialization, training and save/reload, camera/model extraction, accurate-reference qualification, and evaluation. Setup/training must be reported separately from per-delivery rendering/integration costs. T22's millisecond CPU batches cannot predict this training time or GPU memory use.

**Decision for the existing setup: not ready to execute the official training recipe.** GPU absence is not the issue; installed prerequisites, tested platform/ABI compatibility, data conditions and bounded resource estimates remain unresolved. This does not prove an8GB device cannot support a carefully specified workload. No training/install/download protocol is prepared here, and no existing environment is modified.

The smallest useful next evidence is a bounded compatibility/installation-feasibility check for this actual Windows/GPU/toolchain combination, with data-use conditions handled explicitly. It should produce a concrete supported setup/cost decision before any large download or training. The raw receipt must not be presented as a performance benchmark.
