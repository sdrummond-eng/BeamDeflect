"""Tkinter GUI for the BeamDeflect application.

Provides input forms for beam geometry, loads, and supports, and embeds
matplotlib plots for the deflection, shear, and moment diagrams.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from beam.calculator import (
    compute_bending_moment,
    compute_deflection,
    compute_max_stress,
    compute_second_moment_of_area,
    compute_shear_force,
)
from beam.models import (
    BeamConfig,
    Load,
    LoadType,
    SupportCondition,
    SupportType,
)


# Short-term elastic modulus of common structural materials (pascals).
# Steel — typical structural carbon steel.
# Aluminium — typical 6061-T6.
# Timber — typical softwood mean MoE (Eurocode 5 / AS 1720 ranges, ~10–12 GPa).
MATERIAL_MODULUS_PA: dict[str, float] = {
    "Steel": 200e9,
    "Aluminium": 69e9,
    "Timber": 11e9,
}

SUPPORT_OPTIONS: tuple[str, ...] = ("Simply Supported", "Cantilever", "Fixed-Fixed")


def _supports_for(kind: str, length: float) -> list[SupportCondition]:
    """Translate a UI support label into the SupportCondition list."""
    if kind == "Simply Supported":
        return [
            SupportCondition(SupportType.PINNED, 0.0),
            SupportCondition(SupportType.ROLLER, length),
        ]
    if kind == "Cantilever":
        return [SupportCondition(SupportType.FIXED, 0.0)]
    if kind == "Fixed-Fixed":
        return [
            SupportCondition(SupportType.FIXED, 0.0),
            SupportCondition(SupportType.FIXED, length),
        ]
    raise ValueError(f"Unknown support type: {kind!r}")


# ---------------------------------------------------------------------------
# Numeric parsing helpers (raise ValueError with a UI-friendly message).
# ---------------------------------------------------------------------------


def _parse_float(
    text: str,
    name: str,
    *,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float:
    """Parse ``text`` as a finite float, optionally checking bounds."""
    if text is None or str(text).strip() == "":
        raise ValueError(f"{name} is required.")
    try:
        v = float(text)
    except ValueError:
        raise ValueError(f"{name} must be a number (got {text!r}).") from None
    if not np.isfinite(v):
        raise ValueError(f"{name} must be finite.")
    if min_value is not None and v < min_value:
        raise ValueError(f"{name} must be ≥ {min_value} (got {v}).")
    if max_value is not None and v > max_value:
        raise ValueError(f"{name} must be ≤ {max_value} (got {v}).")
    return v


def _parse_positive(text: str, name: str) -> float:
    """Parse a strictly positive float (rejects 0 and negatives)."""
    v = _parse_float(text, name)
    if v <= 0:
        raise ValueError(f"{name} must be greater than zero (got {v}).")
    return v


# ---------------------------------------------------------------------------
# Application window
# ---------------------------------------------------------------------------


class BeamDeflectApp(tk.Tk):
    """Main application window for BeamDeflect."""

    NUM_X_SAMPLES = 401

    def __init__(self) -> None:
        """Initialise the main window and build the widget tree."""
        super().__init__()
        self.title("BeamDeflect")
        self.geometry("1150x700")

        # Accumulated point loads — list of (magnitude_kN, position_m).
        self._point_loads: list[tuple[float, float]] = []

        self._build_input_panel()
        self._build_plot_panel()

        # The plot panel takes any extra horizontal space on resize.
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

    # -- Layout ------------------------------------------------------------

    def _build_input_panel(self) -> None:
        """Create the input panel for beam geometry, loads, and supports."""
        frame = ttk.LabelFrame(self, text="Inputs", padding=8)
        frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        frame.columnconfigure(1, weight=1)

        # --- Geometry & material -----------------------------------------
        row = 0
        ttk.Label(frame, text="Beam length (m):").grid(row=row, column=0, sticky="w")
        self.length_var = tk.StringVar(value="5.0")
        ttk.Entry(frame, textvariable=self.length_var, width=14).grid(
            row=row, column=1, sticky="ew", padx=4, pady=2
        )

        row += 1
        ttk.Label(frame, text="Material:").grid(row=row, column=0, sticky="w")
        self.material_var = tk.StringVar(value="Steel")
        ttk.Combobox(
            frame,
            textvariable=self.material_var,
            values=list(MATERIAL_MODULUS_PA),
            state="readonly",
            width=12,
        ).grid(row=row, column=1, sticky="ew", padx=4, pady=2)

        row += 1
        ttk.Label(frame, text="Width (mm):").grid(row=row, column=0, sticky="w")
        self.width_var = tk.StringVar(value="100")
        ttk.Entry(frame, textvariable=self.width_var, width=14).grid(
            row=row, column=1, sticky="ew", padx=4, pady=2
        )

        row += 1
        ttk.Label(frame, text="Height (mm):").grid(row=row, column=0, sticky="w")
        self.height_var = tk.StringVar(value="200")
        ttk.Entry(frame, textvariable=self.height_var, width=14).grid(
            row=row, column=1, sticky="ew", padx=4, pady=2
        )

        row += 1
        ttk.Label(frame, text="Support:").grid(row=row, column=0, sticky="w")
        self.support_var = tk.StringVar(value=SUPPORT_OPTIONS[0])
        ttk.Combobox(
            frame,
            textvariable=self.support_var,
            values=SUPPORT_OPTIONS,
            state="readonly",
            width=12,
        ).grid(row=row, column=1, sticky="ew", padx=4, pady=2)

        # --- Point loads --------------------------------------------------
        row += 1
        ttk.Separator(frame, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(10, 4)
        )
        row += 1
        ttk.Label(frame, text="Point loads").grid(
            row=row, column=0, columnspan=2, sticky="w"
        )

        row += 1
        ttk.Label(frame, text="Magnitude (kN):").grid(row=row, column=0, sticky="w")
        self.pt_mag_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.pt_mag_var, width=14).grid(
            row=row, column=1, sticky="ew", padx=4, pady=2
        )

        row += 1
        ttk.Label(frame, text="Position (m):").grid(row=row, column=0, sticky="w")
        self.pt_pos_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.pt_pos_var, width=14).grid(
            row=row, column=1, sticky="ew", padx=4, pady=2
        )

        row += 1
        ttk.Button(frame, text="Add load", command=self._add_point_load).grid(
            row=row, column=0, sticky="ew", padx=4, pady=2
        )
        ttk.Button(
            frame, text="Remove selected", command=self._remove_point_load
        ).grid(row=row, column=1, sticky="ew", padx=4, pady=2)

        row += 1
        self.loads_list = tk.Listbox(frame, height=5, exportselection=False)
        self.loads_list.grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=4, pady=2
        )

        # --- UDL ----------------------------------------------------------
        row += 1
        ttk.Separator(frame, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(10, 4)
        )
        row += 1
        ttk.Label(frame, text="UDL (kN/m, full span):").grid(
            row=row, column=0, sticky="w"
        )
        self.udl_var = tk.StringVar(value="0")
        ttk.Entry(frame, textvariable=self.udl_var, width=14).grid(
            row=row, column=1, sticky="ew", padx=4, pady=2
        )

        # --- Calculate ----------------------------------------------------
        row += 1
        ttk.Button(frame, text="Calculate", command=self.on_calculate).grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=4, pady=(14, 2)
        )

    def _build_plot_panel(self) -> None:
        """Create the panel hosting the matplotlib result plots."""
        frame = ttk.Frame(self, padding=6)
        frame.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self.fig = Figure(figsize=(7, 6), tight_layout=True)
        self.ax_def = self.fig.add_subplot(311)
        self.ax_bmd = self.fig.add_subplot(312)
        self.ax_sfd = self.fig.add_subplot(313)
        self._reset_axes()

        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        # Result summary labels below the figure.
        summary = ttk.Frame(frame)
        summary.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.max_def_var = tk.StringVar(value="Max deflection: —")
        self.max_stress_var = tk.StringVar(value="Max stress: —")
        ttk.Label(summary, textvariable=self.max_def_var).grid(
            row=0, column=0, sticky="w", padx=4
        )
        ttk.Label(summary, textvariable=self.max_stress_var).grid(
            row=0, column=1, sticky="w", padx=24
        )

    def _reset_axes(self) -> None:
        """Clear the three subplots and reapply titles/labels/grid."""
        self.ax_def.clear()
        self.ax_def.set_title("Deflection")
        self.ax_def.set_ylabel("δ (mm, ↓ +)")
        self.ax_def.grid(True)
        # Plot the dip below the axis so the curve visually matches the
        # beam's deformed shape — engine returns downward-positive δ.
        self.ax_def.invert_yaxis()

        self.ax_bmd.clear()
        self.ax_bmd.set_title("Bending moment diagram")
        self.ax_bmd.set_ylabel("M (kN·m)")
        self.ax_bmd.grid(True)

        self.ax_sfd.clear()
        self.ax_sfd.set_title("Shear force diagram")
        self.ax_sfd.set_ylabel("V (kN)")
        self.ax_sfd.set_xlabel("x (m)")
        self.ax_sfd.grid(True)

    # -- Point load list management ---------------------------------------

    def _add_point_load(self) -> None:
        """Validate the magnitude/position fields and append to the list."""
        try:
            # Parse length first so the position bound is meaningful.
            length = _parse_positive(self.length_var.get(), "Beam length")
            mag = _parse_float(self.pt_mag_var.get(), "Point load magnitude")
            pos = _parse_float(
                self.pt_pos_var.get(),
                "Point load position",
                min_value=0.0,
                max_value=length,
            )
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        self._point_loads.append((mag, pos))
        self.loads_list.insert("end", f"{mag:g} kN @ {pos:g} m")
        self.pt_mag_var.set("")
        self.pt_pos_var.set("")

    def _remove_point_load(self) -> None:
        """Remove the load currently selected in the listbox."""
        selection = self.loads_list.curselection()
        if not selection:
            return
        idx = selection[0]
        self.loads_list.delete(idx)
        del self._point_loads[idx]

    # -- Calculate --------------------------------------------------------

    def on_calculate(self) -> None:
        """Handle the Calculate button: run the solver and update plots."""
        try:
            cfg = self._build_config()
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        if not cfg.loads:
            messagebox.showerror(
                "No load applied",
                "Add at least one point load, or enter a non-zero UDL.",
            )
            return

        try:
            x = np.linspace(0.0, cfg.length, self.NUM_X_SAMPLES)
            deflection_m = compute_deflection(cfg, x)
            moment_Nm = compute_bending_moment(cfg, x)
            shear_N = compute_shear_force(cfg, x)
            sigma_max_Pa = compute_max_stress(cfg)
        except ValueError as exc:
            messagebox.showerror("Calculation error", str(exc))
            return

        # Refresh plots.
        self._reset_axes()
        self.ax_def.plot(x, deflection_m * 1e3)       # m -> mm
        self.ax_bmd.plot(x, moment_Nm * 1e-3)          # N·m -> kN·m
        self.ax_bmd.axhline(0.0, color="black", linewidth=0.5)
        self.ax_sfd.plot(x, shear_N * 1e-3)            # N -> kN
        self.ax_sfd.axhline(0.0, color="black", linewidth=0.5)
        self.canvas.draw_idle()

        # Headline numbers.
        max_def_mm = float(np.max(np.abs(deflection_m))) * 1e3
        self.max_def_var.set(f"Max deflection: {max_def_mm:.3f} mm")
        self.max_stress_var.set(f"Max stress: {sigma_max_Pa / 1e6:.2f} MPa")

    def _build_config(self) -> BeamConfig:
        """Assemble a BeamConfig from the current input values."""
        length = _parse_positive(self.length_var.get(), "Beam length")

        material = self.material_var.get()
        if material not in MATERIAL_MODULUS_PA:
            raise ValueError(f"Unknown material: {material!r}.")
        E = MATERIAL_MODULUS_PA[material]

        width = _parse_positive(self.width_var.get(), "Width")
        height = _parse_positive(self.height_var.get(), "Height")

        support_kind = self.support_var.get()
        if support_kind not in SUPPORT_OPTIONS:
            raise ValueError(f"Unknown support: {support_kind!r}.")

        # Point loads (already individually validated when added, but the
        # beam length might have changed since — re-check positions here).
        loads: list[Load] = []
        for mag_kN, pos_m in self._point_loads:
            if not (0.0 <= pos_m <= length):
                raise ValueError(
                    f"Point load at {pos_m} m is outside the beam [0, {length}] m. "
                    "Remove or re-add it after changing the length."
                )
            loads.append(
                Load(
                    LoadType.POINT,
                    magnitude=mag_kN * 1e3,  # kN -> N
                    position=pos_m,
                )
            )

        udl_kNm = _parse_float(self.udl_var.get() or "0", "UDL")
        if udl_kNm != 0.0:
            loads.append(
                Load(
                    LoadType.DISTRIBUTED,
                    magnitude=udl_kNm * 1e3,  # kN/m -> N/m
                    position=0.0,
                    end_position=length,
                )
            )

        moment_of_inertia = compute_second_moment_of_area(width, height)
        return BeamConfig(
            length=length,
            elastic_modulus=E,
            moment_of_inertia=moment_of_inertia,
            width_mm=width,
            height_mm=height,
            loads=loads,
            supports=_supports_for(support_kind, length),
        )


def run() -> None:
    """Create and run the BeamDeflect Tkinter application."""
    app = BeamDeflectApp()
    app.mainloop()


if __name__ == "__main__":
    run()
