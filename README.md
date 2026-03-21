# TabletCAD

TabletCAD is a Dash-based engineering app for **tablet punch geometry calculation** and **2D/3D drawing generation**.

It supports Round, Capsule, and Oval families with multiple cup configurations, bisect options, and reference-style dimensioning inspired by legacy Natoli scripts.

---

## Features

- Interactive tablet design UI with segmented controls for:
  - `Tablet Shape`: Round / Capsule / Oval
  - `Cup Configuration`: CON / COM / CBE / FFRE / FFBE / MOD (profile set is shape-dependent)
- Shape families:
  - Round
  - Capsule (standard + modified)
  - Oval
- Cup profile support:
  - Concave
  - Compound Cup
  - Concave Bevel Edge
  - Flat Face Radius Edge
  - Flat Face Bevel Edge
  - Modified Oval (Oval only)
- Scoring/Bisect modes:
  - None
  - Standard
  - Cut Through
  - Decreasing
  - Optional cruciform and double-sided options (profile-dependent)
- Live calculations panel:
  - Die Hole SA
  - Cup SA
  - Cup Volume
  - Tablet SA
  - Tablet Volume
  - Tablet Weight
  - Tablet Density
  - Tablet SA/V
  - Perimeter
- 2D technical drawing renderer (dimensioned, annotation-based, optional shaded mode)
- 3D Plotly viewer with compact icon toolbar:
  - View presets (Front/Back/Left/Right/Top/Bottom/Isometric)
  - Edge toggle
  - Boundary box toggle
  - Fullscreen
  - Screenshot
- Preset management (SQLite-backed):
  - Load
  - Save
  - Save As
  - Delete
- Constraints Inspector modal (reads from `constraints.csv`)
- Export:
  - PDF specification export
  - STL mesh export
- Multilingual UI:
  - English
  - Russian
  - Chinese
- Constraint-aware UI behavior:
  - Profile-dependent field visibility/editability
  - Runtime clamping/validation of geometric parameters
  - Coupled parameter synchronization in callbacks
- Golden-regression tests vs reference equations

---

## Tech Stack

- Python
- Dash
- dash-bootstrap-components
- Plotly
- NumPy
- Matplotlib (2D rendering backend)
- PyTest (tests)

---

## Runtime File Structure (Actually Used by the App)

```text
tabcad/
├── app.py                              # Entry point, layout wiring, callback registration
├── constraints.csv                     # Data source for Constraints Inspector modal
├── presets.db                          # SQLite presets storage (created/used at runtime)
│
├── assets/
│   ├── apollo_viewer.css               # Global UI styles (sidebar, toolbars, modals)
│   ├── ApolloViewerFonts.ttf           # Icon font for 2D/3D toolbar glyphs
│   └── osifont.ttf                     # PDF-export font resource
│
├── locales/
│   ├── en.json                         # i18n dictionary (EN)
│   ├── ru.json                         # i18n dictionary (RU)
│   └── cn.json                         # i18n dictionary (CN)
│
├── components/
│   ├── sidebar.py                      # Left panel inputs + controls
│   └── viewer.py                       # Calculations, 2D/3D panels, preset modal
│
├── callbacks/
│   ├── ui_updater.py                   # Field visibility/editability + constraints sync
│   ├── graph_updater.py                # Main generation callback (mesh/2D/3D/PDF/STL/metrics)
│   ├── plotly_ui.py                    # 2D/3D viewer toolbar interactions
│   ├── presets.py                      # Preset load/save/save-as/delete callbacks
│   ├── constraints_viewer.py           # Constraints modal open/filter/table callbacks
│   └── i18n_callbacks.py               # Language switching callbacks
│
└── core/
    ├── defaults.py                     # Base/profile/bisect defaults and shape-specific defaults
    ├── db.py                           # SQLite access layer for presets
    ├── i18n.py                         # Translation loader/helper
    ├── engine.py                       # Facade over domain geometry functions
    ├── renderer.py                     # 2D drawing renderer (matplotlib -> image)
    ├── renderer_3d.py                  # 3D renderer (Plotly mesh/scene)
    ├── stl_exporter.py                 # STL export from generated mesh
    ├── pdf_generator.py                # PDF export generator
    └── domain/
        ├── shapes.py                   # Shape geometry helpers
        ├── profiles.py                 # Cup/profile equations
        └── mesh.py                     # Mesh generation + metrics + bisect geometry
```

### Not part of the live runtime path

- `tests/` (test-only)
- `references/` and `core/natoli_forms/` (reference/legacy/parity material)
- `constraints.xlsx` (analytical helper file; runtime viewer reads `constraints.csv`)
- `GEMINI.md`, PDFs in repo root (documentation/reference artifacts)

---

## Installation

> No pinned `requirements.txt` is currently enforced in this branch, so install dependencies manually.

### 1) Create and activate a virtual environment

```bash
python -m venv .venv
```

Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install dash dash-bootstrap-components plotly numpy matplotlib pytest
```

---

## Run the App

```bash
python app.py
```

Default local URL:

- `http://127.0.0.1:8051`

---

## How to Use

1. Select **Tablet Shape**.
2. Select **Cup Configuration**.
3. Set dimensions in the left sidebar.
4. Configure bisect behavior if needed.
5. Click **Generate Drawing**.

The right panel shows:

- **2D drawing** (technical views + dimensions)
- **3D model** (interactive Plotly view)
- Calculated metrics panel

---

## 3D Toolbar

Current 3D toolbar includes:

- **View** dropdown (Front/Back/Left/Right/Top/Bottom/Isometric)
- **Edge** toggle
- **Boundary Box** toggle
- **Full screen**
- **Screenshot**

The 3D model is centered with unified framing logic across views.

---

## 2D Toolbar

Current 2D toolbar includes:

- **Shaded** toggle
- **Full screen**
- **Screenshot**

---

## Validation & Constraints

The UI enforces profile- and shape-dependent rules, including:

- Editable/non-editable field states by configuration
- Non-negative and minimum limits for geometric inputs
- Cup depth / radius coupled constraints in specific modes
- Additional tangent/ref-flat style limits for bevel/flat-face variants

Most logic lives in:

- `callbacks/ui_updater.py`

---

## Tests

Run all tests:

```bash
pytest -q
```

Golden regression test:

- `tests/test_golden_regression.py`

It compares domain metrics against reference outputs from `core/reference_bridge.py` across representative shape/profile cases with per-case tolerances.

---

## Branching Strategy

Typical workflow:

- `main`: stable baseline
- `exp/geometry-3d`: active geometry/3D experimentation

Recommended:

1. Create feature branch from active branch
2. Commit small logical units
3. Push and open PR
4. Merge after verification

---

## Troubleshooting

### UI changes not visible

- Restart app
- Hard refresh browser: `Ctrl+F5`

### Static assets (icons/CSS) not updating

- Confirm files are in `assets/`
- Hard refresh to clear browser cache

### Dropdown/overlay clipping issues

- Check `z-index` and `overflow` styles in `components/viewer.py` and `assets/apollo_viewer.css`

---

## Preset Naming and Saving Logic

The preset system automatically generates names based on the tablet's physical dimensions and features to ensure consistency.

- **Naming Convention:** `TAB - [W]x[L] - [Tt] - [ProfileCode] - [ScoringCode] - [Suffix]`
  - Example: `TAB-8x16-4,4-O-CON-00`
- **Suffix Numbering:** Every preset name ends with a two-digit suffix (starting from `-00`). 
  - When you click **Save As**, the system checks the database for existing presets with the same base name.
  - If a preset with identical parameters exists, it will use its name.
  - If parameters differ, it automatically finds the highest existing suffix and increments it (e.g., `-01`, `-02`), ensuring you never accidentally overwrite an existing preset even if the core dimensions are identical.
- **Save vs. Save As:**
  - **Save As:** Generates a unique name with a numeric suffix to prevent collision.
  - **Save:** Overwrites the *currently loaded* preset without changing its name or suffix, allowing for iterative edits.

---

## Notes

- **Defaults & Params Flow (Single Source of Truth)**  
  Defaults live only in `core/defaults.py` and are applied in UI/Callbacks. Runtime geometry/render/PDF/STL expects a full `params` dict and fails fast if a required key is missing.
  Flow:
  1. `components/sidebar.py` sets initial input values from `core/defaults.py`
  2. `callbacks/ui_updater.py` adjusts inputs (still using `core/defaults.py`)
  3. `callbacks/graph_updater.py::_build_params` assembles the final `params` (fills `None` from `core/defaults.py`)
  4. `core/domain/*`, `core/renderer*.py`, `core/pdf_generator.py`, `core/stl_exporter.py` consume `params` with **no internal defaults**

- **Constraints file (reference helper)**  
  There is a constraints file used mainly as a reference to visualize parameter limits and relationships. It is only lightly integrated (the constraints viewer is hooked into the UI), and the file itself exists primarily for human inspection due to the complexity/volume of constraints.

- Some legacy/reference files are intentionally kept for parity and auditability.
- Architecture goal is domain-first single-runtime path after complete parity and regression confidence.

---

## License

License is not defined yet in this repository.
Add a `LICENSE` file before external distribution.

