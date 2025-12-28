# 表面1から見て、表面2との 片側表面間距離
# 表面1の各点において、最近接する表面2の点を探索し、その点を頂点とする三角形群に対して、射影して距離計算するか、射影できなければ辺上でもっとも距離が近くなる
# 点との距離を計算し、最小のものを採用する

import os
import numpy as np
import myio
import utility
try:
    from scipy.spatial import cKDTree as KDTree
except Exception:
    KDTree = None

def as_array_nodes(nodes):
    coords = np.empty((len(nodes), 3), dtype=float)
    id_to_idx = {}
    for i, nd in enumerate(nodes):
        v = utility.vector(nd)
        coords[i, :] = v
        id_to_idx[nd.id] = i
    return coords, id_to_idx

if __name__=="__main__":
    # 入力はSTLでもVTKでもOK
    filepath1 = myio.select_surface()
    filepath2 = myio.select_surface()
    if os.path.splitext(filepath1)[1].lower() == ".stl":
        filepath1 = myio.convert_stl_to_vtk(filepath1)
    if os.path.splitext(filepath2)[1].lower() == ".stl":
        filepath2 = myio.convert_stl_to_vtk(filepath2)
    (surface_nodes1, surface_node_dict1,surface_triangles1, surface_triangle_dict1) = myio.read_vtk_for_hausdorff(filepath1)
    (surface_nodes2, surface_node_dict2,surface_triangles2, surface_triangle_dict2) = myio.read_vtk_for_hausdorff(filepath2)

    # ノード座標を配列化 & id→index を構築
    P1, id_to_idx_1 = as_array_nodes(surface_nodes1)  # shape: (N1,3)
    P2, id_to_idx_2 = as_array_nodes(surface_nodes2)  # shape: (N2,3)

    # 近傍探索: KDTree（なければ総当たりフォールバック）
    if KDTree is not None:
        tree = KDTree(P2)
        # distances: (N1,), indices: (N1,)
        _, nn_idx = tree.query(P1, k=1, workers=-1)
    else:
        # フォールバック（総当たり）。メモリ余裕があれば距離行列を作ってargmin
        # 距離二乗のargminでもOK（比較のみ）だが、以降の「最近傍ノードID」取得が目的なので距離は使わない。
        # ただしMが大きいと重いので、可能ならSciPy導入を推奨。
        # ここではメモリ節約の逐次版：
        nn_idx = np.empty(P1.shape[0], dtype=int)
        for i, p in enumerate(P1):
            d2 = np.sum((P2 - p)**2, axis=1)
            nn_idx[i] = int(np.argmin(d2))

    # 最近傍ノードIDを各nodeに保存（従来仕様を踏襲）
    for i, idx2 in enumerate(nn_idx):
        surface_nodes1[i].closest_surface_node_id = int(idx2) + 1

    # 三角形頂点の座標アクセスを速くするためのヘルパ
    # tri.nodeX.id -> index -> 座標 という流れにする
    def tri_vertices_coords_in_surf2(tri):
        A = surface_node_dict2[tri.node0.id]
        B = surface_node_dict2[tri.node1.id]
        C = surface_node_dict2[tri.node2.id]
        return A, B, C

    # 片側Hausdorff距離（ノード→最近傍点の属する三角形群への点-三角形距離の最小）
    haus = np.empty(len(surface_nodes1), dtype=float)

    for i, nd1 in enumerate(surface_nodes1):
        # 最近傍ノード（surface2側）のインデックス（0始まり）
        j2 = nd1.closest_surface_node_id - 1
        nb_node2 = surface_nodes2[j2]

        # そのノードが関係する三角形IDの集合を走査
        min_d = float("inf")
        rel_tri_ids = nb_node2.related_triangle_ids

        for tri_id in rel_tri_ids:
            tri = surface_triangle_dict2[tri_id]
            A, B, C = tri_vertices_coords_in_surf2(tri)
            d = utility.calc_point_to_triangle_distance(nd1, A, B, C)
            if d < min_d:
                min_d = d

        haus[i] = min_d

    myio.write_vtk_hausdorff(surface_nodes1, surface_triangles1, haus.tolist())

    haus_min = float(np.min(haus))
    haus_max = float(np.max(haus))
    haus_ave = float(np.mean(haus))

    filepath_haus = os.path.join("output", "hausdorff.txt")
    memo = f"""max_hausdorff_distance  : {haus_max} 
min_hausdorff_distance  : {haus_min}
ave_hausdorff_distance  : {haus_ave}"""
    with open(filepath_haus, "w") as f:
        f.write(memo)
