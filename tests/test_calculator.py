"""Unit tests for :mod:`beam.calculator`.

Each test exercises a closed-form benchmark from Roark's Table 8.1 and
asserts that the calculation engine matches the textbook formula
evaluated with the same parameters.  Expected values are computed in
the test (rather than hard-coded mm figures) so the assertion is
self-consistent with the cited formula.
"""

from __future__ import annotations

import numpy as np
import pytest

from beam.calculator import (
    compute_bending_moment,
    compute_deflection,
    compute_reactions,
    compute_second_moment_of_area,
)
from beam.models import BeamConfig, Load, LoadType, SupportCondition, SupportType


# Shared section/material — Steel, 100 mm × 200 mm rectangle.
E_STEEL = 200e9  # Pa
B_MM = 100.0
H_MM = 200.0


def _rect_beam(
    length: float,
    loads: list[Load],
    supports: list[SupportCondition],
) -> BeamConfig:
    """Build a BeamConfig for the shared steel rectangle."""
    return BeamConfig(
        length=length,
        elastic_modulus=E_STEEL,
        moment_of_inertia=compute_second_moment_of_area(B_MM, H_MM),
        width_mm=B_MM,
        height_mm=H_MM,
        loads=loads,
        supports=supports,
    )


def test_compute_deflection_simply_supported_point_load() -> None:
    """Case 1 — Simply supported beam under a central point load.

    Roark Table 8.1, simply supported beam, intermediate concentrated load:
        δ_max = P · L³ / (48 · E · I)
        M_max = P · L / 4
    Parameters: L = 5 m, E = 200 GPa, 100 × 200 mm rectangle, P = 10 kN
    at mid-span.  With these inputs the formula gives δ ≈ 1.953 mm and
    M_max = 12.5 kN·m.
    """
    L = 5.0
    P = 10_000.0
    cfg = _rect_beam(
        length=L,
        loads=[Load(LoadType.POINT, magnitude=P, position=L / 2)],
        supports=[
            SupportCondition(SupportType.PINNED, 0.0),
            SupportCondition(SupportType.ROLLER, L),
        ],
    )
    EI = E_STEEL * cfg.moment_of_inertia

    delta_expected = P * L**3 / (48.0 * EI)        # Roark Table 8.1, Case 1e.
    m_max_expected = P * L / 4.0                   # Roark Table 8.1, Case 1e.

    x = np.linspace(0.0, L, 1001)
    delta = compute_deflection(cfg, x)
    moment = compute_bending_moment(cfg, x)

    # Numerical double integration: rel=1e-3 is comfortably below the
    # 1001-point trapezoid error for this loading.
    assert float(delta.max()) == pytest.approx(delta_expected, rel=1e-3)
    # The maximum lies at the load point and falls exactly on the grid.
    assert float(np.max(np.abs(moment))) == pytest.approx(m_max_expected, rel=1e-6)


def test_compute_deflection_cantilever_end_load() -> None:
    """Case 3 — Cantilever with a point load at the free end.

    Roark Table 8.1, cantilever, point load at free end:
        δ_tip   = P · L³ / (3 · E · I)
        M_wall  = −P · L
    Parameters: L = 4 m, E = 200 GPa, 100 × 200 mm rectangle, P = 5 kN
    at x = L.  With these inputs the formula gives δ_tip ≈ 8.0 mm and
    M_wall = −20.0 kN·m.
    """
    L = 4.0
    P = 5_000.0
    cfg = _rect_beam(
        length=L,
        loads=[Load(LoadType.POINT, magnitude=P, position=L)],
        supports=[SupportCondition(SupportType.FIXED, 0.0)],
    )
    EI = E_STEEL * cfg.moment_of_inertia

    delta_tip_expected = P * L**3 / (3.0 * EI)     # Roark Table 8.1, Case 1a.
    m_wall_expected = -P * L                       # Roark Table 8.1, Case 1a.

    x = np.linspace(0.0, L, 1001)
    delta = compute_deflection(cfg, x)
    moment = compute_bending_moment(cfg, x)

    # Tip deflection is the last sample, monotonic for this loading.
    assert float(delta[-1]) == pytest.approx(delta_tip_expected, rel=1e-3)
    # Wall moment is the bending moment at x = 0 (sagging-positive sign).
    assert float(moment[0]) == pytest.approx(m_wall_expected, rel=1e-9)
    # And it should appear in the reaction output as the moment_Nm field.
    reactions = compute_reactions(cfg)
    assert reactions[0]["moment_Nm"] == pytest.approx(m_wall_expected, rel=1e-9)
    assert reactions[0]["force_N"] == pytest.approx(P, rel=1e-9)


def test_compute_shear_distribution() -> None:
    """Shear force on an SS beam with a central point load is a ±P/2 step.

    For Case 1 (SS, central load P at L/2):
        V(x) = +P/2 for 0 ≤ x < L/2
        V(x) = −P/2 for L/2 < x ≤ L
    Source: Roark Table 8.1, Case 1e (shear column).
    """
    L = 5.0
    P = 10_000.0
    cfg = _rect_beam(
        length=L,
        loads=[Load(LoadType.POINT, magnitude=P, position=L / 2)],
        supports=[
            SupportCondition(SupportType.PINNED, 0.0),
            SupportCondition(SupportType.ROLLER, L),
        ],
    )
    # Use points that straddle the discontinuity but don't land on it.
    x = np.array([0.0, 0.25 * L, 0.49 * L, 0.51 * L, 0.75 * L, L])
    from beam.calculator import compute_shear_force

    V = compute_shear_force(cfg, x)
    np.testing.assert_allclose(
        V,
        [P / 2, P / 2, P / 2, -P / 2, -P / 2, -P / 2],
        rtol=1e-9,
    )


def test_compute_moment_distribution() -> None:
    """Bending moment on an SS beam with a central point load is triangular.

    For Case 1 (SS, central load P at L/2):
        M(x) = P · x / 2          for 0 ≤ x ≤ L/2
        M(x) = P · (L − x) / 2    for L/2 ≤ x ≤ L
    Source: Roark Table 8.1, Case 1e (moment column).
    """
    L = 5.0
    P = 10_000.0
    cfg = _rect_beam(
        length=L,
        loads=[Load(LoadType.POINT, magnitude=P, position=L / 2)],
        supports=[
            SupportCondition(SupportType.PINNED, 0.0),
            SupportCondition(SupportType.ROLLER, L),
        ],
    )
    x = np.linspace(0.0, L, 1001)
    M = compute_bending_moment(cfg, x)

    # Build the analytical moment on the same grid.
    M_expected = np.where(x <= L / 2, P * x / 2.0, P * (L - x) / 2.0)
    np.testing.assert_allclose(M, M_expected, rtol=1e-9, atol=1e-9)

    # Spot-check the peak in physical units.
    assert float(M.max()) == pytest.approx(P * L / 4.0, rel=1e-9)


def test_compute_reactions_balance() -> None:
    """Reactions equilibrate the applied loads for every supported config.

    Verifies the three end-condition families requested:
      • Simply supported beam under Case 2 loading (UDL over full span):
          R_A = R_B = w · L / 2
          δ_max = 5 · w · L⁴ / (384 · E · I)        (Roark Table 8.1, Case 2e)
      • Cantilever under Case 3 loading: ΣF = P, M_wall = −P·L.
      • Fixed-fixed beam under a centre point load:
          R_A = R_B = P / 2
          M_A = M_B = −P · L / 8                     (Roark Table 8.1, Case 1d)
    """
    # --- Simply supported, full-span UDL (Case 2 of the user's brief) ----
    L = 5.0
    w = 2_000.0
    cfg = _rect_beam(
        length=L,
        loads=[Load(LoadType.DISTRIBUTED, magnitude=w, position=0.0, end_position=L)],
        supports=[
            SupportCondition(SupportType.PINNED, 0.0),
            SupportCondition(SupportType.ROLLER, L),
        ],
    )
    EI = E_STEEL * cfg.moment_of_inertia
    reactions = compute_reactions(cfg)
    assert reactions[0]["force_N"] == pytest.approx(w * L / 2.0, rel=1e-9)
    assert reactions[1]["force_N"] == pytest.approx(w * L / 2.0, rel=1e-9)
    # Vertical equilibrium check: ΣR = total downward force.
    assert (
        reactions[0]["force_N"] + reactions[1]["force_N"]
        == pytest.approx(w * L, rel=1e-9)
    )
    # And while we're here, verify the Case 2 deflection benchmark.
    x = np.linspace(0.0, L, 1001)
    delta = compute_deflection(cfg, x)
    delta_expected = 5.0 * w * L**4 / (384.0 * EI)   # Roark Table 8.1, Case 2e.
    assert float(delta.max()) == pytest.approx(delta_expected, rel=1e-3)

    # --- Cantilever (Case 3) -------------------------------------------
    L = 4.0
    P = 5_000.0
    cfg = _rect_beam(
        length=L,
        loads=[Load(LoadType.POINT, magnitude=P, position=L)],
        supports=[SupportCondition(SupportType.FIXED, 0.0)],
    )
    reactions = compute_reactions(cfg)
    assert reactions[0]["force_N"] == pytest.approx(P, rel=1e-9)
    assert reactions[0]["moment_Nm"] == pytest.approx(-P * L, rel=1e-9)

    # --- Fixed-fixed, centre point load -------------------------------
    L = 5.0
    P = 10_000.0
    cfg = _rect_beam(
        length=L,
        loads=[Load(LoadType.POINT, magnitude=P, position=L / 2)],
        supports=[
            SupportCondition(SupportType.FIXED, 0.0),
            SupportCondition(SupportType.FIXED, L),
        ],
    )
    reactions = compute_reactions(cfg)
    assert reactions[0]["force_N"] == pytest.approx(P / 2.0, rel=1e-9)
    assert reactions[1]["force_N"] == pytest.approx(P / 2.0, rel=1e-9)
    assert reactions[0]["moment_Nm"] == pytest.approx(-P * L / 8.0, rel=1e-9)
    assert reactions[1]["moment_Nm"] == pytest.approx(-P * L / 8.0, rel=1e-9)
