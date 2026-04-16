# TabletCAD

TabletCAD is a Dash-based engineering app for **tablet punch geometry calculation** and **2D/3D drawing generation**.

It supports Round, Capsule, and Oval families with multiple cup configurations, bisect options, and reference-style dimensioning.

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


---

## TODO / Roadmap

### Priority 1: Critical Improvements

#### 1.1 Visual Validation Feedback
- [ ] Red border highlight for constraint violations in input fields
- [ ] Tooltip/popover with violation reason on hover
- [ ] Visual indicator for auto-corrected values (e.g., yellow flash)
- [ ] Real-time constraint summary panel

#### 1.2 History and Undo/Redo
- [ ] Undo/Redo functionality (Ctrl+Z / Ctrl+Y)
- [ ] Session history stored in localStorage
- [ ] Auto-save every 30 seconds
- [ ] "Restore last session" on page load

---

### Priority 2: Feature Extensions

#### 2.1 Material Library
- [ ] Material database (Mannitol, Lactose, MCC, etc.)
- [ ] Custom material creation
- [ ] Auto-fill density from selected material
- [ ] Material-specific validation rules

#### 2.2 Multi-Tablet Design
- [ ] Multiple tablets in single project
- [ ] Side-by-side parameter comparison
- [ ] Batch PDF export
- [ ] Tablet set management (blister pack design)

#### 2.3 Tooling Constraints
- [ ] Press parameters input (max force, turret speed)
- [ ] Tooling type selection (D-tool / B-tool)
- [ ] Compression force validation
- [ ] Tool hardness recommendations

#### 2.4 CAD/CAM Integration
- [ ] STEP/IGES export
- [ ] DXF/DWG export for AutoCAD
- [ ] JSON export/import for system integration
- [ ] Excel/CSV parameter import

---

### Priority 3: Analytics & Reporting

#### 3.1 Comparative Analysis
- [ ] Compare multiple designs side-by-side
- [ ] Delta percentage calculation
- [ ] Export comparison report

#### 3.2 Geometry Optimization
- [ ] Target function definition (min SA/V, max cup volume, etc.)
- [ ] Automatic parameter optimization
- [ ] Constraint-aware optimization bounds

#### 3.3 Enhanced Documentation
- [ ] Multi-page PDF reports
- [ ] Revision history table
- [ ] Electronic signature support
- [ ] QR code with parameters

---

### Priority 4: UX/UI Improvements

#### 4.1 Visual Enhancements
- [ ] Dark theme
- [ ] Customizable 3D model colors
- [ ] Smooth view transition animations
- [ ] Interactive tooltips on geometry hover

#### 4.2 Keyboard Shortcuts
```
Ctrl+G    — Generate Drawing
Ctrl+S    — Save Preset
Ctrl+E    — Export PDF
Ctrl+Z    — Undo
Ctrl+Y    — Redo
1-8       — Switch 3D View Preset
```

#### 4.3 Mobile Support
- [ ] Responsive design for tablets
- [ ] Touch-friendly controls
- [ ] Simplified mobile interface

---

### Priority 5: Enterprise Features

#### 5.1 Multi-User Support
- [ ] User authentication
- [ ] Shared preset libraries
- [ ] Role-based access control

#### 5.2 API Integration
```python
# REST API endpoints
POST /api/tablet/generate
GET  /api/tablet/export/pdf
GET  /api/tablet/export/stl
```

#### 5.3 LIMS/ERP Integration
- [ ] Export to laboratory systems
- [ ] SAP/Oracle integration
- [ ] CLI batch processing mode

---

### Performance Optimization

- [ ] Adaptive mesh resolution for PDF export (lower mesh_n)
- [ ] Reduced 3D surface points for PDF (lower theta/rr)
- [ ] Numba JIT compilation for profile calculations
- [ ] Contour caching for unchanged shapes

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
    ├── preset_naming.py                # Shared preset and PDF drawing-number naming helper
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

## PDF 2D Scale Logic

PDF export uses a fixed 2D drawing window (depends on orientation in `core/pdf_generator.py`).

- Scale is chosen automatically from ISO factors: `10, 5, 4, 2.5, 2, 1, 0.5, 0.4, 0.25, 0.2, 0.1`
- The selected factor is the largest one that fits both width and height into the target window
- Fitting uses annotated bounds from the 2D renderer (geometry + dimension texts), not the full canvas frame
- The drawing is clipped to the window rectangle to keep layout stable
- Title block `Scale` is formatted as `N:1` for enlargements and `1:N` for reductions

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

- Architecture goal is domain-first single-runtime path.

---

## PDF Dimension System Change Log (From `c739482`)

This section documents critical in-progress changes made after commit `c739482`
(`feat: improve 3D settings UI with realtime input syncing, dynamic PDF quality`).

### Files changed

- `callbacks/graph_updater.py`
- `core/renderer.py`

### Scope summary

- Extended PDF 2D scale solver in `graph_updater`:
  - `_pick_iso_scale_from_bounds(...)` now accepts geometry size (`geom_w/geom_h`) and current scale.
  - Added geometry/padding split to estimate printable fit:
    `new_phys = geom * scale + padding`.
  - Reworked stabilization loop from 2-pass to iterative (up to 5 passes) with checks for:
    - scale convergence
    - `view_w` convergence
  - Persists final render scale into `_render_2d_scale_ratio`.

- Reworked ISO PDF dimension styling/calibration in `renderer`:
  - Base style constants updated:
    - thinner line defaults
    - larger outside tails
    - added `pointer_shelf_length`
  - Added globals: `POINTER_SHELF_LENGTH`, `PDF_SCALE_RATIO`.
  - `_dim_text_kwargs()` split by mode (web vs pdf behavior).
  - `draw_ext`, `draw_ext_outside`, `draw_pointer` now apply PDF offset normalization.
  - Pointer shelf length switched from fixed literal to configurable global.

- Added dynamic “paper-constant” scaling in `render_tablet(...)` PDF path:
  - dimension font size uses `pdf_2d_dim_font_size`, `view_w`, and `pdf_scale_ratio`
  - line widths dynamically normalized to page result
  - overrun/tails/text gaps normalized by scale
  - arrows normalized to physical-size targets

- Updated view spacing logic in PDF mode:
  - side/front view gap now uses scale-aware formula in PDF mode
  - web mode keeps original spacing.

- CBE-specific dimension edits:
  - introduced separate `cup_depth_dy` / `bevel_depth_dy`
  - CBE PDF branch currently applies additional vertical offsets for these dimensions.

- CBE/FFBE angle dimension tuning:
  - PDF branch uses custom `ext_len` floor and divisor
  - PDF branch uses enlarged angle arc radius and text offset.

### Notes

- These changes are intentionally tracked as a dedicated engineering checkpoint because PDF
  print readability and dimension placement were tuned iteratively over a long cycle.

---

## License

License is not defined yet in this repository.
Add a `LICENSE` file before external distribution.
