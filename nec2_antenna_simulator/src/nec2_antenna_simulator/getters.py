"""Getter helpers"""

def get_impedance(nec):
  """Return the complex input impedance from the first NEC port.

  Parameters
  ----------
  nec : object
      NEC context with ``get_input_parameters`` available.

  Returns
  -------
  complex
      Complex impedance at the first input.
  """
  index = 0
  return nec.get_input_parameters(index).get_impedance()
