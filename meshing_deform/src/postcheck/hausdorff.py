# 表面1から見て、表面2との 片側表面間距離
# 表面1の各点において、最近接する表面2の点を探索し、その点を頂点とする三角形群に対して、射影して距離計算するか、射影できなければ辺上でもっとも距離が近くなる
# 点との距離を計算し、最小のものを採用する

import os
import numpy as np
import tkinter as tk
from tkinter import filedialog

try:
    from scipy.spatial import cKDTree as KDTree
except Exception:
    KDTree = None


class NodeForHausdorff:
    def __init__(self, id, x, y, z):
        self.id = id
        self.x = x
        self.y = y
        self.z = z
        self.closest_surface_node_id = None
        self.related_triangle_ids = []

    def append(self, id):
        self.related_triangle_ids.append(id)


class Triangle:
    def __init__(self, id, node0, node1, node2):
        self.id = id
        self.node0 = node0
        self.node1 = node1
        self.node2 = node2


def vec(node):
    return np.array([node.x, node.y, node.z], dtype=float)


# ----------------------------
# GUI helpers
# ----------------------------
def select_surface(initialdir=None):
    """Select a surface file (.stl or .vtk) and return its absolute path (or '' if cancelled)."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    filepath = filedialog.askopenfilename(
        title="Select surface file",
        filetypes=[
            ("All supported files", "*.stl *.vtk"),
            ("STL files", "*.stl"),
            ("VTK files", "*.vtk"),
            ("All files", "*.*"),
        ],
        initialdir=initialdir if initialdir is not None else os.getcwd(),
        parent=root,
    )
    root.destroy()
    return filepath


def select_output_dir(initialdir=None):
    """Select output folder and return its absolute path (or '' if cancelled)."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    out_dir = filedialog.askdirectory(
        title="Select output folder",
        initialdir=initialdir if initialdir is not None else os.getcwd(),
        parent=root,
    )
    root.destroy()
    return out_dir


# ----------------------------
# STL -> VTK (UNSTRUCTURED_GRID)
# ----------------------------
def convert_stl_to_vtk(filepath_stl, output_dir):
    """
    Convert ASCII STL to VTK (UNSTRUCTURED_GRID).
    Output is written into output_dir with the same base name as STL.
    """
    filename_without_ext = os.path.splitext(os.path.basename(filepath_stl))[0]
    output_filename = filename_without_ext + ".vtk"

    os.makedirs(output_dir, exist_ok=True)
    output_filepath = os.path.join(output_dir, output_filename)

    triangles = []
    with open(filepath_stl, "r") as f:
        lines = f.readlines()

    current_triangle = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 4 and parts[0].lower() == "vertex":
            x, y, z = map(float, parts[1:4])
            current_triangle.append((x, y, z))
            if len(current_triangle) == 3:
                triangles.append(tuple(current_triangle))
                current_triangle = []

    points = []
    point_index = {}
    cells = []

    for tri in triangles:
        cell = []
        for p in tri:
            if p not in point_index:
                point_index[p] = len(points)
                points.append(p)
            cell.append(point_index[p])
        cells.append(cell)

    with open(output_filepath, "w") as f:
        f.write("# vtk DataFile Version 2.0\n")
        f.write("Converted from STL\n")
        f.write("ASCII\n")
        f.write("DATASET UNSTRUCTURED_GRID\n")

        f.write(f"POINTS {len(points)} double\n")
        for x, y, z in points:
            f.write(f"{x} {y} {z}\n")
        f.write("\n")

        total_size = len(cells) * 4
        f.write(f"CELLS {len(cells)} {total_size}\n")
        for c in cells:
            f.write(f"3 {c[0]} {c[1]} {c[2]}\n")
        f.write("\n")

        f.write(f"CELL_TYPES {len(cells)}\n")
        for _ in cells:
            f.write("5\n")

    print(f"finished stl_to_vtk convert: {output_filepath}")
    return output_filepath


# ----------------------------
# Read VTK (expects POINTS + CELLS triangles)
# ----------------------------
def read_vtk_for_hausdorff(filepath_vtk):
    with open(filepath_vtk, "r") as file:
        lines = file.readlines()

    points_section = False
    cells_section = False

    surface_node_dict = {}
    surface_nodes = []
    surface_triangle_dict = {}
    surface_triangles = []

    node_id = 1
    triangle_id = 1

    for line in lines:
        line = line.strip()

        if line.startswith("POINTS"):
            points_section = True
            cells_section = False
            node_id = 1
            surface_node_dict = {}
            surface_nodes = []
            continue

        if line.startswith("CELLS"):
            points_section = False
            cells_section = True
            triangle_id = 1
            surface_triangle_dict = {}
            surface_triangles = []
            continue

        if points_section:
            if not line:
                points_section = False
                continue
            coords = list(map(float, line.split()))
            x, y, z = coords[0], coords[1], coords[2]
            surface_node = NodeForHausdorff(node_id, x, y, z)
            surface_node_dict[node_id] = surface_node
            surface_nodes.append(surface_node)
            node_id += 1

        if cells_section:
            if line.startswith("CELL_TYPES") or line.startswith("POINT_DATA") or line.startswith("CELL_DATA"):
                cells_section = False
                continue
            if not line:
                cells_section = False
                continue
            cell_data = list(map(int, line.split()))
            if cell_data[0] == 3:
                node0 = surface_node_dict[cell_data[1] + 1]
                node1 = surface_node_dict[cell_data[2] + 1]
                node2 = surface_node_dict[cell_data[3] + 1]
                surface_triangle = Triangle(triangle_id, node0, node1, node2)
                surface_triangle_dict[triangle_id] = surface_triangle
                surface_triangles.append(surface_triangle)

                surface_node_dict[cell_data[1] + 1].append(triangle_id)
                surface_node_dict[cell_data[2] + 1].append(triangle_id)
                surface_node_dict[cell_data[3] + 1].append(triangle_id)
                triangle_id += 1

    return surface_nodes, surface_node_dict, surface_triangles, surface_triangle_dict


# ----------------------------
# Write Hausdorff VTK (POLYDATA) to a chosen output folder
# ----------------------------
def write_vtk_hausdorff(
    surface_nodes,
    surface_triangles,
    haus,
    output_dir,
    filename="hausdorff.vtk",
):
    """
    Always write into output_dir (no GUI here; output_dir is already selected).
    """
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    n_points = len(surface_nodes)
    n_tri = len(surface_triangles)

    with open(filepath, "w") as f:
        f.write("# vtk DataFile Version 2.0\n")
        f.write("Hausdorff distance\n")
        f.write("ASCII\n")
        f.write("DATASET POLYDATA\n")

        f.write(f"POINTS {n_points} float\n")
        for pt in surface_nodes:
            f.write(f"{pt.x} {pt.y} {pt.z}\n")

        f.write(f"POLYGONS {n_tri} {n_tri * 4}\n")
        for tri in surface_triangles:
            f.write(f"3 {tri.node0.id - 1} {tri.node1.id - 1} {tri.node2.id - 1}\n")

        f.write(f"POINT_DATA {n_points}\n")
        f.write("SCALARS haus float 1\n")
        f.write("LOOKUP_TABLE default\n")
        for v in haus:
            f.write(f"{v}\n")

    print(f"Saved: {filepath}")
    return filepath


# ----------------------------
# Utilities
# ----------------------------
def as_array_nodes(nodes):
    coords = np.empty((len(nodes), 3), dtype=float)
    id_to_idx = {}
    for i, nd in enumerate(nodes):
        coords[i, :] = vec(nd)
        id_to_idx[nd.id] = i
    return coords, id_to_idx


def calc_point_to_triangle_distance(P, A, B, C):
    """
    点 P と三角形 ABC の最短距離を計算
    """
    AB = vec(B) - vec(A)
    AC = vec(C) - vec(A)
    AP = vec(P) - vec(A)

    d1 = np.dot(AB, AP)
    d2 = np.dot(AC, AP)
    d3 = np.dot(AB, AB)
    d4 = np.dot(AB, AC)
    d5 = np.dot(AC, AC)

    denom = d3 * d5 - d4 * d4

    if denom == 0:
        return np.linalg.norm(AP)

    v = (d5 * d1 - d4 * d2) / denom
    w = (d3 * d2 - d4 * d1) / denom
    u = 1 - v - w

    if u >= 0 and v >= 0 and w >= 0:
        N = np.cross(AB, AC)
        nrm = np.linalg.norm(N)
        if nrm == 0:
            return np.linalg.norm(AP)
        N = N / nrm
        dist = abs(np.dot(AP, N))
    else:
        def segment_distance(P, Q, R):
            QR = vec(R) - vec(Q)
            denom2 = np.dot(QR, QR)
            if denom2 == 0:
                return np.linalg.norm(vec(P) - vec(Q))
            t = np.dot(vec(P) - vec(Q), QR) / denom2
            t = np.clip(t, 0, 1)
            projection = vec(Q) + t * QR
            return np.linalg.norm(vec(P) - projection)

        dist = min(
            segment_distance(P, A, B),
            segment_distance(P, B, C),
            segment_distance(P, C, A),
        )

    return dist


# ----------------------------
# Main
# ----------------------------
if __name__ == "__main__":
    # 1) 出力フォルダを最初に1回だけ選ぶ（以降、すべてここに出す）
    out_dir = select_output_dir()
    if not out_dir:
        print("Output folder selection cancelled.")
        raise SystemExit

    # 2) 入力ファイル選択（できれば out_dir を初期ディレクトリにしておく）
    filepath1 = select_surface(initialdir=out_dir)
    filepath2 = select_surface(initialdir=out_dir)

    if not filepath1 or not filepath2:
        print("Input selection cancelled.")
        raise SystemExit

    # 3) STLなら out_dir にVTK変換出力
    if os.path.splitext(filepath1)[1].lower() == ".stl":
        filepath1 = convert_stl_to_vtk(filepath1, out_dir)
    if os.path.splitext(filepath2)[1].lower() == ".stl":
        filepath2 = convert_stl_to_vtk(filepath2, out_dir)

    # 4) VTK読み込み
    (surface_nodes1, surface_node_dict1, surface_triangles1, surface_triangle_dict1) = read_vtk_for_hausdorff(filepath1)
    (surface_nodes2, surface_node_dict2, surface_triangles2, surface_triangle_dict2) = read_vtk_for_hausdorff(filepath2)

    # 5) 配列化
    P1, _ = as_array_nodes(surface_nodes1)
    P2, _ = as_array_nodes(surface_nodes2)

    # 6) 最近傍探索
    if KDTree is not None:
        tree = KDTree(P2)
        _, nn_idx = tree.query(P1, k=1, workers=-1)
    else:
        nn_idx = np.empty(P1.shape[0], dtype=int)
        for i, p in enumerate(P1):
            d2 = np.sum((P2 - p) ** 2, axis=1)
            nn_idx[i] = int(np.argmin(d2))

    for i, idx2 in enumerate(nn_idx):
        surface_nodes1[i].closest_surface_node_id = int(idx2) + 1

    def tri_vertices_coords_in_surf2(tri):
        A = surface_node_dict2[tri.node0.id]
        B = surface_node_dict2[tri.node1.id]
        C = surface_node_dict2[tri.node2.id]
        return A, B, C

    # 7) 片側Hausdorff距離
    haus = np.empty(len(surface_nodes1), dtype=float)

    for i, nd1 in enumerate(surface_nodes1):
        j2 = nd1.closest_surface_node_id - 1
        nb_node2 = surface_nodes2[j2]

        min_d = float("inf")
        rel_tri_ids = nb_node2.related_triangle_ids

        for tri_id in rel_tri_ids:
            tri = surface_triangle_dict2[tri_id]
            A, B, C = tri_vertices_coords_in_surf2(tri)
            d = calc_point_to_triangle_distance(nd1, A, B, C)
            if d < min_d:
                min_d = d

        haus[i] = min_d

    # 8) VTK出力（必ず out_dir）
    vtk_out = write_vtk_hausdorff(
        surface_nodes1,
        surface_triangles1,
        haus.tolist(),
        output_dir=out_dir,
        filename="hausdorff.vtk",
    )

    # 9) テキスト出力（必ず out_dir）
    haus_min = float(np.min(haus))
    haus_max = float(np.max(haus))
    haus_ave = float(np.mean(haus))

    filepath_haus = os.path.join(out_dir, "hausdorff.txt")
    memo = f"""max_hausdorff_distance  : {haus_max} 
min_hausdorff_distance  : {haus_min}
ave_hausdorff_distance  : {haus_ave}"""
    with open(filepath_haus, "w") as f:
        f.write(memo)

    print(f"Saved: {filepath_haus}")
