"""Antenna metrics"""
import numpy as np


def reflection_coefficient(z, z0):
  """Compute the magnitude of the reflection coefficient.

  Parameters
  ----------
  z : complex or ndarray
      Load impedance.
  z0 : complex or ndarray
      Reference impedance.

  Returns
  -------
  float or ndarray
      Reflection coefficient.
  """
  return (z - z0) / (z + z0)

def vswr(z, z0):
    """Compute voltage standing wave ratio (VSWR).

    Parameters
    ----------
    z : complex or ndarray
        Load impedance.
    z0 : complex or ndarray
        Reference impedance.

    Returns
    -------
    float or ndarray
        VSWR value.
    """
    Gamma = np.abs(reflection_coefficient(z, z0))
    return (1 + Gamma) / (1 - Gamma)

def mismatch(z, z0):
    """Compute mismatch efficiency.

    Parameters
    ----------
    z : complex or ndarray
        Load impedance.
    z0 : complex or ndarray
        Reference impedance.

    Returns
    -------
    float or ndarray
        Mismatch efficiency.
    """
    Gamma = reflection_coefficient(z, z0)
    return 1 - Gamma**2

def transmission_line(z0, zl, l, f_mhz, vf=1.0):
    """
    Compute the input impedance of a lossless transmission line.

    This function evaluates the input impedance Zin of a lossless
    transmission line of length `l`, characteristic impedance `z0`,
    and load impedance `zl`, at frequency `f_mhz`.

    The calculation assumes:
        - Lossless line (alpha = 0)
        - Real characteristic impedance (z0)
        - Phase velocity vp = c * vf

    Parameters
    ----------
    z0 : float or complex
        Characteristic impedance of the transmission line (ohms).
        Typically real for a lossless line (e.g., 50 ohms).
    zl : complex or ndarray
        Load impedance at the end of the line (ohms).
    l : float
        Physical length of the transmission line (meters).
    f_mhz : float or ndarray
        Frequency in MHz.
    vf : float, optional
        Velocity factor of the transmission line (dimensionless).
        Default is 1.0 (free-space propagation).

    Returns
    -------
    complex or ndarray
        Input impedance at the beginning of the transmission line (ohms).

    Notes
    -----
    The input impedance is computed using:

        Zin = Z0 * (ZL + j Z0 tan(beta l)) /
                    (Z0 + j ZL tan(beta l))

    where:
        beta = 2*pi*f / vp
        vp = c * vf

    For a lossless line, the magnitude of the reflection coefficient
    is preserved along the line:

        |Γ_in| = |Γ_L|
    """
    f = f_mhz * 1e6
    vp = 3e8 * vf
    beta = 2 * np.pi * f / vp
    zin = z0 * (zl + 1j * z0 * np.tan(beta * l)) / (z0 + 1j * zl * np.tan(beta * l))
    return zin
