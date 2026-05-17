"""Pure calculation functions for beam deflection analysis.

All formulas use SI units throughout (metres, newtons, pascals).  Inline
comments cite the source of each closed-form expression; unless noted
otherwise, citations refer to:

    Young, W. C. & Budynas, R. G., "Roark's Formulas for Stress and
    Strain", 7th ed., McGraw-Hill, 2002.

Sign conventions
----------------
- The coordinate ``x`` runs from 0 at the left end to ``L`` at the right end.
- Load ``magnitude`` is downward-positive for point and distributed loads.
- Shear force ``V(x)`` is the sum of upward forces to the left of the cut
  (so a downward point load produces a negative jump).
- Bending moment ``M(x)`` is sagging-positive: positive ``M`` tensions the
  bottom fibre, in agreement with the Euler–Bernoulli relation
  ``M = E·I·d²y/dx²`` with ``y`` measured upward.
- The deflection returned by :func:`compute_deflection` is reported
  downward-positive, which is the standard engineering convention used
  in Roark's tables.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import cumulative_trapezoid

from beam.models import BeamConfig, Load, LoadType, SupportCondition, SupportType


# ---------------------------------------------------------------------------
# Section properties
# ---------------------------------------------------------------------------


def compute_second_moment_of_area(width_mm: float, height_mm: float) -> float:
    """Second moment of area I of a solid rectangle about its centroidal axis.

    Args:
        width_mm: Section width b in millimetres.
        height_mm: Section height h (parallel to the load) in millimetres.

    Returns:
        I in metres⁴.
    """
    if width_mm <= 0 or height_mm <= 0:
        raise ValueError("width_mm and height_mm must be positive.")
    b = width_mm / 1000.0  # mm -> m
    h = height_mm / 1000.0
    # Rectangular section about the centroidal axis: I = b·h³ / 12
    # Source: Roark's Table A.1 (Properties of Sections), solid rectangle.
    return b * h**3 / 12.0


# ---------------------------------------------------------------------------
# Support classification
# ---------------------------------------------------------------------------


# String tags used to identify the three configurations the user requested.
_SIMPLY_SUPPORTED = "simply_supported"
_CANTILEVER = "cantilever"
_FIXED_FIXED = "fixed_fixed"


def _classify_supports(
    supports: list[SupportCondition], length: float
) -> tuple[str, list[SupportCondition]]:
    """Decide whether the supports form a SS, cantilever, or fixed-fixed beam.

    Returns a ``(kind, sorted_supports)`` tuple.  Only the three end-condition
    families requested by the user are recognised; anything else raises.
    """
    if not supports:
        raise ValueError("BeamConfig.supports is empty; cannot determine reactions.")

    sorted_sup = sorted(supports, key=lambda s: s.position)
    types = [s.support_type for s in sorted_sup]
    positions = [s.position for s in sorted_sup]

    tol = 1e-9
    spans_full = (
        len(sorted_sup) == 2
        and abs(positions[0]) < tol
        and abs(positions[-1] - length) < tol
    )

    # Cantilever: a single fixed support at one end, free at the other.
    if len(sorted_sup) == 1 and types[0] is SupportType.FIXED:
        if abs(positions[0]) < tol:
            return _CANTILEVER, sorted_sup
        if abs(positions[0] - length) < tol:
            # Mirror so we always integrate from the fixed end on the left.
            raise ValueError(
                "Cantilever fixed at the right end is not supported; "
                "place the fixed support at position 0."
            )

    # Fixed–fixed: both ends fixed.
    if spans_full and types[0] is SupportType.FIXED and types[1] is SupportType.FIXED:
        return _FIXED_FIXED, sorted_sup

    # Simply supported: one pinned + one roller (in either order), at the ends.
    ss_pair = {SupportType.PINNED, SupportType.ROLLER}
    if spans_full and set(types) <= ss_pair and SupportType.PINNED in types:
        return _SIMPLY_SUPPORTED, sorted_sup

    raise ValueError(
        f"Unsupported configuration: {[t.value for t in types]} at {positions}. "
        "Only simply supported, cantilever, and fixed-fixed beams are supported."
    )


# ---------------------------------------------------------------------------
# Reactions
# ---------------------------------------------------------------------------


def compute_reactions(config: BeamConfig) -> list[dict[str, float]]:
    """Compute the support reactions for the loading on ``config``.

    Returns a list of dictionaries, one per support, ordered by position
    along the beam.  Each entry contains ``position`` (m), ``force_N``
    (upward-positive vertical reaction), and ``moment_Nm`` (sagging-positive
    bending moment exerted on the beam at the support — non-zero only for
    fixed supports).

    Supported end conditions: simply supported, cantilever, fixed-fixed.
    """
    kind, supports = _classify_supports(config.supports, config.length)
    L = config.length

    if kind == _SIMPLY_SUPPORTED:
        return _reactions_simply_supported(config, supports, L)
    if kind == _CANTILEVER:
        return _reactions_cantilever(config, supports, L)
    if kind == _FIXED_FIXED:
        return _reactions_fixed_fixed(config, supports, L)
    raise AssertionError(f"Unhandled support kind: {kind}")


def _reactions_simply_supported(
    config: BeamConfig, supports: list[SupportCondition], L: float
) -> list[dict[str, float]]:
    """Vertical reactions for a beam supported at both ends.

    With supports at x_A = 0 and x_B = L, equilibrium gives
        R_A = (1/L) · Σ P_i · (L − a_i)
        R_B = (1/L) · Σ P_i · a_i
    for point loads P_i at a_i (downward-positive); a UDL is handled by
    replacing it with its resultant acting at the load centroid.
    Source: Roark Table 8.1, simply supported beam — concentrated load
    case 1e and uniformly distributed load case 2e.
    """
    R_A = 0.0
    R_B = 0.0
    for load in config.loads:
        if load.load_type is LoadType.POINT:
            a = load.position
            P = load.magnitude
            # Reaction split for a single point load: lever-arm rule.
            # Source: Roark Table 8.1, Case 1e (simply supported, intermediate load).
            R_A += P * (L - a) / L
            R_B += P * a / L
        elif load.load_type is LoadType.DISTRIBUTED:
            p, q = load.position, _required_end(load)
            w = load.magnitude
            resultant = w * (q - p)
            centroid = 0.5 * (p + q)
            # Same lever-arm rule applied to the UDL resultant.
            # Source: Roark Table 8.1, Case 2e (simply supported, partial UDL).
            R_A += resultant * (L - centroid) / L
            R_B += resultant * centroid / L
        elif load.load_type is LoadType.MOMENT:
            # Applied couple M₀ at any position: vertical equilibrium needs
            # equal and opposite end reactions of magnitude M₀/L.
            # Source: Roark Table 8.1, Case 3e (couple on simply supported beam).
            M0 = load.magnitude
            R_A += -M0 / L
            R_B += M0 / L
    return [
        {"position": supports[0].position, "force_N": R_A, "moment_Nm": 0.0},
        {"position": supports[1].position, "force_N": R_B, "moment_Nm": 0.0},
    ]


def _reactions_cantilever(
    config: BeamConfig, supports: list[SupportCondition], L: float
) -> list[dict[str, float]]:
    """Reactions at the fixed end of a cantilever (free at x = L).

    The wall must carry the entire applied load and balance its moment
    about x = 0:
        R_wall  = Σ P_i           (vertical equilibrium)
        M_wall  = −Σ P_i · a_i    (moment equilibrium about the wall;
                                  hogging at the wall is negative).
    Source: Roark Table 8.1, cantilever beam — concentrated load case 1a
    and uniformly distributed load case 2a.
    """
    R = 0.0
    M_wall = 0.0
    for load in config.loads:
        if load.load_type is LoadType.POINT:
            P = load.magnitude
            a = load.position
            R += P
            # Hogging moment at fixed end: −P·a.  Source: Roark Table 8.1, Case 1a.
            M_wall += -P * a
        elif load.load_type is LoadType.DISTRIBUTED:
            p, q = load.position, _required_end(load)
            w = load.magnitude
            resultant = w * (q - p)
            centroid = 0.5 * (p + q)
            R += resultant
            # Hogging moment at fixed end for a UDL: −w·(q−p)·(p+q)/2.
            # Source: Roark Table 8.1, Case 2a (cantilever, partial UDL).
            M_wall += -resultant * centroid
        elif load.load_type is LoadType.MOMENT:
            # An external couple is carried entirely by the wall.
            # Source: Roark Table 8.1, Case 3a (couple on a cantilever).
            M_wall += load.magnitude
    return [{"position": supports[0].position, "force_N": R, "moment_Nm": M_wall}]


def _reactions_fixed_fixed(
    config: BeamConfig, supports: list[SupportCondition], L: float
) -> list[dict[str, float]]:
    """Reactions and fixed-end moments for a beam fixed at both ends.

    Point load P at distance a from the left end (b = L − a):
        R_A = P · b² · (3a + b) / L³
        R_B = P · a² · (a + 3b) / L³
        M_A = −P · a · b² / L²         (hogging at the left wall)
        M_B = −P · a² · b  / L²        (hogging at the right wall)
    Source: Roark Table 8.1, fixed-fixed beam, concentrated intermediate
    load (Case 1d in the 7th edition).

    A UDL of intensity w between x = p and x = q is handled by integrating
    the point-load formulas over the load span — see ``_fixed_fixed_udl``.
    """
    R_A = 0.0
    R_B = 0.0
    M_A = 0.0
    M_B = 0.0

    for load in config.loads:
        if load.load_type is LoadType.POINT:
            P = load.magnitude
            a = load.position
            b = L - a
            # Roark Table 8.1, Case 1d (fixed-fixed, concentrated load).
            R_A += P * b**2 * (3.0 * a + b) / L**3
            R_B += P * a**2 * (a + 3.0 * b) / L**3
            M_A += -P * a * b**2 / L**2
            M_B += -P * a**2 * b / L**2
        elif load.load_type is LoadType.DISTRIBUTED:
            p, q = load.position, _required_end(load)
            w = load.magnitude
            # Roark Table 8.1, Case 2d (fixed-fixed, partial UDL); the
            # integrated form below reduces to the textbook full-span
            # result R = wL/2, M = wL²/12 when (p, q) = (0, L).
            dR_A, dR_B, dM_A, dM_B = _fixed_fixed_udl(w, p, q, L)
            R_A += dR_A
            R_B += dR_B
            M_A += dM_A
            M_B += dM_B
        elif load.load_type is LoadType.MOMENT:
            # External couple M₀ at distance a from the left end (b = L − a)
            # on a fixed-fixed span:
            #   R_A = −R_B = −6 · M₀ · a · b / L³
            #   M_A = M₀ · b · (2a − b) / L²
            #   M_B = M₀ · a · (2b − a) / L²
            # Source: Roark Table 8.1, Case 3d.
            M0 = load.magnitude
            a = load.position
            b = L - a
            R_A += -6.0 * M0 * a * b / L**3
            R_B += 6.0 * M0 * a * b / L**3
            M_A += M0 * b * (2.0 * a - b) / L**2
            M_B += M0 * a * (2.0 * b - a) / L**2

    return [
        {"position": supports[0].position, "force_N": R_A, "moment_Nm": M_A},
        {"position": supports[1].position, "force_N": R_B, "moment_Nm": M_B},
    ]


def _fixed_fixed_udl(
    w: float, p: float, q: float, L: float
) -> tuple[float, float, float, float]:
    """Reactions/end-moments for a UDL w over [p, q] on a fixed-fixed span L.

    Obtained by integrating the point-load formulas of Roark Table 8.1
    Case 1d over the load segment:

        R_A = (w/L³) · ∫ₚ^q (L³ − 3L·x² + 2·x³) dx
        R_B = (w/L³) · ∫ₚ^q (3L·x² − 2·x³) dx
        M_A = −(w/L²) · ∫ₚ^q (L² · x²/2 − 2L·x³/3 + x⁴/4)′ dx
        M_B = −(w/L²) · ∫ₚ^q (L · x³/3 − x⁴/4)′ dx

    Each integral is evaluated analytically; the full-span case
    (p, q) = (0, L) collapses to the standard result
    R = wL/2, M = wL²/12 (Roark Table 8.1, Case 2d, full span).
    """

    def f_RA(x: float) -> float:
        # Antiderivative of (L³ − 3L·x² + 2x³).
        return L**3 * x - L * x**3 + 0.5 * x**4

    def f_RB(x: float) -> float:
        # Antiderivative of (3L·x² − 2x³).
        return L * x**3 - 0.5 * x**4

    def f_MA(x: float) -> float:
        # Antiderivative of x·(L − x)² = L²·x − 2L·x² + x³.
        return 0.5 * L**2 * x**2 - (2.0 / 3.0) * L * x**3 + 0.25 * x**4

    def f_MB(x: float) -> float:
        # Antiderivative of x²·(L − x) = L·x² − x³.
        return (1.0 / 3.0) * L * x**3 - 0.25 * x**4

    R_A = w * (f_RA(q) - f_RA(p)) / L**3
    R_B = w * (f_RB(q) - f_RB(p)) / L**3
    M_A = -w * (f_MA(q) - f_MA(p)) / L**2
    M_B = -w * (f_MB(q) - f_MB(p)) / L**2
    return R_A, R_B, M_A, M_B


def _required_end(load: Load) -> float:
    if load.end_position is None:
        raise ValueError(
            f"Distributed load at x={load.position} has no end_position set."
        )
    return load.end_position


# ---------------------------------------------------------------------------
# Shear and bending moment diagrams
# ---------------------------------------------------------------------------


def _left_support_state(
    config: BeamConfig,
) -> tuple[str, float, float, float]:
    """Return ``(kind, x_left, R_left, M_left)`` for the integration start.

    ``M_left`` is the bending moment introduced by the leftmost support
    (zero for SS, the hogging fixed-end moment for cantilever/fixed-fixed).
    """
    kind, supports = _classify_supports(config.supports, config.length)
    reactions = compute_reactions(config)
    left = reactions[0]
    return kind, left["position"], left["force_N"], left["moment_Nm"]


def compute_shear_force(
    config: BeamConfig, x_positions: NDArray[np.floating] | Iterable[float]
) -> NDArray[np.float64]:
    """Shear force V(x) at each requested x.

    ``V(x)`` is taken as the sum of upward forces acting to the LEFT of the
    cut: the leftmost reaction enters with its own sign, downward point
    loads subtract from V at their position, and a downward UDL of
    intensity w over [p, q] subtracts ``w·(min(x, q) − p)`` once x exceeds p.
    Source: standard mechanics-of-materials sign convention; see e.g.
    Hibbeler, "Mechanics of Materials", §6.1, and Roark §8.1.
    """
    x = np.asarray(x_positions, dtype=np.float64)
    _, x_left, R_left, _ = _left_support_state(config)

    V = np.full_like(x, R_left, dtype=np.float64)
    # Any additional left-of-domain support (only the leftmost is at x_left=0
    # in the supported configurations) is already captured above.
    for load in config.loads:
        if load.load_type is LoadType.POINT:
            # Heaviside step: downward point load knocks V down past its position.
            mask = x >= load.position
            V[mask] -= load.magnitude
        elif load.load_type is LoadType.DISTRIBUTED:
            p, q = load.position, _required_end(load)
            w = load.magnitude
            # V drops linearly from 0 over the active portion of the UDL.
            # Source: integration of dV/dx = −w(x).
            active_x = np.clip(x, p, q)
            inside_or_past = x > p
            V[inside_or_past] -= w * (active_x[inside_or_past] - p)
        # Pure moments do not contribute to shear.
    return V


def compute_bending_moment(
    config: BeamConfig, x_positions: NDArray[np.floating] | Iterable[float]
) -> NDArray[np.float64]:
    """Bending moment M(x) at each requested x (sagging-positive).

    Computed as the sum of moments about the cut from everything to the
    LEFT of x:
        M(x) = M_wall_left + R_left·x
               − Σ P_i · (x − a_i)            for point loads with a_i ≤ x
               − ∫ₚ^{min(x,q)} w · (x − s) ds for each UDL.
    The integral evaluates in closed form to
        −w · (x_eff − p) · (x − (p + x_eff)/2)  with x_eff = min(x, q).
    Source: Euler–Bernoulli statics; cf. Roark §8.1 and Hibbeler §6.2.
    """
    x = np.asarray(x_positions, dtype=np.float64)
    _, x_left, R_left, M_left = _left_support_state(config)

    # M(x) = M_left + R_left · (x − x_left).
    M = M_left + R_left * (x - x_left)

    for load in config.loads:
        if load.load_type is LoadType.POINT:
            mask = x >= load.position
            # Downward point load P at a: −P·(x − a) for x ≥ a.
            M[mask] -= load.magnitude * (x[mask] - load.position)
        elif load.load_type is LoadType.DISTRIBUTED:
            p, q = load.position, _required_end(load)
            w = load.magnitude
            x_eff = np.clip(x, p, q)
            active = x > p
            # Closed-form moment of a partial UDL about the cut.
            # Source: integration of −w·(x − s) ds from p to min(x, q).
            seg_len = x_eff[active] - p
            arm = x[active] - 0.5 * (p + x_eff[active])
            M[active] -= w * seg_len * arm
        elif load.load_type is LoadType.MOMENT:
            # An applied couple M₀ at position a adds +M₀ to M(x) for x ≥ a.
            # Source: Roark Table 8.1, Case 3 (couple on a beam).
            mask = x >= load.position
            M[mask] += load.magnitude

    return M


# ---------------------------------------------------------------------------
# Deflection
# ---------------------------------------------------------------------------


def compute_deflection(
    config: BeamConfig, x_positions: NDArray[np.floating] | Iterable[float]
) -> NDArray[np.float64]:
    """Transverse deflection y(x) at each requested x (downward-positive).

    The Euler–Bernoulli relation ``M = E·I·d²y/dx²`` (with y upward) is
    integrated twice along the supplied ``x_positions``.  The two
    constants of integration are determined from the kinematic boundary
    conditions appropriate to the end conditions:

        Simply supported:  y(0) = 0, y(L) = 0
        Cantilever:        y(0) = 0, y'(0) = 0
        Fixed-fixed:       y(0) = 0, y'(0) = 0
                           (y(L) = 0, y'(L) = 0 are enforced implicitly
                            by the fixed-end reactions in
                            :func:`compute_reactions`.)

    Source: Roark §8.1, Eq. 8.1-2 (Bernoulli–Euler differential equation
    of the elastic curve); Gere & Goodno, "Mechanics of Materials", §9.2.

    The returned deflection is downward-positive (matches Roark's tables
    and engineering convention); internally we integrate with y-upward
    and negate at the end.
    """
    x = np.asarray(x_positions, dtype=np.float64)
    if x.ndim != 1 or x.size < 2:
        raise ValueError("x_positions must be a 1-D array with at least 2 samples.")
    if not np.all(np.diff(x) > 0):
        raise ValueError("x_positions must be strictly increasing.")

    EI = config.elastic_modulus * config.moment_of_inertia
    if EI <= 0:
        raise ValueError("E·I must be positive.")

    M = compute_bending_moment(config, x)
    # κ(x) = M(x) / (E·I) is the curvature for small deflections.
    # Source: Roark Eq. 8.1-2, Bernoulli–Euler elastic curve.
    curvature = M / EI

    # First integration: slope_increment(x) = ∫₀ˣ κ(s) ds = y'(x) − y'(0).
    slope_inc = cumulative_trapezoid(curvature, x, initial=0.0)
    # Second integration: inner(x) = ∫₀ˣ slope_increment(s) ds
    # so y(x) − y(0) − y'(0)·(x − x₀) = inner(x).
    inner = cumulative_trapezoid(slope_inc, x, initial=0.0)

    kind, _ = _classify_supports(config.supports, config.length)

    if kind == _CANTILEVER:
        # y(0) = 0 and y'(0) = 0; the two constants vanish.
        # Source: Roark §8.1, cantilever boundary conditions.
        y_up = inner
    elif kind == _FIXED_FIXED:
        # y(0) = 0 and y'(0) = 0; the remaining end conditions y(L)=y'(L)=0
        # are satisfied automatically by the reactions in compute_reactions.
        # Source: Roark §8.1, fixed-fixed boundary conditions.
        y_up = inner
    elif kind == _SIMPLY_SUPPORTED:
        # y(0) = 0 fixes the additive constant; y(L) = 0 fixes the slope:
        #   0 = y'(0)·(L − 0) + inner(L)  ⇒  y'(0) = −inner(L) / L
        # Source: Roark §8.1, simply supported boundary conditions.
        L = x[-1] - x[0]
        y_prime_0 = -inner[-1] / L
        y_up = y_prime_0 * (x - x[0]) + inner
    else:
        raise AssertionError(f"Unhandled support kind: {kind}")

    # Convert mathematical (upward-positive) y to engineering (downward-positive).
    return -y_up


# ---------------------------------------------------------------------------
# Stress
# ---------------------------------------------------------------------------


def compute_max_stress(config: BeamConfig) -> float:
    """Peak bending stress σ_max anywhere along the beam, in pascals.

    Uses the flexure formula σ = M·c / I with c = h/2 for a rectangular
    section.  M_max is taken as the maximum of |M(x)| sampled on a fine
    grid (1001 points along the span); for the load types handled here
    the extremum always lies at a support, under a point load, or at a
    UDL endpoint — all of which fall on the sampled grid for any
    reasonable density.
    Source: Roark §8.1, Eq. 8.1-12 (Euler–Bernoulli flexure formula).
    """
    if config.height_mm is None:
        raise ValueError(
            "compute_max_stress requires BeamConfig.height_mm so that "
            "the extreme-fibre distance c = h/2 can be determined."
        )
    h = config.height_mm / 1000.0  # mm -> m
    c = 0.5 * h  # Distance from neutral axis to extreme fibre for a rectangle.

    x = np.linspace(0.0, config.length, 1001)
    M = compute_bending_moment(config, x)
    M_max = float(np.max(np.abs(M)))

    # σ = M · c / I — Roark Eq. 8.1-12.
    return M_max * c / config.moment_of_inertia
