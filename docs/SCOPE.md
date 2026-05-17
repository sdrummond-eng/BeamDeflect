# BeamDeflect — Project Scope Document

---

## 1. Project Identity

| Field | Details |
|---|---|
| **Project name** | BeamDeflect |
| **Owner** | Solo developer |
| **Priority** | Personal learning + open source release |
| **Timeline** | Weekend (2 days) |
| **Repository** | GitHub (public, open source) |

---

## 2. Problem Statement

**Current state:** The developer has prior mechanical engineering knowledge but hasn't actively applied beam theory recently. No dedicated tool exists for quick, intuitive beam behaviour exploration at the student level.

**Pain points:**
- Manual hand calculations are tedious and don't build visual intuition
- Existing tools (spreadsheets, commercial software) are either clunky or opaque
- Hard to rapidly explore "what if" scenarios for different loading and support conditions

**Desired future state:** An intuitive, open source Python desktop app where a student inputs beam and load parameters and immediately sees deflection, stress, and internal force diagrams — building genuine physical intuition through visual feedback.

---

## 3. Objectives & Success Metrics

**Primary objective:** A working GUI application where a user can define a simply-supported, cantilever, or fixed-fixed rectangular beam with point and/or distributed loads and instantly view accurate engineering output charts.

| KPI | Target |
|---|---|
| Deflection curve renders correctly | Passes against known textbook cases |
| Bending moment diagram correct | Passes against known textbook cases |
| Shear force diagram correct | Passes against known textbook cases |
| Max deflection value displayed | Numerically correct to 3 significant figures |
| Max stress value displayed | Numerically correct to 3 significant figures |
| App launches and runs without error | 100% on a clean Python install |
| Error handling covers bad inputs | All edge cases show clear user-facing messages |

---

## 4. Scope Definition

**In scope:**
- Rectangular cross-section beams only
- Three support conditions: simply supported, cantilever, fixed-fixed
- Optional mid-span point support
- Loading types: single or multiple point loads, uniform distributed load (UDL)
- Output charts: deflection curve, bending moment diagram (BMD), shear force diagram (SFD)
- Output values: maximum deflection, maximum bending stress
- Simple Tkinter GUI for all inputs and chart display
- Error handling for invalid inputs (negative dimensions, zero length, unsupported combos)
- GitHub repository with README and usage instructions

**Out of scope:**
- Non-rectangular cross-sections (I-beam, T-beam, circular)
- Dynamic/moving loads
- Buckling or fatigue analysis
- 2D/3D frame analysis
- FEA or finite element methods
- Web or mobile deployment
- Multiple simultaneous beam comparisons

**Future considerations:**
- Additional cross-section profiles
- Varying distributed loads (triangular, trapezoidal)
- Material custom input (user-defined E, ρ)
- Export charts as PNG/PDF
- Unit system toggle (SI / Imperial)

---

## 5. Team & Stakeholders

| Role | Person | Responsibility |
|---|---|---|
| Developer | Solo | All design, coding, testing, and documentation |
| AI coding assistant | Claude Code | Code generation, debugging, refactoring guidance |
| End users | ME students (open source) | Feedback via GitHub issues post-release |

---

## 6. Technical Context

**Tech stack:**

| Component | Technology | Notes |
|---|---|---|
| Language | Python 3.10+ | Standard install |
| GUI framework | Tkinter | Built into Python, no extra install |
| Numerical computation | NumPy | Beam equation discretisation |
| Scientific functions | SciPy | Integration, boundary value solving if needed |
| Charting | Matplotlib (embedded in Tkinter) | FigureCanvasTkAgg for in-app display |
| Version control | Git + GitHub | Public open source repo |
| AI coding tool | Claude Code | Primary development assistant |

**Mathematical foundation:**
All beam equations sourced from standard structural mechanics references (e.g. Roark's Formulas for Stress and Strain, or equivalent). Each formula should be commented in code with its source equation reference so users can verify independently.

---

## 7. Functional Requirements

| ID | Description | Priority | Acceptance criteria |
|---|---|---|---|
| FR-01 | User can input beam length (m) | Must have | Input field validates positive numeric value |
| FR-02 | User can select material from dropdown (Steel, Aluminium, Timber) | Must have | E value auto-populates based on selection |
| FR-03 | User can input cross-section width and height (mm) | Must have | Validates positive numeric, computes I automatically |
| FR-04 | User can select support condition (simply supported, cantilever, fixed-fixed) | Must have | Dropdown updates valid load options accordingly |
| FR-05 | User can add a mid-span point support | Should have | Checkbox enables/disables; updates reaction calculation |
| FR-06 | User can add one or more point loads (magnitude + position) | Must have | Validates position is within beam length |
| FR-07 | User can add a uniform distributed load (magnitude over full span) | Must have | Input field with kN/m units |
| FR-08 | App computes and displays deflection curve chart | Must have | Matches textbook result for at least 2 reference cases |
| FR-09 | App computes and displays bending moment diagram | Must have | Matches textbook reference case |
| FR-10 | App computes and displays shear force diagram | Must have | Matches textbook reference case |
| FR-11 | App displays max deflection value (mm) and location | Must have | Correct to 3 sig. figures |
| FR-12 | App displays max bending stress (MPa) | Must have | Correct to 3 sig. figures |
| FR-13 | All input errors show clear, non-crashing messages | Must have | No unhandled exceptions reach the user |
| FR-14 | Charts update on button press without restarting app | Must have | Re-renders in under 2 seconds |

---

## 8. Risks & Timeline

**Milestones:**

| Day | Milestone | Goal |
|---|---|---|
| ✅ Saturday AM | Project setup | Repo created, dependencies installed, folder structure scaffolded via Claude Code |
| ✅ Saturday PM | Core calculation engine | Beam equations implemented in Python, verified against 2 textbook reference cases |
| ✅ Sunday AM | GUI shell + chart display | Tkinter layout built, matplotlib embedded, charts rendering from hardcoded test inputs |
| ✅ Sunday PM | Wire GUI to engine + polish | Live inputs drive charts, error handling complete, README written, pushed to GitHub |

**Risks:**

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Beam equations implemented incorrectly | Medium | High | Source all formulas from Roark's or equivalent; add inline equation references; verify against at least 2 known textbook cases before building GUI |
| Tkinter layout takes too long | Low | Medium | Use a simple grid layout; Claude Code can scaffold the boilerplate quickly |
| Claude Code output is too complex to understand | Low | Medium | Ask Claude Code to add comments and explain each function; keep modules small |
| Mid-span support complicates solver | Medium | Medium | Descope to optional stretch goal if it blocks Saturday progress |

---

## 9. Pre-Implementation Testing

**Checklist:**
- [x] Identify 2–3 textbook reference cases with known solutions (e.g. simply supported beam, central point load)
- [x] Document expected deflection, BMD, SFD values for each reference case before writing code
- [x] Confirm NumPy/SciPy/Matplotlib install correctly on dev machine
- [x] Agree on folder structure and module names before starting

**Entry criteria:** Reference cases documented, environment working
**Exit criteria:** Calculation engine matches all reference cases within 1% before GUI work begins

---

## 10. Post-Implementation Testing

**Immediate checks:**
- [x] App launches on a clean Python environment
- [x] All three support conditions produce plausible output
- [x] Point load and UDL both render without errors
- [x] Invalid inputs (letters, negatives, zero length) show error messages, don't crash
- [x] Charts are clearly labelled with axes, units, and title

**KPI validation:**

| KPI | Test method | Pass threshold |
|---|---|---|
| Deflection curve accuracy | Compare to textbook reference case | Within 1% of known value |
| BMD accuracy | Compare to textbook reference case | Within 1% of known value |
| SFD accuracy | Compare to textbook reference case | Within 1% of known value |
| Max deflection display | Manual check against reference | Correct to 3 sig. figures |
| Error handling | Enter 10 invalid input combinations | Zero unhandled exceptions |

---

## 11. Definition of Done

- [x] All FR-01 through FR-14 requirements implemented and passing
- [x] Calculation engine verified against minimum 2 textbook reference cases
- [x] All beam equations commented with source reference in code
- [x] GUI runs without error on a clean Python 3.10+ install
- [x] GitHub repo is public with a README covering: what it does, how to install, how to run, and example screenshots
- [x] No unhandled exceptions for any tested input combination

---

## 12. Claude Code starter prompts

Paste these into Claude Code in order to get started:

**1. Scaffold the project**
```
Create a Python project called BeamDeflect with the following folder structure:
- main.py (entry point)
- beam/calculator.py (pure calculation functions, no GUI)
- beam/models.py (dataclasses for BeamConfig, Load, SupportCondition)
- gui/app.py (Tkinter GUI)
- tests/test_calculator.py (unit tests)
- README.md
Add a requirements.txt with numpy, scipy, and matplotlib. Do not write any logic yet — just the files, folder structure, and empty stubs with docstrings.
```

**2. Implement the calculation engine**
```
In beam/calculator.py, implement the following functions for a rectangular cross-section beam:
- compute_second_moment_of_area(width_mm, height_mm) -> float
- compute_reactions(beam_config) for simply supported, cantilever, and fixed-fixed conditions
- compute_shear_force(beam_config, x_positions) -> np.ndarray
- compute_bending_moment(beam_config, x_positions) -> np.ndarray
- compute_deflection(beam_config, x_positions) -> np.ndarray
- compute_max_stress(beam_config) -> float

Support point loads and uniform distributed loads. Comment every formula with its source equation (e.g. "Roark's Table 8.1, Case 2"). Use dataclasses from beam/models.py for inputs.
```

**3. Verify against a reference case**
```
In tests/test_calculator.py, write a unit test that verifies the calculation engine against this known textbook case:
- Simply supported beam, length 5m, Steel (E=200 GPa), rectangular section 100mm wide x 200mm deep
- Single central point load of 10 kN
- Expected max deflection: 1.302 mm (from standard formula δ = PL³/48EI)
- Expected max bending moment: 12.5 kNm
Run the tests and fix any failures before proceeding.
```

**4. Build the Tkinter GUI**
```
In gui/app.py, build a Tkinter GUI for BeamDeflect with:
- Input panel (left side): fields for beam length (m), material dropdown (Steel/Aluminium/Timber), width (mm), height (mm), support condition dropdown (Simply Supported/Cantilever/Fixed-Fixed), point load inputs (magnitude kN + position m, with Add button for multiple), UDL input (kN/m)
- A Calculate button that calls the beam/calculator.py functions
- Output panel (right side): embedded matplotlib figure with 3 subplots — deflection curve, BMD, SFD — plus text labels for max deflection and max stress
- Clear error messages via messagebox for invalid inputs (non-numeric, out of range, zero/negative dimensions)
Keep the layout simple: grid-based, no decorative styling needed.
```

**5. Prepare for GitHub release**
```
Write a README.md for BeamDeflect that includes:
- One-paragraph description of what the app does and who it's for
- Requirements (Python 3.10+, pip install -r requirements.txt)
- How to run (python main.py)
- A description of the supported beam types, load types, and outputs
- A note that all beam equations are sourced from standard structural mechanics references with inline code comments
- Placeholder section for screenshots (I'll add these manually)
Also add a MIT licence file.
```

---

## 13. Progress notes

**Scaffold complete**
- Full folder structure in place at `/home/sam/projects/BeamDeflect/`
- Claude Code added `LoadType` and `SupportType` enums and concrete dataclass fields to `models.py` — kept as-is, good foundation for Prompt 2
- `__init__.py` files added to all packages — correct practice, no changes needed
- Stubs use `...` bodies rather than `pass` — better for type checking, kept as-is
- `requirements.txt` includes numpy, scipy, matplotlib
- Security: bubblewrap sandbox enabled, project-level `settings.json` in place alongside global deny rules

**Calculation engine complete — all 8 reference cases passed**
- `beam/calculator.py` fully implemented with 6 functions, all citing Roark's Formulas for Stress and Strain
- Reference cases verified exact: SS + centre point load, SS + UDL, cantilever + end point load, cantilever + UDL, fixed-fixed + UDL, fixed-fixed + centre point load, second moment of area, max stress
- `beam/models.py` extended with `width_mm`, `height_mm`, `loads`, and `supports` fields on `BeamConfig`
- Moment loads (LoadType.MOMENT) added opportunistically — can be removed later if surface area reduction desired
- Cantilever constraint: fixed end must be at x=0; x=L raises a clear error rather than silently wrong output
- Pre-implementation exit criteria met: all reference cases within 1% (exact match) ✅
- `tests/test_calculator.py` stubs need updating to use new function signatures before Prompt 3

**Tests complete — all 5 passing**
- 5 tests covering: SS centre point load deflection + moment, cantilever tip deflection + wall moment + reactions, shear distribution, moment distribution (1001-point grid), reactions balance for all 3 support conditions
- Tests compute expected δ from formulas in-test (e.g. `P*L**3/(48*E*I)`) rather than hardcoded values — correct approach for traceability
- Prompt 3 had arithmetic errors in expected deflection values (1.302/1.628/16.0 mm were wrong); engine and tests are correct
- Actual values: SS centre load δ = 1.953 mm, SS UDL δ = 1.221 mm, cantilever tip δ = 8.00 mm
- Moment values from prompt were correct: SS M_max = 12.5 kNm, cantilever M_wall = -20 kNm
- pytest added to requirements.txt

**GUI complete — end-to-end validated**
- `gui/app.py` built: left input panel (length, material, width, height, support, point loads listbox, UDL) + right output panel (3 matplotlib subplots: δ, M, V + max deflection and max stress labels)
- End-to-end validation: SS + central 10 kN → 1.953 mm / 12.50 kNm / 18.75 MPa — matches engine benchmarks exactly
- Unit conversions confirmed correct: kN→N, kN/m→N/m, mm→m for I, Pa→MPa for display
- Error handling covers: empty fields, non-numeric, inf/nan, out-of-range, non-positive dimensions, point load outside beam length
- Deflection axis inverted so curve visually dips downward (matching Roark downward-positive convention)
- Materials: Steel 200 GPa, Aluminium 69 GPa, Timber 11 GPa
- `main.py` stub needs one-line wire-up: `from gui.app import run; run()`
- Fedora requires `sudo dnf install python3-tkinter` — to be noted in README
- Only full-span UDL supported in UI (engine supports partial UDLs — future enhancement)

**Live GUI validated — all outputs correct**
- Test case: SS beam, 5m, Steel, 100×200mm, 10 kN central point load
- Max deflection: 1.953 mm ✅ | Max stress: 18.75 MPa ✅
- Deflection curve: smooth symmetric arc, pins at both ends ✅
- BMD: clean triangle peaking at 12.5 kNm at midspan ✅
- SFD: +5 kN / -5 kN step at midspan ✅
- Fix required: `sudo dnf install python3-pillow-tk` on Fedora (system Pillow missing ImageTk)
- All 4 weekend milestones complete ✅

**Project shipped — BeamDeflect v0.1**
- Repository live at https://github.com/sdrummond-eng/BeamDeflect
- 12 files, 1474 insertions, initial commit 36f1f19
- Re-authentication required for gh CLI (stored token was invalid) — resolved via `gh auth login`
- First push attempt failed due to sandbox network block; retried with explicit permission prompt — no silent bypass
- Pending: add repo description and topics on github.com, tag v0.1 release, add screenshots to README

**Project complete — screenshot added, README final**
- Screenshot committed at `docs/screenshots/ss_point_load.png`, commit 2459402
- README renders screenshot inline on github.com under Screenshots heading
- Co-authored-by trailer added by Claude Code harness on commits — amend with `git commit --amend` if clean history preferred
- Repository live at https://github.com/sdrummond-eng/BeamDeflect
- Still to do (optional): tag v0.1 release, add GitHub repo description and topics
- Pre-implementation exit criteria fully met ✅
