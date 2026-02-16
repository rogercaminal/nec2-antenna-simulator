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
      Magnitude of the reflection coefficient.
  """
  return np.abs((z - z0) / (z + z0))

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
    Gamma = reflection_coefficient(z, z0)
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
