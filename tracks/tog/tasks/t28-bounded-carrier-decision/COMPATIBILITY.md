# T28 — bounded compatibility decision

29 October 2026. **The fixed native-Windows route is not qualified by this bounded evidence.** This is an unresolved source/build contract, not proof of incompatibility or an 8GB impossibility. This reviewer made no external requests, imports, probes or installation changes. The external phase is closed; this note evaluates its saved evidence and inherited T24–T27 source inspections.

The candidate retains torch2.11+cu128 and SlangTorch1.3.7, with an isolated environment, CUDA12.8 toolkit and compatible MSVC. It deliberately differs from the published Python3.9/torch2.0.1/CUDA11.7 recipe. The existing successful torch device query does not qualify this renderer.

The [CUDA12.8 Windows guide](https://docs.nvidia.com/cuda/archive/12.8.0/cuda-installation-guide-microsoft-windows/index.html), saved excerpt L27–46, lists Windows11 releases and native x86_64 support for MSVC193x/Visual Studio2022 and MSVC192x/Visual Studio2019. This identifies documented compiler families; it does not establish their presence here, compatibility with this project's generated bindings, or a successful extension build. T27 did not locate nvcc/cl in its bounded checks.

The [Blackwell compatibility guide](https://docs.nvidia.com/cuda/blackwell-compatibility-guide/index.html), saved excerpt L12–26 and L37–44, distinguishes compatible cubins from forward-compatible PTX that the driver can JIT. Older-toolkit applications can work when suitable PTX is included; architecture-conditional PTX has exceptions. Therefore “CUDA11.7 is necessarily impossible on Blackwell” is unsupported. This renderer's actual generated/bundled GPU code was not inspected or executed, so the general mechanism establishes no application-level compatibility.

[SlangTorch1.3.7 metadata](https://pypi.org/pypi/slangtorch/1.3.7/json) declares Python>=3.7 and torch>=1.1.0, plus filelock, hatchling and ninja. It advertises a 19,312,541-byte `py3-none-any` wheel and OS-independent classification. These are packaging/dependency declarations, not a tested Windows/Python3.12/torch2.11/CUDA12.8 matrix or evidence that generated native bindings share the required ABI. No wheel or source archive was acquired.

The metadata-linked `shader-slang/slang-python` tags request returned connector HTTP400/INVALID_ARGUMENT: the endpoint was rejected as unsupported, with no repository content. This is not evidence that the repository/version is absent. The linked [Slang documentation page](https://shader-slang.com/slang/user-guide/a1-02-slangpy.html) returned an accessibility error. Neither was retried. Consequently the fixed package's source revision, native-binding generation path and platform/toolchain assumptions remain unresolved.

Inherited source evidence adds concrete untested obligations: Slang `loadModule`/`launchRaw`/backward bindings; the runtime-built CUB sort extension; simple-knn; and the classic rasterizer imported by the renderer package. The [T27 recipe](../t27-workload-feasibility/RECIPE_CONTRACT.md) also installs fused-SSIM and uses Bash/Unix hooks. None has been built against the retained torch. Their existence identifies checks, not observed API/ABI failures.

Memory readiness is separately unknown. At main pin `dd175d52938264770a783cbb7929e20572675544`, `arguments/__init__.py` L55 defaults image storage to CUDA; `scene/cameras.py` L38–45 transfers observations/masks; `scene/__init__.py` L72–76 constructs both camera sets. Model, optimizer, temporary rendering and resident-image costs therefore matter. Device capacity alone cannot predict fit, peak storage or training duration.

The remaining version/source gap would require further dependency investigation beyond this closed decision. Under the frozen protocol, close this acquisition route rather than presenting an installation/training procedure as ready. Reopening needs concrete usable carrier/environment evidence. No inference here changes T22's scientific gates or establishes a TOG contribution.

Saved evidence SHA256 (third-party bytes remain ignored):

| File | SHA256 |
|---|---|
| `acquired/nvidia-guides.web.txt` | `344027bb54a6c1ab4bfdf8243f729a17a2fed12291c7895a370766f645593638` |
| `acquired/slangtorch-1.3.7.json` | `7430ada9d1eaa7b604768e9cc8f64bc6b0f8473911f0932f6428f9e6305365a8` |
| `acquired/slang-tags-error.txt` | `057f31fbf5e0244c0b80e46027d0a6ac619dee619f775a71ec728945a64a4896` |
| `acquired/slang-document-error.web.txt` | `b07f8f3a7bac6e1962dd05c96fe64987e482b8c7cca1dd188ed6b5cc590f5ac8` |
