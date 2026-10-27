"""Shared differentiable, periodic MAC passive-smoke model for R20.

Arrays use x,y,z spatial order.  Density lives at cell centers; component j
lives on the lower j-face of that cell. Accepted frames are numbered 1..steps;
force() uses zero-based update indices 0..steps-1. No asset loading, runtime
configuration, checkpointing, fitting, clipping, or implicit device selection
is performed here. All rollout tensors retain their autograd graph.

This is a deliberately changed model: no combustion, diffusion, buoyancy,
obstacles, density sources, or claimed fidelity to the earlier FieryGS model.
Semi-Lagrangian interpolation preserves nonnegativity, but not density mass.
"""
from __future__ import annotations

import math
import torch


class SmokeModel:
    """Unit periodic cube, consistent MAC projection, synchronous old-v transport.

    Controls: (4,3,8,8,8), four temporal knots, each an 8^3 MAC force field.
    Main optical contract: 20-degree orthographic view, 32^2 optical pixels,
    64 midpoint samples, nonnegative absorption, then bilinear alpha upscale.
    The optical renderer uses zero extension outside the cube, not periodic
    wrapping. 64^2 output therefore does not contain 64^2 independent rays.
    """

    FACE_OFFSETS = ((0.0, 0.5, 0.5), (0.5, 0.0, 0.5), (0.5, 0.5, 0.0))
    CENTER_OFFSET = (0.5, 0.5, 0.5)

    def __init__(self, n=32, steps=40, dt=0.025, image_size=64,
                 device="cpu", dtype=torch.float64, kappa=1.0,
                 frame_start=16, render_size=32, render_samples=64):
        if n < 2 or steps < 2 or not 1 <= frame_start <= steps:
            raise ValueError("n>=2, steps>=2 and 1<=frame_start<=steps required")
        if image_size < 1 or render_size < 1 or render_samples < 1:
            raise ValueError("positive image/sample dimensions required")
        if not math.isfinite(dt) or dt <= 0 or not math.isfinite(kappa) or kappa < 0:
            raise ValueError("positive finite dt and nonnegative finite kappa required")
        if dtype not in (torch.float32, torch.float64):
            raise ValueError("only float32/float64 supported")
        self.n, self.steps, self.dt = int(n), int(steps), float(dt)
        self.h, self.image_size = 1.0 / self.n, int(image_size)
        self.device, self.dtype = torch.device(device), dtype
        self.kappa, self.frame_start = float(kappa), int(frame_start)
        self.render_size, self.render_samples = int(render_size), int(render_samples)
        axis = torch.arange(self.n, device=self.device, dtype=self.dtype)
        ijk = torch.stack(torch.meshgrid(axis, axis, axis, indexing="ij"), dim=-1)
        self.centers = (ijk + 0.5) * self.h
        self.faces = tuple((ijk + self._constant(o)) * self.h for o in self.FACE_OFFSETS)

        # D uses forward differences, G backward differences. DG has only the
        # constant null mode; the even-grid Nyquist modes are NOT discarded.
        freq = torch.fft.fftfreq(self.n, d=1.0 / self.n, device=self.device, dtype=self.dtype)
        one = -4.0 * torch.sin(math.pi * freq / self.n).square() / self.h**2
        lap = one[:, None, None] + one[None, :, None] + one[None, None, :]
        nonzero = lap != 0
        safe_lap = torch.where(nonzero, lap, torch.ones_like(lap))
        self.inverse_laplacian = torch.where(nonzero, 1.0 / safe_lap, torch.zeros_like(lap))

        # Exactly [0,13,26,39] for 40 updates; hats partition unity including
        # both end updates. These are update indices, not accepted frame IDs.
        hats = [[max(0.0, 1.0 - abs(3.0 * s / (self.steps - 1) - k))
                 for k in range(4)] for s in range(self.steps)]
        self.time_weights = self._constant(hats)
        self._prepare_camera()

    def _constant(self, value):
        return torch.as_tensor(value, dtype=self.dtype, device=self.device)

    def divergence(self, velocity):
        """MAC faces -> cell centers: Dv = sum_j (v_j[i+1]-v_j[i])/h."""
        return sum((torch.roll(velocity[j], -1, dims=j) - velocity[j]) / self.h
                   for j in range(3))

    def gradient(self, pressure):
        """Cell centers -> MAC faces, the negative adjoint of divergence."""
        return torch.stack([(pressure - torch.roll(pressure, 1, dims=j)) / self.h
                            for j in range(3)])

    def project(self, velocity):
        """Orthogonal Euclidean MAC projection; full-domain FFT and zero-mean p."""
        divergence = self.divergence(velocity)
        pressure = torch.fft.ifftn(torch.fft.fftn(divergence) * self.inverse_laplacian).real
        return velocity - self.gradient(pressure)

    def sample(self, field, points, offset=CENTER_OFFSET, periodic=True):
        """Trilinearly sample at physical unit-cube points (...,3).

        field has arbitrary leading channels and three trailing spatial axes.
        offset is its position within its lattice cell, in lattice units.
        Custom gathers support reverse AD, torch.func.jvp and mixed second AD
        piecewise away from interpolation-cell boundaries. At a boundary AD
        follows the floor-selected cell; no classical smoothness is asserted.
        Nonperiodic sampling has zero ghost nodes and is zero outside [0,1]^3.
        """
        shape = field.shape[-3:]
        size = self._constant(shape)
        q = points * size - self._constant(offset)
        lower_float = torch.floor(q)
        lower = lower_float.to(torch.int64)
        frac = q - lower_float
        flat = field.reshape(-1, math.prod(shape))
        result = None
        inside = ((points >= 0) & (points <= 1)).all(dim=-1)
        for a in range(2):
            for b in range(2):
                for c in range(2):
                    ix, iy, iz = lower[..., 0] + a, lower[..., 1] + b, lower[..., 2] + c
                    weight = ((frac[..., 0] if a else 1 - frac[..., 0]) *
                              (frac[..., 1] if b else 1 - frac[..., 1]) *
                              (frac[..., 2] if c else 1 - frac[..., 2]))
                    if periodic:
                        ix, iy, iz = ix.remainder(shape[0]), iy.remainder(shape[1]), iz.remainder(shape[2])
                    else:
                        valid = (inside & (ix >= 0) & (ix < shape[0]) &
                                 (iy >= 0) & (iy < shape[1]) & (iz >= 0) & (iz < shape[2]))
                        weight = weight * valid.to(weight.dtype)
                        ix, iy, iz = ix.clamp(0, shape[0]-1), iy.clamp(0, shape[1]-1), iz.clamp(0, shape[2]-1)
                    address = ((ix * shape[1] + iy) * shape[2] + iz).reshape(-1)
                    term = flat.index_select(1, address) * weight.reshape(1, -1)
                    result = term if result is None else result + term
        return result.reshape(*field.shape[:-3], *points.shape[:-1])

    def velocity_at(self, velocity, points):
        return torch.stack([self.sample(velocity[j], points, self.FACE_OFFSETS[j])
                            for j in range(3)], dim=-1)

    def _velocity_on_lattice(self, velocity, destination_offset):
        # Exact trilinear interpolation at these fixed staggered lattice sites.
        # Half-cell offsets reduce to separable averages, avoiding unnecessary
        # differentiable coordinate/gather graphs without changing the stencil.
        components = []
        for j in range(3):
            value = velocity[j]
            for axis in range(3):
                delta = destination_offset[axis] - self.FACE_OFFSETS[j][axis]
                if delta != 0:
                    value = 0.5 * (value + torch.roll(value, -1 if delta > 0 else 1, dims=axis))
            components.append(value)
        return torch.stack(components, dim=-1)

    def _expand_controls(self, controls):
        if tuple(controls.shape) != (4, 3, 8, 8, 8):
            raise ValueError("controls must have shape (4,3,8,8,8)")
        # The four spatially extended knots are computed once per rollout.
        return torch.stack([self.sample(controls[:, j], self.faces[j], self.FACE_OFFSETS[j])
                            for j in range(3)], dim=1)

    def force(self, controls, step):
        """Physical MAC body acceleration for zero-based update index step."""
        if not 0 <= step < self.steps:
            raise ValueError("force step outside 0..steps-1")
        return (self._expand_controls(controls) * self.time_weights[step, :, None, None, None, None]).sum(dim=0)

    def step(self, velocity, density, force):
        """One update: old-v advects v and rho; add dt*f to v; fully project v.

        Density uses old velocity, so a force applied at this update affects
        transport beginning at the next update. No artificial density clamp.
        """
        advected_components = []
        for j in range(3):
            departure = self.faces[j] - self.dt * self._velocity_on_lattice(velocity, self.FACE_OFFSETS[j])
            advected_components.append(self.sample(velocity[j], departure, self.FACE_OFFSETS[j]))
        departure = self.centers - self.dt * self._velocity_on_lattice(velocity, self.CENTER_OFFSET)
        new_density = self.sample(density, departure)
        new_velocity = self.project(torch.stack(advected_components) + self.dt * force)
        return new_velocity, new_density

    def _prepare_camera(self):
        angle = math.radians(20.0)
        co, si = math.cos(angle), math.sin(angle)
        span = co + si
        self.camera = {
            "kind": "orthographic", "rotationYDegrees": 20.0,
            "center": [0.5, 0.5, 0.5], "right": [co, 0.0, -si],
            "up": [0.0, 1.0, 0.0], "depthDirection": [si, 0.0, co],
            "width": span, "height": 1.0, "depthSpan": span,
            "opticalPixels": [self.render_size, self.render_size],
            "depthSamples": self.render_samples, "outputPixels": [self.image_size, self.image_size],
            "pixelOrigin": "lower-left (row increases along camera up)",
            "interpolation": "cell-centered trilinear, zero ghost nodes and zero outside unit cube",
            "upscale": "bilinear alpha, clamped image edges, align_corners=False",
        }
        u = (torch.arange(self.render_size, dtype=self.dtype, device=self.device) + 0.5) / self.render_size - 0.5
        z = (torch.arange(self.render_samples, dtype=self.dtype, device=self.device) + 0.5) / self.render_samples - 0.5
        yy, xx, zz = torch.meshgrid(u, u, z, indexing="ij")
        self.optical_points = (0.5 + xx[..., None] * span * self._constant([co, 0, -si]) +
                               yy[..., None] * self._constant([0, 1, 0]) +
                               zz[..., None] * span * self._constant([si, 0, co]))
        self.optical_dl = span / self.render_samples

    def _upsample_image(self, image):
        # Positive image bilinear interpolation. No periodic wrapping in image.
        height, width = image.shape
        t = (torch.arange(self.image_size, dtype=self.dtype, device=self.device) + 0.5) / self.image_size
        y, x = torch.meshgrid(t * height - 0.5, t * width - 0.5, indexing="ij")
        yf, xf = torch.floor(y), torch.floor(x)
        iy, ix = yf.to(torch.int64), xf.to(torch.int64)
        fy, fx = y-yf, x-xf
        result = None
        for a in range(2):
            for b in range(2):
                address = ((iy+a).clamp(0, height-1) * width + (ix+b).clamp(0, width-1)).reshape(-1)
                weight = (fy if a else 1-fy) * (fx if b else 1-fx)
                term = image.reshape(-1).index_select(0, address).reshape(self.image_size, self.image_size) * weight
                result = term if result is None else result + term
        return result

    def render(self, density):
        """Fixed oblique positive alpha; no RGB, tone mapping, or illumination."""
        sampled = self.sample(density, self.optical_points, periodic=False)
        tau = self.kappa * self.optical_dl * sampled.sum(dim=-1)
        alpha = -torch.expm1(-tau)
        return self._upsample_image(alpha)

    def render_axis(self, density):
        """Diagnostic z-view only, H=y/W=x. Not the primary camera."""
        alpha = -torch.expm1(-self.kappa * self.h * density.sum(dim=2))
        return self._upsample_image(alpha.transpose(0, 1))

    def rollout(self, controls, v0, rho0, return_states=False):
        if tuple(v0.shape) != (3, self.n, self.n, self.n) or tuple(rho0.shape) != (self.n,)*3:
            raise ValueError("v0/rho0 do not match the model grid")
        expanded = self._expand_controls(controls)
        velocity, density = v0, rho0
        frames = []
        velocities, densities = ([v0], [rho0]) if return_states else (None, None)
        for index in range(self.steps):
            force = (expanded * self.time_weights[index, :, None, None, None, None]).sum(dim=0)
            velocity, density = self.step(velocity, density, force)
            if index + 1 >= self.frame_start:
                frames.append(self.render(density))
            if return_states:
                velocities.append(velocity)
                densities.append(density)
        result = {"frames": torch.stack(frames), "velocity": velocity, "density": density}
        if return_states:
            result["states"] = {"velocity": torch.stack(velocities), "density": torch.stack(densities)}
        return result
