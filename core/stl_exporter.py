import struct
import numpy as np
import io
from core.renderer_3d import _shape_contour, _boundary_radius_from_contour, _interp_bilinear

def write_binary_stl(triangles):
    """
    Writes triangles to a binary STL format.
    triangles: (N, 3, 3) numpy array of floats.
    Returns: bytes
    """
    # Calculate normals
    v0 = triangles[:, 0, :]
    v1 = triangles[:, 1, :]
    v2 = triangles[:, 2, :]
    normals = np.cross(v1 - v0, v2 - v0)
    
    # Normalize normals
    norms = np.linalg.norm(normals, axis=1, keepdims=True)
    norms[norms == 0] = 1.0 # avoid division by zero
    normals = normals / norms

    num_triangles = len(triangles)
    
    # Create binary structure
    # Header: 80 bytes
    # Num triangles: 4 bytes (uint32)
    # Triangle data: 50 bytes each
    buffer = io.BytesIO()
    buffer.write(b'TabletCAD Generated STL' + b'\0' * 57)
    buffer.write(struct.pack('<I', num_triangles))
    
    for i in range(num_triangles):
        # 3 floats for normal, 9 floats for vertices, 1 uint16 for attr
        buffer.write(struct.pack('<3f', *normals[i]))
        buffer.write(struct.pack('<3f', *v0[i]))
        buffer.write(struct.pack('<3f', *v1[i]))
        buffer.write(struct.pack('<3f', *v2[i]))
        buffer.write(struct.pack('<H', 0))
        
    return buffer.getvalue()

def grid_to_triangles(X, Y, Z, flip_normals=False):
    """Convert a 2D structured grid into a list of triangles."""
    rows, cols = Z.shape
    v0 = np.stack([X[:-1, :-1], Y[:-1, :-1], Z[:-1, :-1]], axis=-1).reshape(-1, 3)
    v1 = np.stack([X[1:, :-1], Y[1:, :-1], Z[1:, :-1]], axis=-1).reshape(-1, 3)
    v2 = np.stack([X[:-1, 1:], Y[:-1, 1:], Z[:-1, 1:]], axis=-1).reshape(-1, 3)
    v3 = np.stack([X[1:, 1:], Y[1:, 1:], Z[1:, 1:]], axis=-1).reshape(-1, 3)
    
    # Quad is v0, v1, v2, v3
    # Triangle 1: v0, v1, v2
    # Triangle 2: v1, v3, v2
    if flip_normals:
        t1 = np.stack([v0, v2, v1], axis=1)
        t2 = np.stack([v1, v2, v3], axis=1)
    else:
        t1 = np.stack([v0, v1, v2], axis=1)
        t2 = np.stack([v1, v3, v2], axis=1)
        
    return np.concatenate([t1, t2], axis=0)

def generate_tablet_stl(mesh_data, params):
    hb = max(0.0, params.get("Hb", 2.54))
    x_grid = mesh_data["x_grid"]
    y_grid = mesh_data["y_grid"]
    z_top_grid = mesh_data["Z_cup_top"]
    z_bot_grid = mesh_data.get("Z_cup_bottom", mesh_data["Z"])

    theta = np.linspace(0, 2 * np.pi, 320)
    rr = np.linspace(0, 1, 160)
    rr_grid, tt_grid = np.meshgrid(rr, theta, indexing="ij")

    x_c, y_c = _shape_contour(params)
    r_boundary = _boundary_radius_from_contour(x_c, y_c, theta)
    r_grid = rr_grid * r_boundary[None, :]
    x_s = r_grid * np.cos(tt_grid)
    y_s = r_grid * np.sin(tt_grid)

    z_top_interp = _interp_bilinear(z_top_grid, x_grid, y_grid, x_s, y_s)
    z_bot_interp = _interp_bilinear(z_bot_grid, x_grid, y_grid, x_s, y_s)
    zt_s = z_top_interp + hb / 2
    zb_s = -z_bot_interp - hb / 2

    # Bottom needs flip_normals=True to face outwards (downwards)
    tri_top = grid_to_triangles(x_s, y_s, zt_s, flip_normals=False)
    tri_bot = grid_to_triangles(x_s, y_s, zb_s, flip_normals=True)

    # Band (Cylinder side wall)
    z_line = np.array([-hb / 2, hb / 2])
    xb = np.tile(r_boundary * np.cos(theta), (len(z_line), 1))
    yb = np.tile(r_boundary * np.sin(theta), (len(z_line), 1))
    zb = np.tile(z_line[:, None], (1, len(theta)))
    
    # Band flip depends on meshgrid generation, usually False or True depending on the orientation of z_line
    # z_line is bottom to top. X axis is along theta.
    tri_band = grid_to_triangles(xb, yb, zb, flip_normals=False)
    
    all_triangles = np.concatenate([tri_top, tri_bot, tri_band], axis=0)
    
    # Optional: fill the center holes created by the radial grid at r=0. 
    # Usually they converge to a point, but we can leave them if the grid is dense enough.
    
    return write_binary_stl(all_triangles)
