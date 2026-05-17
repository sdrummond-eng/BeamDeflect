"""Dataclasses describing a beam configuration, applied loads, and supports."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class LoadType(str, Enum):
    """Kind of load applied to the beam."""

    POINT = "point"
    DISTRIBUTED = "distributed"
    MOMENT = "moment"


class SupportType(str, Enum):
    """Kind of support constraining the beam."""

    PINNED = "pinned"
    ROLLER = "roller"
    FIXED = "fixed"
    FREE = "free"


@dataclass
class Load:
    """An applied load on the beam.

    Sign convention: ``magnitude`` is downward-positive for point and
    distributed loads (i.e., a positive value pulls the beam toward
    negative y).  For applied couples, positive ``magnitude`` is
    counter-clockwise (sagging-positive at the point of application).

    Attributes:
        load_type: The kind of load (point, distributed, or moment).
        magnitude: Load magnitude — N for point loads, N/m for distributed
            loads, N·m for moments.
        position: Position along the beam in metres. For distributed loads,
            the start position of the load.
        end_position: For distributed loads, the end position in metres;
            ``None`` for point loads and applied moments.
    """

    load_type: LoadType
    magnitude: float
    position: float
    end_position: float | None = None


@dataclass
class SupportCondition:
    """A support constraint applied at a point along the beam.

    Attributes:
        support_type: The kind of support.
        position: Position of the support along the beam in metres.
    """

    support_type: SupportType
    position: float


@dataclass
class BeamConfig:
    """Geometry, material, section, and loading description of a prismatic beam.

    Attributes:
        length: Beam length L in metres.
        elastic_modulus: Young's modulus E in pascals.
        moment_of_inertia: Second moment of area I in metres⁴. For a
            rectangular section this can be computed via
            :func:`beam.calculator.compute_second_moment_of_area`.
        width_mm: Cross-section width b in millimetres (optional; only
            required if ``moment_of_inertia`` was derived from a rectangle
            and downstream code needs to recover the section).
        height_mm: Cross-section height h in millimetres (required by
            :func:`beam.calculator.compute_max_stress` so the extreme-fibre
            distance c = h/2 can be obtained).
        loads: Applied loads acting on the beam.
        supports: Support conditions constraining the beam.
    """

    length: float
    elastic_modulus: float
    moment_of_inertia: float
    width_mm: float | None = None
    height_mm: float | None = None
    loads: list[Load] = field(default_factory=list)
    supports: list[SupportCondition] = field(default_factory=list)
