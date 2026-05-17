# BeamDeflect

BeamDeflect is a small desktop application that computes and visualises the
deflection, bending moment, and shear force of a prismatic beam under
user-defined loads and supports. It is aimed at structural and mechanical
engineering students, junior practitioners, and educators who want a quick,
verifiable sanity check on a beam problem without firing up a full FEA
package — enter the geometry, section, material, supports, and loads in a
Tkinter form, click **Calculate**, and read the diagrams and headline
numbers off the right-hand panel.

## Prerequisites

- Python **3.10+**
- Install the Python dependencies:
  ```bash
  pip install -r requirements.txt
  ```
- On **Fedora Linux**, install the system Tk packages that ship Tkinter and
  its image support (these are not pip-installable):
  ```bash
  sudo dnf install python3-tkinter python3-pillow-tk
  ```
  On other distributions the equivalent packages are typically
  `python3-tk` (Debian/Ubuntu), `tk` (Arch), or `python-tk` (macOS Homebrew).
  Tkinter is bundled with the official python.org installers on Windows
  and macOS.

## How to run

From the project root:

```bash
python main.py
```

## Features

### Supported beam configurations

| Configuration       | Left support | Right support |
| ------------------- | ------------ | ------------- |
| Simply supported    | Pinned       | Roller        |
| Cantilever          | Fixed        | (free end)    |
| Fixed-fixed         | Fixed        | Fixed         |

### Supported load types

- **Point loads** — any number, applied at any position along the beam
  (magnitude in kN, position in m).
- **Uniformly distributed load (UDL)** — a single full-span UDL
  (intensity in kN/m).

### Outputs

For every Calculate run, the right-hand panel shows:

- **Deflection curve** δ(x) in millimetres (downward-positive, plotted so
  the curve visually dips below the axis).
- **Bending moment diagram (BMD)** M(x) in kN·m (sagging-positive).
- **Shear force diagram (SFD)** V(x) in kN.
- **Maximum deflection** in mm.
- **Maximum bending stress** σ<sub>max</sub> = M<sub>max</sub>·c / I in MPa,
  with c = h/2 for the rectangular section.

## Verification & references

All closed-form beam formulas used by the engine — reactions, shear,
bending moment, and deflection — are sourced from:

> Young, W. C. & Budynas, R. G., *Roark's Formulas for Stress and Strain*,
> 7th ed., McGraw-Hill, 2002.

Every formula in `beam/calculator.py` carries an inline comment citing
the specific Roark table or equation it implements (for example
`# Roark Table 8.1, Case 1e (simply supported, intermediate concentrated load)`),
so any computed result can be independently verified against the published
handbook. The test suite in `tests/test_calculator.py` re-evaluates those
same formulas symbolically and asserts that the engine matches them within
tight tolerance.

## Screenshots

_Screenshots coming soon._

## Running the tests

```bash
pip install pytest
python -m pytest
```

## Contributing

Issues and pull requests are welcome via GitHub. Please open an issue first
for anything larger than a small bug fix or doc change so we can discuss the
direction before you sink time into a patch.

## License

Released under the MIT License — see [LICENSE](LICENSE).
