"""Visualization utils"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Tuple, Union, Any, List

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

from .getters import get_structure_currents, get_radiation_pattern

try:
    import plotly.graph_objects as go
except ImportError as e:
    raise ImportError(
        "plotly is required for 3D interactive plotting. Install with: pip install plotly"
    ) from e


WireTuple = Tuple[
    int,      # segments
    float, float, float,  # x0,y0,z0
    float, float, float,  # x1,y1,z1
    float,    # radius
    float, float  # rdel, rrad
]

ExcitationTuple = Tuple[int, int, int, int, float, float, float, float, float, float]
LoadTuple = Tuple[int, int, int, int, float, float, float]


@dataclass
class SegmentMap:
    """Mapping between (wire_idx, seg_idx) and global segment index."""
    wire_idx: int
    seg_idx: int
    global_idx: int
    center_xyz: np.ndarray


def _segment_centers_for_wire(p0: np.ndarray, p1: np.ndarray, nseg: int) -> np.ndarray:
    """
    Return segment center points for a straight wire subdivided into nseg segments.
    Centers are at (k+0.5)/nseg along the wire.
    """
    t = (np.arange(nseg, dtype=float) + 0.5) / float(nseg)
    return p0[None, :] * (1.0 - t[:, None]) + p1[None, :] * t[:, None]


def _build_segment_map(wires: Sequence[WireTuple]) -> List[SegmentMap]:
    segmap: List[SegmentMap] = []
    g = 0
    for wi, w in enumerate(wires):
        nseg, x0, y0, z0, x1, y1, z1, *_ = w
        p0 = np.array([x0, y0, z0], dtype=float)
        p1 = np.array([x1, y1, z1], dtype=float)
        centers = _segment_centers_for_wire(p0, p1, int(nseg))
        for si in range(int(nseg)):
            segmap.append(SegmentMap(wire_idx=wi, seg_idx=si + 1, global_idx=g, center_xyz=centers[si]))
            g += 1
    return segmap


def _find_segment_center(segmap: Sequence[SegmentMap], wire_tag: int, seg_nr: int) -> Optional[np.ndarray]:
    """
    In your repo, wire tags are assigned as i+1 when building geometry. :contentReference[oaicite:1]{index=1}
    So wire_tag maps to wire_idx = wire_tag-1.
    """
    target_wi = wire_tag - 1
    for s in segmap:
        if s.wire_idx == target_wi and s.seg_idx == seg_nr:
            return s.center_xyz
    return None



def _model_from_nec_meta(nec: Any) -> Tuple[Optional[Sequence[WireTuple]], Optional[Sequence[ExcitationTuple]], Optional[Sequence[LoadTuple]]]:
    meta = getattr(nec, "_nec2_meta", None)
    if not isinstance(meta, dict):
        return None, None, None
    return meta.get("wires"), meta.get("excitations"), meta.get("loads")


def plot_nec_model_3d(
    wires: Optional[Sequence[WireTuple]] = None,
    excitations: Optional[Sequence[ExcitationTuple]] = None,
    loads: Union[Sequence[LoadTuple], LoadTuple, None] = None,
    nec: Optional[Any] = None,
    save_html: Optional[str] = None,
    title: str = "NEC model (geometry + sources/loads + currents)",
) -> "go.Figure":
    """
    Interactive 3D visualization:
      - Wires as lines
      - Excitations (EX) as markers
      - Loads (LD) as markers/ranges
      - Segment currents as colored markers (if nec provided and currents accessible)

    Args:
        wires: list of wire tuples matching your repo's set_geometry format:
               (segments, x0,y0,z0, x1,y1,z1, radius, rdel, rrad). :contentReference[oaicite:2]{index=2}
        excitations: list of EX tuples:
               (I1,I2,I3,I4,F1,F2,F3,F4,F5,F6). :contentReference[oaicite:3]{index=3}
        loads: either:
               - None
               - a single LD tuple (I1,I2,I3,I4,F1,F2,F3)
               - or a list of such tuples
               (your current set_loads applies only one tuple; this supports both). :contentReference[oaicite:4]{index=4}
        nec: PyNEC context; if provided, missing wires/excitations/loads can be read
            from ``nec._nec2_meta`` (set by the setter helpers). If show_currents=True,
            currents will be fetched when available.
        freq_index: frequency index for sweeps (0 for single-frequency runs).
        save_html: if set, writes an interactive HTML file at this path.
        title: plot title.

    Returns:
        plotly.graph_objects.Figure
    """
    fig = go.Figure()

    if wires is None and nec is not None:
        wires, meta_ex, meta_ld = _model_from_nec_meta(nec)
        if excitations is None:
            excitations = meta_ex
        if loads is None:
            loads = meta_ld

    if wires is None:
        raise ValueError("wires must be provided, or nec must contain _nec2_meta['wires']")

    if excitations is None:
        excitations = ()

    # Build segment map (lets us place markers at segment centers)
    segmap = _build_segment_map(wires)

    # --- Plot wires ---
    for wi, w in enumerate(wires):
        nseg, x0, y0, z0, x1, y1, z1, radius, rdel, rrad = w
        fig.add_trace(
            go.Scatter3d(
                x=[x0, x1],
                y=[y0, y1],
                z=[z0, z1],
                mode="lines",
                name=f"wire tag {wi+1}",
                hovertemplate=(
                    f"wire tag: {wi+1}<br>"
                    f"segments: {int(nseg)}<br>"
                    f"radius: {radius} m<br>"
                    f"rdel: {rdel}, rrad: {rrad}<br>"
                    f"p0: ({x0:.4g},{y0:.4g},{z0:.4g})<br>"
                    f"p1: ({x1:.4g},{y1:.4g},{z1:.4g})<br>"
                    "<extra></extra>"
                ),
            )
        )

    # --- Plot excitations (EX) ---
    for ex in excitations or []:
        I1, I2, I3, I4, F1, F2, *_ = ex
        # Most common: voltage source (I1=0) or current source (I1=4)
        c = _find_segment_center(segmap, wire_tag=int(I2), seg_nr=int(I3)) if int(I2) != 0 else None
        if c is None:
            continue
        mag = float(np.hypot(F1, F2))
        phase = float(np.degrees(np.arctan2(F2, F1)))
        fig.add_trace(
            go.Scatter3d(
                x=[c[0]], y=[c[1]], z=[c[2]],
                mode="markers",
                name=f"EX (tag {I2}, seg {I3})",
                marker=dict(size=6, symbol="diamond"),
                hovertemplate=(
                    f"EX type I1: {I1}<br>"
                    f"wire tag: {I2}, segment: {I3}<br>"
                    f"phasor: {F1}+j{F2}<br>"
                    f"|exc|: {mag:.4g}, ∠: {phase:.2f}°<br>"
                    "<extra></extra>"
                ),
            )
        )

    # --- Plot loads (LD) ---
    ld_list: List[LoadTuple] = []
    if loads is None:
        ld_list = []
    elif isinstance(loads, tuple) and len(loads) == 7:
        ld_list = [loads]  # single
    else:
        ld_list = list(loads)  # type: ignore[arg-type]

    for ld in ld_list:
        I1, I2, I3, I4, F1, F2, F3 = ld
        tag = int(I2)
        s0 = int(I3)
        s1 = int(I4)
        if tag <= 0:
            continue

        # If (0,0) means whole wire in some conventions; here we only mark explicit ranges.
        if s0 <= 0 or s1 <= 0:
            continue

        # Mark each loaded segment center
        centers = []
        for s in range(min(s0, s1), max(s0, s1) + 1):
            c = _find_segment_center(segmap, wire_tag=tag, seg_nr=s)
            if c is not None:
                centers.append(c)
        if not centers:
            continue
        centers = np.vstack(centers)

        fig.add_trace(
            go.Scatter3d(
                x=centers[:, 0], y=centers[:, 1], z=centers[:, 2],
                mode="markers",
                name=f"LD (tag {tag}, {s0}-{s1})",
                marker=dict(size=4, symbol="square"),
                hovertemplate=(
                    f"LD type I1: {I1}<br>"
                    f"wire tag: {tag}, segments: {s0}..{s1}<br>"
                    f"F1,F2,F3: {F1}, {F2}, {F3}<br>"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="Z (m)",
            aspectmode="data",
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(itemsizing="constant"),
    )

    if save_html:
        fig.write_html(save_html, include_plotlyjs="cdn")
    return fig


def plot_radiation_patterns(
    nec,
    freq_indices=None,
    *,
    rmin=-15,
    rmax_pad=1.1,
    figsize_per_row=(10, 5.8),
):
    """
    Plot NEC radiation pattern cuts in polar coordinates.

    - Left column: θ cut at selected φ index (slider)
    - Right column: φ cut at selected θ index (slider)

    Parameters
    ----------
    nec : object
        Whatever your get_radiation_pattern expects.
    freq_indices : None | int | list[int]
        None => plot all frequencies (tries to detect count; see note below).
        int => single frequency.
        list[int] => multiple frequencies.
    rmin : float
        Lower radial limit (e.g., -15 dB).
    rmax_pad : float
        Multiply global max by this for upper radial limit.
    figsize_per_row : tuple(float, float)
        Base figsize per row when plotting multiple frequencies.
    """

    # --- resolve freq_indices ---
    if isinstance(freq_indices, (int, np.integer)):
        freq_indices = [int(freq_indices)]
    elif freq_indices is None:
        n_freq = nec._nec2_meta["frequency"][1]
        freq_indices = [i for i in range(n_freq)]
    else:
        freq_indices = [int(i) for i in freq_indices]

    # Get actual value of frequencies
    freq0 = nec._nec2_meta["frequency"][2]
    delta_freq = nec._nec2_meta["frequency"][3]
    freqs = []
    for i in freq_indices:
        freqs.append(freq0 + i * delta_freq)

    # --- load patterns for each frequency ---
    patterns = []
    global_max = -np.inf

    for fi, f in zip(freq_indices, freqs):
        rp = get_radiation_pattern(nec=nec, freq_index=fi)
        gains = np.asarray(rp["gain_db"])
        thetas = np.asarray(rp["theta"])
        phis = np.asarray(rp["phi"])

        patterns.append({"f": f, "fi": fi, "gains": gains, "thetas": thetas, "phis": phis})
        global_max = max(global_max, float(np.nanmax(gains)))

    rmax = float(global_max * rmax_pad)

    nrows = len(patterns)
    fig_w, fig_h = figsize_per_row
    fig, ax = plt.subplots(
        nrows, 2,
        figsize=(fig_w, fig_h * nrows),
        subplot_kw=dict(polar=True),
        squeeze=False
    )

    # --- initial indices (from first frequency's global max) ---
    g0 = patterns[0]["gains"]
    i0, j0 = np.unravel_index(np.nanargmax(g0), g0.shape)

    # --- draw initial lines and store handles ---
    line_theta = []  # θ cut lines per row
    line_phi = []    # φ cut lines per row

    for r, p in enumerate(patterns):
        gains = p["gains"]
        thetas = p["thetas"]
        phis = p["phis"]

        theta_rad = np.deg2rad(thetas)
        phi_rad = np.deg2rad(phis)

        # set r-limits
        ax[r, 0].set_rlim([rmin, rmax])
        ax[r, 1].set_rlim([rmin, rmax])

        # plot initial cuts
        lt, = ax[r, 0].plot(theta_rad, gains[:, j0], color="r", linewidth=3)
        lp, = ax[r, 1].plot(phi_rad,   gains[i0, :], color="r", linewidth=3)

        line_theta.append(lt)
        line_phi.append(lp)

        # titles (show actual degrees, not indices)
        ax[r, 0].set_title(f"f={p['f']:.3f} MHz  |  θ cut (φ = {phis[j0]:.1f}°)")
        ax[r, 1].set_title(f"f={p['f']:.3f} MHz  |  φ cut (θ = {thetas[i0]:.1f}°)")

    # --- sliders (one pair controlling all rows) ---
    fig.subplots_adjust(bottom=0.12)

    sax_phi   = fig.add_axes([0.12, 0.05, 0.30, 0.03])
    sax_theta = fig.add_axes([0.58, 0.05, 0.30, 0.03])

    # Use shape of first pattern to define slider ranges
    n_theta, n_phi = patterns[0]["gains"].shape

    s_phi = Slider(
        ax=sax_phi,
        label="φ index",
        valmin=0,
        valmax=n_phi - 1,
        valinit=j0,
        valstep=1
    )
    s_theta = Slider(
        ax=sax_theta,
        label="θ index",
        valmin=0,
        valmax=n_theta - 1,
        valinit=i0,
        valstep=1
    )

    def update_phi(_val):
        j = int(s_phi.val)
        for r, p in enumerate(patterns):
            gains = p["gains"]
            phis = p["phis"]
            line_theta[r].set_ydata(gains[:, j])
            ax[r, 0].set_title(f"f={p['f']:.3f} MHz  |  θ cut (φ = {phis[j]:.1f}°)")
        fig.canvas.draw_idle()

    def update_theta(_val):
        i = int(s_theta.val)
        for r, p in enumerate(patterns):
            gains = p["gains"]
            thetas = p["thetas"]
            line_phi[r].set_ydata(gains[i, :])
            ax[r, 1].set_title(f"f={p['f']:.3f} MHz  |  φ cut (θ = {thetas[i]:.1f}°)")
        fig.canvas.draw_idle()

    s_phi.on_changed(update_phi)
    s_theta.on_changed(update_theta)

    return fig, ax, (s_theta, s_phi)

