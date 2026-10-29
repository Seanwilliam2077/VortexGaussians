# T49 — two ordinary closures, distinct field contracts

T48's diffusion limitation is a state-coupling limitation, not evidence that affine viscous vorticity transport needs a new solver. [Separating metric and envelope](METRIC_ENVELOPE.md) repairs it exactly for the prescribed affine equation. A [curl-Gaussian carrier](CURL_CARRIER.md) also closes exactly for that operation through ordinary covector evolution. The [source screen](SOURCES.md) directly matches the general magnetization formulation, so broad claims of inventing projected impulse velocity or covector diffusion are unavailable.

## What the two calculations establish

Both calculations use the same prescribed incompressible affine velocity A(t)x+b(t), the same constant viscosity nu, and free space. Neither imposes that this prescribed velocity is reconstructed from the represented vorticity. This common operation allows a mathematical contract comparison, not an equal-field or equal-particle-count performance comparison.

| Property | Separate metric/envelope carrier | Curl-Gaussian carrier |
|---|---|---|
| Field | Q_M c times a Gaussian in Fourier space | curl(a G_C) |
| Stored record | M,C,c,mu: 18 scalars; one positive M-scale redundancy | C,a,mu: 12 scalars |
| Affine coefficient update | cdot=A c | adot=-A^T a |
| Envelope update | Cdot=A C+C A^T+2 nu I | Same envelope ODE |
| Other state update | Mdot=A M+M A^T | None needed for this carrier |
| Joint affine/heat closure | Exact for the prescribed equation | Exact for the prescribed equation |
| Vorticity localization | Algebraic tail; nonzero single carrier not absolutely L1 | Gaussian derivative; total vorticity zero |
| Coefficient interpretation | c is a raw-source parameter | a equals the normalized unit-density impulse integral |
| Available velocity representation | One-parameter ordinary term plus a two-parameter correction; no lower-dimensional impossibility claim | Ordinary one-dimensional integral plus a local Gaussian term |
| Center self-velocity | Zero by odd velocity parity | Nonzero for nonzero a; isotropic value (2/3)G_C(0)a |

The lower parameter or integral count in the curl-Gaussian column does not prove greater efficiency at matching a specified flow. The families represent different fields and have different low-frequency, parity and tail behavior. A meaningful comparison would first approximate the same initial vorticity/velocity to a stated tolerance and charge fitting, state, evolution and complete reconstruction. No such representation-error or timing evidence exists here.

Exact parameter ODEs also do not eliminate their integration cost for arbitrary time-dependent A. Reusing only a center velocity and local gradient of a nonlinear self-induced field does not inherit this exact closure. Neither separate local maps nor an unchanged Gaussian covariance constitute a demonstrated Navier–Stokes method.

## Consequence for implementation

The current demo's raw-vorticity source and these proposed carriers are not interchangeable records. In particular, covector a stretches with -A^T rather than A, and the curl carrier's center self-velocity cannot be discarded using an old zero-self convention. This is a prospective implementation contract, not a reported bug in code that does not implement the new family.

The complete ordinary reconstruction formulas are available to every comparator. A candidate cannot earn an advantage by comparing against a mandatory global grid solve, dropping another method's self term, or using the first term of a different model as an inaccurate baseline. Gaussian-localized vorticity still induces a long-range velocity; it does not authorize Gaussian-distance culling of velocity interactions.

## Finite decision

**Retain both derivations as ordinary reference contracts. Do not select either as a new core method or start a solver implementation on closure alone.** This task removes a real ambiguity: the missing diffusion state can be supplied ordinarily, and another established formulation offers a different localized carrier. The remaining research problem is a useful, accurate and efficient treatment of self-consistent/non-affine motion or another clearly specified operation, beyond these ordinary identities.

The next information gap is a specifically identified graphics paper, _Impulse Fluid Simulation_, whose author-hosted PDF exceeded the web tool's size limit in this round. Its full solver and comparison contract may directly constrain this route. [NEXT_EVIDENCE.md](NEXT_EVIDENCE.md) prepares one bounded read of that same document through a size-limited local acquisition; no new search family, numerical run, method or benchmark is authorized by the preparation. The ordinary magnetization formulation is already matched, so this read must seek concrete algorithm/evaluation distinctions rather than rediscovering that formulation.

The full research goal remains active and unachieved. There is no established distinct method, practical task result, measured strong-baseline advantage or multi-scene validation. All prior results and gates remain sealed; art inactivity, main and the deleted automation remain unchanged.
