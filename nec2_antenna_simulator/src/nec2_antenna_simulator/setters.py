"""Helper functions to set the cards"""


def set_geometry(nec, wires, excitations):
    """Define geometry and excitations on the NEC context.

    Parameters
    ----------
    nec : object
        NEC context with ``get_geometry`` and card methods.
    wires : list[tuple]
        Wire tuples with segment count, endpoints, radius, and taper settings
        suitable for ``geometry.wire``.
    excitations : list[tuple]
        Excitation cards passed to ``nec.ex_card``. The expected tuple layout
        is ``(I1, I2, I3, I4, F1, F2, F3, F4, F5, F6)``.

    Returns
    -------
    object
        The same NEC context, for chaining.
    """
    geo = nec.get_geometry()

    for i, wire in enumerate(wires):
        geo.wire(i+1, *wire)
    nec.geometry_complete(1)

    for excitation in excitations:
        nec.ex_card(*excitation)

    return nec


def set_loads(nec, loads):
    """Apply load cards to the NEC context.

    Parameters
    ----------
    nec : object
        NEC context with ``ld_card``.
    loads : tuple or list
        Load parameters for ``nec.ld_card`` with layout
        ``(I1, I2, I3, I4, F1, F2, F3)``.

    Returns
    -------
    object
        The same NEC context, for chaining.
    """
    if len(loads) > 0:
        nec.ld_card(*loads)
    return nec


def set_ground(nec, ground):
    """Configure the ground model for the NEC context.

    Parameters
    ----------
    nec : object
        NEC context with ``gn_card``.
    ground : tuple
        Ground parameters for ``nec.gn_card`` with layout
        ``(I1, I2, F1, F2, F3, F4, F5, F6)``.

    Returns
    -------
    object
        The same NEC context, for chaining.
    """
    nec.gn_card(*ground)
    return nec


def set_frequency(nec, frequency):
    """Set the frequency sweep.

    Parameters
    ----------
    nec : object
        NEC context with ``fr_card``.
    frequency : tuple
        Frequency parameters for ``nec.fr_card`` with layout
        ``(I1, I2, F1, F2)``.

    Returns
    -------
    object
        The same NEC context, for chaining.
    """
    nec.fr_card(*frequency)
    return nec


def set_radiation_pattern(nec, rad_pattern):
    """Define radiation pattern sampling and normalization.

    Parameters
    ----------
    nec : object
        NEC context with ``rp_card``.
    rad_pattern : tuple
        Radiation pattern parameters for ``nec.rp_card`` with layout
        ``(I1, I2, I3, I4, I5, F1, F2, F3, F4, F5, F6, F7)``.

    Returns
    -------
    object
        The same NEC context, for chaining.
    """
    nec.rp_card(*rad_pattern)
    return nec


def run(nec):
    """Execute the analysis run.

    Parameters
    ----------
    nec : object
        NEC context with ``xq_card``.

    Returns
    -------
    object
        The same NEC context, for chaining.
    """
    nec.xq_card(0)
    return nec
