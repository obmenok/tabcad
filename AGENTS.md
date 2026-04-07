# AGENTS.md — Context for AI Assistants

This document provides essential context for any AI model working on the **TabletCAD** project. Read this file first before making any code changes.

---

## Project Overview

**TabletCAD** is a Dash-based engineering application for calculating tablet punch geometry and generating 2D/3D technical drawings. It is used by pharmaceutical engineers to design tablet tooling.

### Target Users
- Pharmaceutical formulation scientists
- Tablet tooling engineers
- Quality assurance specialists

### Core Workflow
```
User Input (Dimensions) → Geometry Calculation → 2D Drawing + 3D Model → Export (PDF/STL)
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.x |
| Frontend | Dash, dash-bootstrap-components |
| 3D Visualization | Plotly |
| 2D Rendering | Matplotlib |
| Numerical Computing | NumPy |
| PDF Export | reportlab |
| Database | SQLite (presets) |
| Testing | PyTest |

---

## File Structure

```
tabcad/
├── app.py                    # Entry point, layout wiring
├── constraints.csv           # Constraints data for Inspector
├── presets.db                # SQLite presets storage
│
├── assets/
│   ├── apollo_viewer.css     # Global UI styles
│   ├── ApolloViewerFonts.ttf # Icon font for toolbars
│   └── osifont.ttf           # PDF font
│
├── locales/
│   ├── en.json               # i18n English
│   ├── ru.json               # i18n Russian
│   └── cn.json               # i18n Chinese
│
├── components/
│   ├── sidebar.py            # Left panel inputs
│   └── viewer.py             # 2D/3D panels, preset modal
│
├── callbacks/
│   ├── ui_updater.py         # Field visibility, validation, sync
│   ├── graph_updater.py      # Main generation callback
│   ├── plotly_ui.py          # 3D toolbar interactions
│   ├── presets.py            # Preset CRUD operations
│   ├── constraints_viewer.py # Constraints modal
│   └── i18n_callbacks.py     # Language switching
│
└── core/
    ├── defaults.py           # Single source of truth for defaults
    ├── db.py                 # SQLite access layer
    ├── i18n.py               # Translation helper
    ├── engine.py             # Facade over domain geometry
    ├── preset_naming.py      # Shared preset/PDF drawing-number naming helper
    ├── renderer.py           # 2D drawing (matplotlib)
    ├── renderer_3d.py        # 3D rendering (Plotly)
    ├── stl_exporter.py       # STL mesh export
    ├── pdf_generator.py      # PDF specification export
    └── domain/
        ├── shapes.py         # Shape geometry helpers
        ├── profiles.py       # Cup profile equations
        └── mesh.py           # Mesh generation + metrics
```

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INPUT (UI)                             │
│  components/sidebar.py ←── core/defaults.py (initial values)        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CALLBACKS (Validation + Sync)                    │
│  callbacks/ui_updater.py                                            │
│  - Clamp values to valid ranges                                     │
│  - Synchronize dependent parameters                                 │
│  - Apply profile/shape constraints                                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PARAMS ASSEMBLY                                  │
│  callbacks/graph_updater.py::_build_params()                        │
│  - Collect all inputs into params dict                              │
│  - Fill None values from core/defaults.py                           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    GEOMETRY ENGINE                                  │
│  core/engine.py → core/domain/*.py                                  │
│  - Generate mesh                                                    │
│  - Calculate metrics (volume, SA, weight)                           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    OUTPUT GENERATION                                │
│  core/renderer.py      → 2D drawing                                │
│  core/renderer_3d.py   → 3D Plotly mesh                            │
│  core/pdf_generator.py → PDF specification                         │
│  core/stl_exporter.py  → STL mesh file                             │
│  core/preset_naming.py → Shared preset + drawing-number naming     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Business Logic Rules (MANDATORY)

### Precision & Limits

| Rule | Value | Reason |
|------|-------|--------|
| Decimal precision | 4 digits after decimal | Manufacturing tolerance |
| Minimum value | `0.01` | Prevents degenerate geometry |
| UI step | `0.01` | Consistent user experience |
| Bevel Angle max | `60°` | Tooling limitation |

### Geometric Constraints

#### Thickness vs Diameter (Round Tablets)
```
IF W < Tt THEN Tt = W
IF Hb < 0.01 THEN reduce Dc (preserve cup shape as long as possible)
```

#### Thickness Formula
```
Tt = Hb + 2 × Dc  (always true)
```

#### Cup Depth ↔ Cup Radius (Bidirectional)
```
Rc = (span² + Dc²) / (2 × Dc)
Dc = Rc - √(Rc² - span²)
```

#### Weight → Thickness
```
Weight change → Hb adjustment (not Dc)
Hb minimum = 0.01
Stop reducing at Hb = 0.01 (preserve cup geometry)
```

### Empty Input Handling
- **Never crash** on empty input
- Restore last valid value on blur/enter
- Use `dash.no_update` to prevent unnecessary re-renders

---

## Architecture Rules (MANDATORY)

### 1. Single Source of Truth

**✅ CORRECT:**
```python
from core.defaults import BASE_DEFAULTS, PROFILE_DEFAULTS

w = params.get("W") or BASE_DEFAULTS["W"]
```

**❌ FORBIDDEN:**
```python
w = params.get("W", 7.94)  # Magic number!
```

### 2. Fail-Fast Principle

**✅ CORRECT:**
```python
def render_tablet(params):
    if "W" not in params:
        raise KeyError("Missing required parameter: W")
    # ... proceed with guaranteed params
```

**❌ FORBIDDEN:**
```python
def render_tablet(params):
    w = params.get("W", 7.94)  # Silent failure!
```

### 3. Input Factory Pattern

**✅ CORRECT:**
```python
# In components/sidebar.py
make_input("input-w", "W (mm)", default=BASE_DEFAULTS["W"])
```

**❌ FORBIDDEN:**
```python
# Hardcoded input
html.Div([
    dbc.Input(id="input-w", value=7.94, type="number")
])
```

### 4. Callback Best Practices

**✅ CORRECT:**
```python
@callback(
    [Output("field-a", "value"), Output("field-b", "value")],
    [Input("trigger", "value")],
    prevent_initial_call=True
)
def update_fields(trigger_val):
    if trigger_val is None:
        return dash.no_update, dash.no_update
    
    new_a = calculate_a(trigger_val)
    new_b = calculate_b(trigger_val)
    
    return new_a, new_b  # Only update if changed
```

**❌ FORBIDDEN:**
```python
# Returns values even when unchanged → infinite loop
return trigger_val * 2, trigger_val * 3
```

### 5. Error Handling

**✅ CORRECT:**
```python
try:
    mesh = generate_mesh(params)
except (ValueError, ZeroDivisionError, OverflowError) as e:
    # Expected geometry errors
    print(f"Geometry error: {e}")
    return error_state
```

**❌ FORBIDDEN:**
```python
try:
    mesh = generate_mesh(params)
except Exception:  # Catches TypeError, NameError, etc.
    pass  # Hides bugs!
```

---

## Supported Configurations

### Shapes
| Shape | Profiles | Bisect Options |
|-------|----------|----------------|
| Round | CON, COM, CBE, FFRE, FFBE | None, Standard, Cut Through, Decreasing, Cruciform |
| Capsule | CON, CBE, FFRE, FFBE | None, Standard, Cut Through, Decreasing, Double-sided |
| Capsule (Modified) | CON, CBE | None, Standard, Cut Through, Decreasing, Double-sided |
| Oval | CON, MOD, COM, CBE, FFRE, FFBE | None, Standard, Cut Through, Decreasing, Double-sided |

### Profile Codes
| Code | Full Name |
|------|-----------|
| CON | Concave |
| COM | Compound Cup |
| CBE | Concave Bevel Edge |
| FFRE | Flat Face Radius Edge |
| FFBE | Flat Face Bevel Edge |
| MOD | Modified Oval |

---

## Key Parameters

| Parameter | Description | Typical Range |
|-----------|-------------|---------------|
| `W` | Width/Diameter | 3–25 mm |
| `L` | Length (non-round) | W–30 mm |
| `Tt` | Tablet Thickness | 1–10 mm |
| `Dc` | Cup Depth | 0.1–3 mm |
| `Hb` | Belly Band | 0.01–5 mm |
| `Rc_min` | Minor Cup Radius | 3–50 mm |
| `Rc_maj` | Major Cup Radius (Oval) | 10–100 mm |
| `Land` | Land width | 0.05–0.5 mm |
| `Bev_A` | Bevel Angle | 20–60° |
| `density` | Material density | 1.0–1.5 g/cm³ |

---

## Common Tasks

### Adding a New Input Field

1. Add default to `core/defaults.py`
2. Create input in `components/sidebar.py` using `make_input()`
3. Add to `_build_params()` in `callbacks/graph_updater.py`
4. Add validation/sync logic in `callbacks/ui_updater.py` if needed
5. Update i18n files (`locales/*.json`)

### Adding a New Profile

1. Add profile equation in `core/domain/profiles.py`
2. Add defaults in `core/defaults.py` under `PROFILE_DEFAULTS`
3. Update `_profile_options()` in `callbacks/ui_updater.py`
4. Add visibility rules in `update_ui_visibility()`
5. Add validation constraints in `sync_cup_radii_depth()`
6. Add test case in `tests/test_golden_regression.py`

### Adding a New Shape

1. Add shape geometry in `core/domain/shapes.py`
2. Add shape-specific defaults in `core/defaults.py`
3. Update UI controls in `components/sidebar.py`
4. Add shape button callbacks in `callbacks/ui_updater.py`
5. Add shape contour logic in `core/renderer_3d.py`
6. Add test cases for all profiles

---

## Testing

### Run Tests
```bash
pytest -q
```

### Test Structure
- `tests/` — unit and integration tests
- Test coverage includes geometry calculations, profile equations, and UI callbacks

---

## Internationalization (i18n)

### Translation Files
- `locales/en.json`
- `locales/ru.json`
- `locales/cn.json`

### Usage in Code
```python
from core.i18n import t

label = t("dim.w", lang)  # lang from "lang-store"
```

### Adding New Translation
1. Add key to all three locale files
2. Use `t("key.subkey", lang)` in components

---

## Performance Considerations

### Bottlenecks
| Component | Time % | Optimization |
|-----------|--------|--------------|
| `generate_mesh()` | 30-40% | Reduce mesh_n for PDF |
| `render_tablet_3d()` | 20-30% | Lower theta/rr resolution |
| Plotly `to_image()` | Variable | Lower DPI for PDF |

### Optimization Opportunities
- Adaptive mesh resolution based on export type
- Contour caching for unchanged shapes
- Numba JIT for profile calculations

---

## Troubleshooting

### UI Changes Not Visible
- Restart app
- Hard refresh: `Ctrl+F5`

### Callback Infinite Loop
- Check for missing `dash.no_update`
- Verify `prevent_initial_call=True`
- Check circular Input/Output dependencies

### Geometry Errors
- Check parameter bounds
- Verify profile/shape compatibility
- Check for degenerate inputs (zero spans, etc.)

### PDF Export Issues
- Check font files in `assets/`
- Verify `reportlab` is installed
- Check image DPI settings

---

## Code Style

### Python
- Follow PEP 8
- Use type hints for function signatures
- Docstrings for public functions
- Maximum line length: 100 characters

### Naming Conventions
| Type | Convention | Example |
|------|------------|---------|
| Functions | snake_case | `generate_mesh()` |
| Classes | PascalCase | `TabletGeometry` |
| Constants | UPPER_SNAKE | `BASE_DEFAULTS` |
| Variables | snake_case | `cup_depth` |
| Parameters | CamelCase in dict | `params["CupDepth"]` |

### Comments
- Use Russian for business logic explanations
- Use English for technical comments
- Document "why", not "what"

---

## Quick Reference

### Key Files to Know
| File | Purpose |
|------|---------|
| `core/defaults.py` | All default values |
| `core/engine.py` | Geometry facade |
| `core/preset_naming.py` | Shared preset and PDF drawing-number naming |
| `callbacks/ui_updater.py` | Validation & sync logic |
| `callbacks/graph_updater.py` | Main generation callback |

### Key Functions
| Function | Location | Purpose |
|----------|----------|---------|
| `generate_mesh()` | `core/engine.py` | Generate geometry + metrics |
| `_build_params()` | `callbacks/graph_updater.py` | Assemble params dict |
| `render_tablet()` | `core/renderer.py` | 2D drawing |
| `render_tablet_3d()` | `core/renderer_3d.py` | 3D Plotly mesh |
| `build_preset_base_name()` | `core/preset_naming.py` | Shared naming for presets and drawing numbers |

### Important Callbacks
| Callback | File | Triggers |
|----------|------|----------|
| `sync_weight_density_with_volume()` | `ui_updater.py` | Weight/Density/Geometry → Weight/Tt |
| `sync_cup_radii_depth()` | `ui_updater.py` | Dc ↔ Rc bidirectional sync |
| `sync_physical_params()` | `ui_updater.py` | Tt ↔ Hb ↔ Dc relationship |
| `update_ui_visibility()` | `ui_updater.py` | Show/hide fields by profile/shape |

---

## Do's and Don'ts

### ✅ DO
- Import defaults from `core/defaults.py`
- Use `dash.no_update` for unchanged outputs
- Validate inputs before calling geometry functions
- Round to 4 decimal places
- Test with `pytest` before committing
- Update i18n files for new labels

### ❌ DON'T
- Hardcode magic numbers
- Use `try...except Exception: pass`
- Create inputs without `make_input()`
- Return values that haven't changed
- Skip validation for "obviously correct" inputs
- Mix languages in comments (one per block)

---

*This document is the source of truth for AI assistants working on TabletCAD. When in doubt, refer to this file first.*
