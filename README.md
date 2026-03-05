# TabletCAD

TabletCAD is a Dash-based engineering app for **tablet punch geometry calculation** and **2D/3D drawing generation**.

It supports Round, Capsule, and Oval families with multiple cup configurations, bisect options, and reference-style dimensioning inspired by legacy Natoli scripts.

---

## Features

- Interactive parameter-driven tablet design UI
- 2D technical drawing generation (dimensions + annotations)
- 3D Plotly model viewer with compact icon toolbar
- Shape families:
  - Round
  - Capsule (standard + modified)
  - Oval
- Cup profiles:
  - Concave
  - Compound Cup
  - Concave Bevel Edge
  - Flat Face Radius Edge
  - Flat Face Bevel Edge
  - Modified Oval (for Oval family)
- Bisect modes:
  - None
  - Standard
  - Cut Through
  - Decreasing
  - Optional cruciform / double-sided behavior (where applicable)
- Derived metrics:
  - Die Hole SA
  - Cup Volume
  - Cup SA
  - Perimeter
  - Tablet SA
  - Tablet Volume
- UI logic with geometric constraints and profile-dependent editability
- Golden-regression tests comparing domain outputs vs reference formulas

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

## Project Structure

```text
tabcad/
├─ app.py                      # Dash app entry point
├─ assets/                     # Static assets (CSS, icon font)
├─ callbacks/
│  ├─ graph_updater.py         # Main generation callback (2D + 3D + metrics)
│  ├─ ui_updater.py            # Dynamic UI visibility + constraints + sync logic
│  └─ plotly_ui.py             # Client/UI callbacks (fullscreen, screenshot, toolbar state)
├─ components/
│  ├─ sidebar.py               # Input controls panel
│  └─ viewer.py                # 2D/3D view layout
├─ core/
│  ├─ ARCHITECTURE.md          # Domain-first architecture notes
│  ├─ engine.py                # Domain facade used by callbacks/renderers
│  ├─ renderer.py              # 2D drawing renderer
│  ├─ renderer_3d.py           # 3D Plotly renderer
│  ├─ reference_bridge.py      # Bridge to reference forms (for parity/testing)
│  ├─ domain/
│  │  ├─ shapes.py             # Shape normalization + geometry helpers
│  │  ├─ profiles.py           # Pure cup profile equations
│  │  └─ mesh.py               # Mesh generation + bisect + metrics
│  └─ natoli_forms/            # Integrated reference form logic/assets
├─ references/                 # Legacy/reference source files
└─ tests/
   └─ test_golden_regression.py
```

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

## Notes

- Some legacy/reference files are intentionally kept for parity and auditability.
- Architecture goal is domain-first single-runtime path after complete parity and regression confidence.

---

## License

License is not defined yet in this repository.
Add a `LICENSE` file before external distribution.

