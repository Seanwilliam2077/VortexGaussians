# T17 execution failure and one allowed repair

29 October 2026. The 28 October protocol, its pre-input dependency amendment and all 48 fixtures remain unchanged. The protocol/derivation/implementation were real progress during the preceding goal turn; execution had not yet occurred. The continued goal is active, independently of the previously deleted hourly automation.

## Attempt 1: retained initialization failure

Input generation completed before any solve. `inputs.json` SHA256 is `5cccf0238c679e14bc50e67d2d24726a58295b484b1d3464bf77d4eca0491cb7`. The original script SHA256 is `8d0e4221ba82708e14f2db9764d35f4ed48cf1ae3dc82f857cdb7823f0e14953`; its exact bytes are preserved in `run-01/source-qualification.py`. Protocol SHA256 is `4c631c90d08d1e5b9ac19ebc6e52cbd2c902c267af105ccbedeb1cccc292586c`.

The first supervised attempt exited with native Windows child status `3228369023` (`0xc06d007f`) after 6.061169 seconds. It created an empty `cases` directory but no progress or case result. The supervisor returned a failure; no Python exception record was produced. All three source/input hashes stayed unchanged. This attempt is a failure, not a discarded warm-up or a completed qualification.

Root initially inspected files only and missed the empty directory. The implementation author caught that distinction during source review: the worker creates `cases` after imports and input validation, then generates GL nodes before opening its progress stream. Thus the failure window is node initialization rather than evidence that NumPy import itself failed.

## Bounded runtime diagnosis

Four isolated child diagnostics, containing no fixture integration, are retained in three JSON files under `run-01`:

- Captured NumPy imports with and without `CREATE_NO_WINDOW` both succeed (0.159644 and 0.165556 seconds).
- An import with the original hidden/inherited-handle setup succeeds (0.777720 seconds); its printed output was not visible in the tool response.
- `np.polynomial.legendre.leggauss(32)` prints its pre-call marker, then reproduces the same native exit code (7.247534 seconds), with no stderr or post-call marker.

These observations isolate a failure in the installed `leggauss` execution path. A specific DLL or BLAS root cause has not been proved. No package, driver or environment was installed or changed.

## Single repair authorized before attempt 2

The protocol permits one disclosed repair/re-execution for implementation failure. Replace only GL node construction with the ordinary Newton iteration for zeros of the Legendre polynomial, evaluating the polynomial/derivative by recurrence and using the standard GL weight formula. Retain orders 32 and 64, the identical segment breakpoints, integrands, fixtures, tolerances and decision gates. Bound iterations and check rule symmetry, positive weights and polynomial moments; these are implementation-validity checks, not a changed research gate. Record their diagnostics. Explicit child stdout/stderr files improve failure observability while retaining a hidden process and the 300-second supervisor cap.

The input retains its original generator identity. The repaired execution records the new script identity separately. Attempt 2 must use a fresh output directory and the same input bytes. No third full attempt, added ray, altered threshold or rescue construction is authorized by this task.
