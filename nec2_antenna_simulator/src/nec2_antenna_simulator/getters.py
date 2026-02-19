"""Getter helpers"""

from typing import Any, Dict, Optional, Tuple

import numpy as np

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


def get_structure_currents(nec, freq_index: int = 0) -> Dict[str, Any]:
  """Extract structure current data from the NEC context when available.

  Parameters
  ----------
  nec : object
      NEC context with ``get_structure_currents`` available.
  freq_index : int, optional
      Frequency index for sweep results, by default 0.

  Returns
  -------
  dict
      Dictionary with best-effort keys:
      - ``currents``: complex ndarray of per-segment currents.
      - ``tags``: int ndarray of wire tags.
      - ``segments``: int ndarray of segment numbers.
      - ``count``: number of entries if exposed by the binding.
      - ``raw``: the raw object returned by ``get_structure_currents``.
  """
  if not hasattr(nec, "get_structure_currents"):
    raise AttributeError("nec does not expose get_structure_currents")

  obj = nec.get_structure_currents(freq_index)
  data: Dict[str, Any] = {"raw": obj}

  def _first(getters):
    for name in getters:
      if hasattr(obj, name):
        return getattr(obj, name)
    return None

  n: Optional[int] = None
  n_fn = _first(["get_n", "get_count", "get_num", "size"])
  if n_fn is not None:
    try:
      n = int(n_fn() if callable(n_fn) else n_fn)
    except Exception:
      n = None
  if n is None:
    try:
      n = len(obj)
    except Exception:
      n = None
  if n is not None:
    data["count"] = n

  # Try array-style access first.
  arr_fn = _first(["get_currents", "get_current_array", "as_array"])
  if arr_fn is not None:
    try:
      currents = np.array(arr_fn(), dtype=np.complex128).ravel()
      if currents.size:
        data["currents"] = currents
    except Exception:
      pass

  # Try indexed access if needed.
  if "currents" not in data and n:
    cur_fn = _first(["get_current", "current"])
    cur_re_fn = _first(["get_current_real", "get_real", "real"])
    cur_im_fn = _first(["get_current_imag", "get_imag", "imag"])

    def _current_from_item(item):
      item_cur = None
      if hasattr(item, "get_current"):
        item_cur = item.get_current
      elif hasattr(item, "current"):
        item_cur = item.current
      if item_cur is not None:
        return complex(item_cur())
      if hasattr(item, "get_current_real") and hasattr(item, "get_current_imag"):
        return complex(float(item.get_current_real()), float(item.get_current_imag()))
      if hasattr(item, "get_real") and hasattr(item, "get_imag"):
        return complex(float(item.get_real()), float(item.get_imag()))
      if hasattr(item, "real") and hasattr(item, "imag"):
        return complex(float(item.real()), float(item.imag()))
      return None

    if cur_fn or (cur_re_fn and cur_im_fn):
      currents = np.zeros(n, dtype=np.complex128)
      for i in range(n):
        if cur_fn:
          try:
            currents[i] = complex(cur_fn(i))
            continue
          except TypeError:
            pass
        if cur_re_fn and cur_im_fn:
          try:
            currents[i] = complex(float(cur_re_fn(i)), float(cur_im_fn(i)))
            continue
          except TypeError:
            pass

        if hasattr(obj, "__getitem__"):
          try:
            item = obj[i]
            value = _current_from_item(item)
            if value is not None:
              currents[i] = value
              continue
          except Exception:
            pass
      data["currents"] = currents

  # Tag/segment metadata if exposed.
  if n:
    tag_fn = _first(["get_tag", "get_tag_number", "get_tag_no", "get_tagno", "tag"])
    seg_fn = _first(["get_seg", "get_segment", "get_segment_number", "get_seg_number", "segment"])
    if tag_fn is not None:
      tags = np.zeros(n, dtype=int)
      for i in range(n):
        tags[i] = int(tag_fn(i))
      data["tags"] = tags
    if seg_fn is not None:
      segments = np.zeros(n, dtype=int)
      for i in range(n):
        segments[i] = int(seg_fn(i))
      data["segments"] = segments

  return data


def get_radiation_pattern(nec, freq_index: int = 0) -> Dict[str, Any]:
    rp = nec.get_radiation_pattern(freq_index)
    gains = rp.get_gain()
    thetas = rp.get_theta_angles()
    phis = rp.get_phi_angles()
    data = {"gain_db": gains, "theta": thetas, "phi": phis}
    return data


