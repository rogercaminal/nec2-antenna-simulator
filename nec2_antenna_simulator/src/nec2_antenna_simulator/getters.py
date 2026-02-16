"""Getter helpers"""

def get_impedance(nec, index):
  """Return the complex input impedance for a given NEC input index.

  Parameters
  ----------
  nec : object
      NEC context with ``get_input_parameters`` available.
  index : int
      Input index to query.

  Returns
  -------
  complex
      Complex impedance at the requested input.
  """
  return nec.get_input_parameters(index).get_impedance()
