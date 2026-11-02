#!/usr/bin/env python3
"""
make_stl_enh.py: Convert enhanced GeoTIFF DEM into a collision binary STL mesh.
Part of the enhanced Dominus lunar terrain mesh pipeline for Gazebo Fortress.
"""

import json
import os
import struct
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

COLLISION_STRIDE = 2  # ASSUMPTION


def generate_stl():
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

    # Full grid shape and center computation
    full_rows, full_cols = elevation.shape
    x_center = (full_cols - 1) * pixel_size / 2.0
    y_center = (full_rows - 1) * pixel_size / 2.0

    # Subsample elevation using stride and scale pixel size
    elevation_stl = elevation[::COLLISION_STRIDE, ::COLLISION_STRIDE]
    stl_pixel_size = pixel_size * COLLISION_STRIDE
    rows, cols = elevation_stl.shape

    col_indices = np.arange(cols, dtype=np.float32)
    row_indices = np.arange(rows, dtype=np.float32)

    x_coords = col_indices * stl_pixel_size - x_center
    y_coords = (rows - 1 - row_indices) * stl_pixel_size - y_center
    z_coords = elevation_stl - z_offset

    # Prepare vertices array in row-major order: (rows, cols, 3)
    vertices = np.zeros((rows, cols, 3), dtype=np.float32)
    for r in range(rows):
        vertices[r, :, 0] = x_coords
        vertices[r, :, 1] = y_coords[r]
        vertices[r, :, 2] = z_coords[r, :]

    # Prepare triangles
    # Cells: (rows - 1) x (cols - 1)
    tl = vertices[:-1, :-1, :]  # shape: (rows-1, cols-1, 3)
    tr = vertices[:-1, 1:, :]
    bl = vertices[1:, :-1, :]
    br = vertices[1:, 1:, :]

    # Flatten to list of triangles: (N, 3, 3)
    # Tri 1: (bl, br, tl)
    # Tri 2: (br, tr, tl)
    tri1 = np.stack([bl, br, tl], axis=2).reshape(-1, 3, 3)
    tri2 = np.stack([br, tr, tl], axis=2).reshape(-1, 3, 3)
    all_triangles = np.concatenate([tri1, tri2], axis=0)

    triangle_count = all_triangles.shape[0]
    vertex_count = rows * cols

    # Compute facet normals: cross(v1 - v0, v2 - v0)
    e1 = all_triangles[:, 1, :] - all_triangles[:, 0, :]
    e2 = all_triangles[:, 2, :] - all_triangles[:, 0, :]
    normals = np.cross(e1, e2)
    norm_lens = np.linalg.norm(normals, axis=1, keepdims=True)
    norm_lens[norm_lens == 0] = 1.0
    unit_normals = normals / norm_lens

    # Ensure all face normals point +Z (up)
    assert np.all(unit_normals[:, 2] > 0), "Some facet normals do not point upwards (+Z)!"

    # Prepare output directory and path
    meshes_dir = enhanced_dir / "c1_terrain_enh" / "meshes"
    meshes_dir.mkdir(parents=True, exist_ok=True)
    stl_path = meshes_dir / "terrain_collision.stl"

    # Write binary STL
    header = b"Dominus C1 Safest Terrain Collision Mesh".ljust(80, b"\x00")

    with open(stl_path, "wb") as f_stl:
        f_stl.write(header)
        f_stl.write(struct.pack("<I", triangle_count))

        # Each facet: normal (3f), v0 (3f), v1 (3f), v2 (3f), attribute byte count (1H = 0)
        facet_dtype = np.dtype([
            ('normal', '<f4', (3,)),
            ('v0', '<f4', (3,)),
            ('v1', '<f4', (3,)),
            ('v2', '<f4', (3,)),
            ('attr', '<u2')
        ])

        facets_data = np.empty(triangle_count, dtype=facet_dtype)
        facets_data['normal'] = unit_normals
        facets_data['v0'] = all_triangles[:, 0, :]
        facets_data['v1'] = all_triangles[:, 1, :]
        facets_data['v2'] = all_triangles[:, 2, :]
        facets_data['attr'] = 0

        f_stl.write(facets_data.tobytes())

    # Bounding box
    bbox_x = (float(np.min(x_coords)), float(np.max(x_coords)))
    bbox_y = (float(np.min(y_coords)), float(np.max(y_coords)))
    bbox_z = (float(np.min(z_coords)), float(np.max(z_coords)))

    print("=== make_stl_enh.py finished successfully ===")
    print(f"Vertices: {vertex_count}")
    print(f"Triangles: {triangle_count}")
    print(f"Bounding box:")
    print(f"  X: [{bbox_x[0]:.2f}, {bbox_x[1]:.2f}] m")
    print(f"  Y: [{bbox_y[0]:.2f}, {bbox_y[1]:.2f}] m")
    print(f"  Z: [{bbox_z[0]:.2f}, {bbox_z[1]:.2f}] m")
    print(f"File written:")
    print(f"  {stl_path} ({stl_path.stat().st_size} bytes)")


if __name__ == "__main__":
    generate_stl()
