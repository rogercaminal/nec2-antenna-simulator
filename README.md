# nec2-antenna-simulator

## Overview
This project provides a small Python package that wraps common NEC2 (Numerical Electromagnetics Code) setup steps and a Docker image that bundles PyNEC/necpp plus Jupyter for interactive antenna simulations. The goal is to make it easy to:

- Build and run NEC2-based models without installing a toolchain locally.
- Define geometry, excitations, loads, ground models, and radiation patterns using concise helper functions.
- Compute common antenna metrics like reflection coefficient, VSWR, and mismatch efficiency.

The package lives at `nec2_antenna_simulator/src/nec2_antenna_simulator` and is mounted into the container for editable development.

## Quick start with Docker

### Prerequisites
- Docker and Docker Compose installed.

### Build and run
From the repository root:

```sh
docker-compose up --build
```

This will:
- Build an image that includes Python, Jupyter, and the PyNEC/necpp toolchain.
- Start Jupyter Lab on `http://localhost:8888`.
- Mount your local `notebooks/` and `nec2_antenna_simulator/` directories into the container.

### Restart only
If the image is already built:

```sh
docker-compose up
```

### Container details
The compose setup mounts:
- `./notebooks` -> `/work/notebooks`
- `./nec2_antenna_simulator` -> `/work/nec2_antenna_simulator`

The container starts by running:

```sh
pip install -e /work/nec2_antenna_simulator
```

This ensures the package is importable even though the source directory is bind-mounted.

### Importing the package
In a notebook or a Python shell in the container:

```python
from nec2_antenna_simulator import getters, setters, metrics
```

## Package aim and design

The package provides small helpers around common NEC2 card operations. It does not try to hide NEC2; instead it:

- Keeps the NEC card arguments explicit and in the same order as PyNEC expects.
- Encourages readable, repeatable setup code.
- Provides antenna metrics computed from complex impedances.

## Card helper functions and parameters

All helper functions accept the `nec` context object (from PyNEC) and return the same context for simple chaining.

### Geometry and excitation
`set_geometry(nec, wires, excitations)`

- **wires**: list of wire tuples passed to `geometry.wire`.
  - Tuple layout matches PyNEC: `(segments, x0, y0, z0, x1, y1, z1, radius, segment_length_ratio, radius_taper_ratio)`
  - `segments` is the number of segments along the wire.
  - `(x0, y0, z0)` and `(x1, y1, z1)` are endpoints.
  - `radius` is the wire radius.
  - The ratio values control segment length distribution and tapering.

- **excitations**: list of tuples passed to `nec.ex_card`.
  - Tuple layout: `(I1, I2, I3, I4, F1, F2, F3, F4, F5, F6)`
  - `I1`: excitation type (0 = voltage source, 4 = current source)
  - `I2`: wire tag number
  - `I3`: segment number
  - `I4`: unused (leave 0)
  - `F1`: real part of excitation
  - `F2`: imaginary part of excitation
  - `F3`-`F6`: unused

### Loads
`set_loads(nec, loads)`

- **loads**: parameters passed to `nec.ld_card`.
  - Tuple layout: `(I1, I2, I3, I4, F1, F2, F3)`
  - `I1`: load type (resistive, reactive, etc.)
  - `I2`: wire tag number
  - `I3`: start segment
  - `I4`: end segment
  - `F1`-`F3`: load parameters (depend on `I1`)

### Ground
`set_ground(nec, ground)`

- **ground**: parameters passed to `nec.gn_card`.
  - Tuple layout: `(I1, I2, F1, F2, F3, F4, F5, F6)`
  - `I1`: ground type (-1 = free space, 0 = finite ground, 1 = perfect ground, 2 = finite ground Sommerfeld/Norton)
  - `I2`: number of radial wires (if using a ground screen)
  - `F1`: relative permittivity (eps_r)
  - `F2`: conductivity (S/m)
  - `F3`-`F6`: radial screen or second medium parameters

### Frequency sweep
`set_frequency(nec, frequency)`

- **frequency**: parameters passed to `nec.fr_card`.
  - Tuple layout: `(I1, I2, F1, F2)`
  - `I1`: sweep type (0 = linear stepping, 1 = logarithmic stepping)
  - `I2`: number of frequency points
  - `F1`: start frequency
  - `F2`: step size (or multiplier in log mode)

### Radiation pattern
`set_radiation_pattern(nec, rad_pattern)`

- **rad_pattern**: parameters passed to `nec.rp_card`.
  - Tuple layout: `(I1, I2, I3, I4, I5, F1, F2, F3, F4, F5, F6, F7)`
  - `I1`: calculation mode (0 = normal far field, 1-6 = special ground/surface wave modes)
  - `I2`: number of theta samples
  - `I3`: number of phi samples
  - `I4`: output format (0 recommended)
  - `I5`: normalization mode (0 = no normalization, 5 = normalize total gain to 0 dB max)
  - `F1`: gain type
  - `F2`: averaging
  - `F3`: starting theta (deg)
  - `F4`: starting phi (deg)
  - `F5`: delta theta (deg)
  - `F6`: delta phi (deg)
  - `F7`: radial distance R

### Execute the run
`run(nec)`

- Calls `nec.xq_card(0)` to execute the analysis.

## Metrics helpers

The `metrics` module provides convenience functions for complex impedance analysis:

- `reflection_coefficient(z, z0)` -> magnitude of reflection coefficient
- `vswr(z, z0)` -> voltage standing wave ratio
- `mismatch(z, z0)` -> mismatch efficiency

These functions accept scalars or numpy arrays.

## Notes
- The code assumes PyNEC/necpp is installed in the container image.
- If you change the package source, just restart the container and your edits are live because of the bind mount.
