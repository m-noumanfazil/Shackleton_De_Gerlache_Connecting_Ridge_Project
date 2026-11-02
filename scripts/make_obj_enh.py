#!/usr/bin/env python3
"""
make_obj_enh.py: Convert enhanced GeoTIFF DEM into a visual OBJ mesh with UVs and smooth normals.
Part of the enhanced Dominus lunar terrain mesh pipeline for Gazebo Fortress.
"""

import json
import os
import sys
from pathlib import Path

# Compatibility shim: prioritize system numpy (1.x) over local numpy 2.x if local breaks system scipy/matplotlib
for p in list(sys.path):
    if '.local' in p and 'site-packages' in p:
        sys.path.remove(p)
        import numpy as np
        sys.path.insert(0, p)
        break
else:
    import numpy as np

import rasterio


def generate_obj():
    script_dir = Path(__file__).resolve().parent
    enhanced_dir = script_dir.parent
    project_dir = enhanced_dir.parent

    tif_path = enhanced_dir / "enhanced_dem.tif"

    if not tif_path.exists():
        raise FileNotFoundError(f"Input DEM not found at: {tif_path}")

    with rasterio.open(tif_path) as src:
        data = src.read(1)
        if np.isnan(data).any():
            raise ValueError("DEM contains NaN elevation values. Cannot proceed.")
        elevation = data.astype(np.float32)
        pixel_size = float(abs(src.transform.a))

    assert abs(pixel_size - 0.625) < 1e-6, f"pixel_size must be 0.625, got {pixel_size}"
    print(f"pixel_size: {pixel_size}")

    # Read subtracted_z_offset_meters from project_dir/c1_terrain/meshes/terrain_meta.json
    meta_json_path = project_dir / "c1_terrain" / "meshes" / "terrain_meta.json"
    if not meta_json_path.exists():
        raise FileNotFoundError(f"Original metadata not found at: {meta_json_path}")
    with open(meta_json_path, "r") as f:
        orig_meta = json.load(f)
    z_offset = float(orig_meta["subtracted_z_offset_meters"])
    print(f"z_offset: {z_offset}")

    rows, cols = elevation.shape

    # Geometry calculations
    # Re-center x and y so terrain is centered at (0, 0)
    x_center = (cols - 1) * pixel_size / 2.0
    y_center = (rows - 1) * pixel_size / 2.0

    z_min = float(np.min(elevation))
    z_max = float(np.max(elevation))

    # Coordinates per grid vertex
    # col goes 0..cols-1 (+X east), row goes 0..rows-1 (+Y north, so flipped)
    col_indices = np.arange(cols, dtype=np.float32)
    row_indices = np.arange(rows, dtype=np.float32)

    x_coords = col_indices * pixel_size - x_center
    y_coords = (rows - 1 - row_indices) * pixel_size - y_center
    z_coords = elevation - z_offset

    # Compute UVs: u = (x - xmin) / width, v = (y - ymin) / height
    # u ranges from 0 (col=0) to 1 (col=cols-1)
    # v ranges from 0 (row=rows-1, south) to 1 (row=0, north)
    u_coords = col_indices / (cols - 1)
    v_coords = (rows - 1 - row_indices) / (rows - 1)

    # Compute smooth per-vertex normals using central differences on heightfield
    # z = f(x, y). Gradient is (-dz/dx, -dz/dy, 1.0)
    dx = pixel_size
    dy = pixel_size

    # dz/dx: X increases with col
    dz_dx = np.zeros_like(z_coords)
    dz_dx[:, 1:-1] = (z_coords[:, 2:] - z_coords[:, :-2]) / (2.0 * dx)
    dz_dx[:, 0] = (z_coords[:, 1] - z_coords[:, 0]) / dx
    dz_dx[:, -1] = (z_coords[:, -1] - z_coords[:, -2]) / dx

    # dz/dy: Y increases as row decreases (row 0 is north / max Y)
    # y = (rows - 1 - row) * dy => delta_y = -dy * delta_row
    # dz/dy = (z(y + dy) - z(y - dy)) / (2 * dy) = (z[row - 1] - z[row + 1]) / (2 * dy)
    dz_dy = np.zeros_like(z_coords)
    dz_dy[1:-1, :] = (z_coords[:-2, :] - z_coords[2:, :]) / (2.0 * dy)
    dz_dy[0, :] = (z_coords[0, :] - z_coords[1, :]) / dy
    dz_dy[-1, :] = (z_coords[-2, :] - z_coords[-1, :]) / dy

    nx = -dz_dx
    ny = -dz_dy
    nz = np.ones_like(z_coords)

    norm_len = np.sqrt(nx**2 + ny**2 + nz**2)
    nx /= norm_len
    ny /= norm_len
    nz /= norm_len

    # Prepare output directories
    meshes_dir = enhanced_dir / "c1_terrain_enh" / "meshes"
    meshes_dir.mkdir(parents=True, exist_ok=True)

    obj_path = meshes_dir / "terrain_visual.obj"
    mtl_path = meshes_dir / "terrain_visual.mtl"
    meta_path = meshes_dir / "terrain_meta.json"

    # Write MTL file
    mtl_content = (
        "# Material definition for Dominus terrain\n"
        "newmtl regolith\n"
        "Ka 0.000000 0.000000 0.000000\n"
        "Kd 0.100000 0.100000 0.100000\n"
        "Ks 0.000000 0.000000 0.000000\n"
        "map_Kd ../textures/regolith_dark_albedo.png\n"
    )
    with open(mtl_path, "w") as f_mtl:
        f_mtl.write(mtl_content)

    # Write OBJ file
    # Vertex order: row-major (r from 0..rows-1, c from 0..cols-1)
    vertex_count = rows * cols
    triangle_count = (rows - 1) * (cols - 1) * 2

    with open(obj_path, "w") as f_obj:
        f_obj.write("# Dominus C1 Safest Terrain Visual Mesh\n")
        f_obj.write("mtllib terrain_visual.mtl\n\n")

        # Write positions (v)
        for r in range(rows):
            y_val = y_coords[r]
            for c in range(cols):
                f_obj.write(f"v {x_coords[c]:.6f} {y_val:.6f} {z_coords[r, c]:.6f}\n")

        # Write texture coordinates (vt)
        for r in range(rows):
            v_val = v_coords[r]
            for c in range(cols):
                f_obj.write(f"vt {u_coords[c]:.6f} {v_val:.6f}\n")

        # Write vertex normals (vn)
        for r in range(rows):
            for c in range(cols):
                f_obj.write(f"vn {nx[r, c]:.6f} {ny[r, c]:.6f} {nz[r, c]:.6f}\n")

        f_obj.write("\nusemtl regolith\n")

        # Write faces (f v/vt/vn)
        for r in range(rows - 1):
            for c in range(cols - 1):
                tl = r * cols + c + 1
                tr = r * cols + (c + 1) + 1
                bl = (r + 1) * cols + c + 1
                br = (r + 1) * cols + (c + 1) + 1

                # Tri 1
                f_obj.write(f"f {bl}/{bl}/{bl} {br}/{br}/{br} {tl}/{tl}/{tl}\n")
                # Tri 2
                f_obj.write(f"f {br}/{br}/{br} {tr}/{tr}/{tr} {tl}/{tl}/{tl}\n")

    # Write metadata JSON
    meta_info = {
        "dem_file": "enhanced_dem.tif",
        "rows": int(rows),
        "cols": int(cols),
        "pixel_size_meters": float(pixel_size),
        "total_width_meters": float((cols - 1) * pixel_size),
        "total_height_meters": float((rows - 1) * pixel_size),
        "elevation_min_meters": float(z_min),
        "elevation_max_meters": float(z_max),
        "elevation_relief_meters": float(z_max - z_min),
        "subtracted_z_offset_meters": float(z_offset),
        "x_center_offset_meters": float(x_center),
        "y_center_offset_meters": float(y_center),
        "bounds": {
            "x_min": float(np.min(x_coords)),
            "x_max": float(np.max(x_coords)),
            "y_min": float(np.min(y_coords)),
            "y_max": float(np.max(y_coords)),
            "z_min": float(np.min(z_coords)),
            "z_max": float(np.max(z_coords))
        },
        "vertex_count": int(vertex_count),
        "triangle_count": int(triangle_count)
    }

    with open(meta_path, "w") as f_meta:
        json.dump(meta_info, f_meta, indent=2)

    # Print summary output
    print("=== make_obj_enh.py finished successfully ===")
    print(f"Vertices: {vertex_count}")
    print(f"Triangles: {triangle_count}")
    print(f"Bounding box:")
    print(f"  X: [{meta_info['bounds']['x_min']:.2f}, {meta_info['bounds']['x_max']:.2f}] m")
    print(f"  Y: [{meta_info['bounds']['y_min']:.2f}, {meta_info['bounds']['y_max']:.2f}] m")
    print(f"  Z: [{meta_info['bounds']['z_min']:.2f}, {meta_info['bounds']['z_max']:.2f}] m")
    print(f"Subtracted elevation offset: {z_offset:.4f} m (original elevation: {z_min:.2f} to {z_max:.2f} m)")
    print(f"Files written:")
    print(f"  {obj_path} ({obj_path.stat().st_size} bytes)")
    print(f"  {mtl_path}")
    print(f"  {meta_path}")


if __name__ == "__main__":
    generate_obj()
