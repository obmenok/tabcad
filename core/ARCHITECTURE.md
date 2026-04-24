Domain-first structure:

- `core/domain/profiles.py`: pure cup profile equations.
- `core/domain/shapes.py`: shape normalization and geometry helpers.
- `core/domain/mesh.py`: mesh generation, bisect math, metrics.
- `core/engine.py`: compatibility facade used by callbacks/renderer.
- `core/preset_naming.py`: shared naming helper for preset codes and PDF drawing numbers.
- `core/reference_bridge.py`: temporary bridge to exact Natoli scripts.

Goal:
- keep `domain` as the single source of truth for universal math;
- use Natoli scripts as reference outputs until full parity and tests;
- then remove bridge/fallback and keep one clean runtime path.
