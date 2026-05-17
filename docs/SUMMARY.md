# BeamDeflect — Project Summary

**Repository:** https://github.com/sdrummond-eng/BeamDeflect  
**Status:** Complete — v0.1 shipped  
**Built:** Weekend project (1 day, May 2026)  
**Stack:** Python 3.14, Tkinter, NumPy, SciPy, Matplotlib  

---

## What it does

BeamDeflect is an open source desktop GUI for mechanical engineering students. Given a rectangular beam's geometry, material, support conditions, and loading, it instantly plots the deflection curve, bending moment diagram (BMD), and shear force diagram (SFD), and displays maximum deflection and bending stress. All underlying equations are cited to Roark's Formulas for Stress and Strain (Young & Budynas, 7th ed.) with inline code references.

---

## How to run it

```bash
# Fedora
sudo dnf install python3-tkinter python3-pillow-tk
pip install -r requirements.txt
python main.py

# Debian/Ubuntu
sudo apt install python3-tk
pip install -r requirements.txt
python main.py
```

---

## Project structure

```
BeamDeflect/
├── main.py                  # Entry point — calls gui.app.run()
├── beam/
│   ├── models.py            # BeamConfig, Load, LoadType, SupportCondition, SupportType
│   └── calculator.py        # Pure calculation functions (no GUI), all cited to Roark's
├── gui/
│   └── app.py               # Tkinter GUI — BeamDeflectApp(tk.Tk)
├── tests/
│   └── test_calculator.py   # 5 unit tests, all passing
├── docs/
│   └── screenshots/
│       └── ss_point_load.png
├── requirements.txt         # numpy, scipy, matplotlib, pytest
├── README.md
└── LICENSE                  # MIT, 2026 BeamDeflect Contributors
```

---

## Capabilities

**Support conditions:** Simply supported, cantilever (fixed end at x=0), fixed-fixed

**Load types:** Single or multiple point loads (kN + position), uniform distributed load (kN/m, full span)

**Materials:** Steel (E=200 GPa), Aluminium (E=69 GPa), Timber (E=11 GPa)

**Outputs:** Deflection curve (mm), BMD (kNm), SFD (kN), max deflection (mm), max bending stress (MPa)

---

## Verified reference cases

All cases matched closed-form formulas exactly (within integration tolerance of rel=1e-3):

| Case | Formula | Result |
|---|---|---|
| SS + central point load | δ = PL³/48EI | 1.953 mm |
| SS + full UDL | δ = 5wL⁴/384EI | 1.221 mm |
| Cantilever + end point load | δ = PL³/3EI | 8.00 mm |
| Cantilever + UDL | δ = wL⁴/8EI | 12.0 mm |
| Fixed-fixed + UDL | δ = wL⁴/384EI | 0.250 mm |
| Fixed-fixed + central point load | δ = PL³/192EI | 0.250 mm |
| Max bending stress | σ = Mc/I | 18.75 MPa |
| Second moment of area | I = bh³/12 | 6.667×10⁻⁵ m⁴ |

---

## Key technical decisions

**Tests use formula-derived expected values** rather than hardcoded numbers — e.g. `P*L**3 / (48*E*I)`. This keeps tests traceable and avoids arithmetic errors in the prompt.

**Cantilever constraint:** Fixed end must be at x=0. Fixed end at x=L raises a clear error rather than producing silently wrong sign conventions.

**Deflection axis inverted** in the GUI so the curve visually dips downward, matching Roark's downward-positive δ convention.

**UDL UI limited to full span** — the engine supports partial and multiple UDLs, so extending the UI is a small future change.

**Unit conversions in GUI:** kN→N, kN/m→N/m, mm→m for second moment of area, Pa→MPa for stress display.

---

## Known Fedora-specific issues

- `python3-tkinter` must be installed separately: `sudo dnf install python3-tkinter`
- System Pillow (12.2.0) missing `ImageTk`: `sudo dnf install python3-pillow-tk`
- `gnome-screenshot` needed for Wayland screenshots: `sudo dnf install gnome-screenshot`
- Claude Code sandbox blocks outbound HTTPS — `git push` and `gh repo create` required explicit permission prompt to disable sandbox for that command

---

## Security setup

- Global `~/.claude/settings.json` denies: curl, wget, ssh, scp, nc, nmap, WebFetch, and read access to ~/.ssh, ~/.gnupg, Bitwarden config, finance pipeline, .bashrc, .bash_history
- Project `BeamDeflect/.claude/settings.json` allows edits only to beam/, gui/, tests/, main.py, requirements.txt, README.md
- Claude Code `/sandbox` enabled with bubblewrap (bwrap) — Fedora package: `sudo dnf install bubblewrap socat`

---

## Future enhancements (from scope)

- Additional cross-section profiles (I-beam, T-beam, circular)
- Varying distributed loads (triangular, trapezoidal)
- Custom material input (user-defined E, ρ)
- Export charts as PNG/PDF
- Unit system toggle (SI / Imperial)
- Partial and multiple UDL support in the GUI
- Mid-span point support

---

## How this was built

Scoped and built using Claude (claude.ai) for planning and Claude Code for implementation across one weekend. Prompts were sequenced: scaffold → calculation engine → test verification → GUI → README/release. The calculation engine was verified against 8 reference cases before any GUI work began, retiring the math accuracy risk early.

**Claude Code prompts used:** 5 (scaffold, engine, tests, GUI, README)  
**Tests:** 5 unit tests, all passing  
**Commits:** 3 (initial scaffold, screenshot, docs)
