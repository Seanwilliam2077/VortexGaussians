# Extract the T131 native checkpoint

The 40,149-byte archive contains the neutral frame-1 cache and the supplementary feedback used by the experiment. The 52,025-byte native frame was reconstructed on the CPU with Blackbody's writer. Its SHA-256 matches the digest independently observed by all three GPU workers. The feedback bytes likewise match the original readback digest. The cache marker, native cache metadata and sidecar JSON were recreated from the fixture and recorded metadata. The original temporary files were removed after the experiment. [Download archive](neutral-frame1.zip) · [Package SHA-256](SHA256SUMS) · [Original measurements](../evidence/reference.json)

From this directory, extract to a new folder using the standard library.

```sh
python -m zipfile -e neutral-frame1.zip extracted
```

Use `extracted` as the cache root with `make_fixture(Path("extracted"))` from the T131 operator. The pinned Blackbody `SimCache` opens `extracted/final` read-only with signature `ce4eeec10ec82219`, lists exactly one checkpoint at frame 1, and decodes `f+0000001.bbc`. The root also contains `feedback.bin` and `feedback.json` for the separate supplemented control. [T131 operator](../run.py)

To check the archive without any GPU, use the T130 Python runtime and the pinned Blackbody source checkout at `e2ac951dbfabc6060073943e4c344439ac5f4555`. The first command validates the supplied archive, exact historical payload hashes, all native array leaves and readonly frame discovery. The second rebuilds a new deterministic archive from the published measurements, validates it and prints its SHA-256.

```sh
python build.py --source BLACKBODY_CHECKOUT
python build.py --source BLACKBODY_CHECKOUT --build --archive new-checkpoint.zip
```
