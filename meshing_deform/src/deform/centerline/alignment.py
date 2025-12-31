from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from pathlib import Path
import commonlib.utility as utility
import commonlib.node as node
import commonlib.myio as myio
import numpy as np
import pandas as pd

def _unit(v, eps=1e-12):
    v = np.asarray(v, dtype=float).reshape(3,)
    n = np.linalg.norm(v)
    if n < eps or not np.isfinite(n):
        return None
    return v / n

def alignment(original_centerline_nodes,target_centerline_nodes, radius_list_target, target_centerline_filepath, output_dir):
    curvature_differential = []
    curvature_differential_max = float("-inf")
    for i in range(len(original_centerline_nodes)):
        if i == 0 or i == len(original_centerline_nodes)-1:
            continue
        original_centerline_nodes[i].calc_curvature(original_centerline_nodes)

        target_centerline_nodes[i].calc_curvature(target_centerline_nodes)
        diff = target_centerline_nodes[i].curvature - original_centerline_nodes[i].curvature
        curvature_differential.append(diff)
        if diff > curvature_differential_max:
            curvature_differential_max    = diff
            curvature_differential_max_id = i

    i0 = curvature_differential_max_id
    org = original_centerline_nodes[i0]
    tgt = target_centerline_nodes[i0]

    org.calc_circumcircle(original_centerline_nodes[i0-1], original_centerline_nodes[i0+1])
    tgt.calc_circumcircle(target_centerline_nodes[i0-1], target_centerline_nodes[i0+1])

    org_ucd = org.unit_center_dir
    tgt_ucd = tgt.unit_center_dir

    if (org_ucd is not None) and (tgt_ucd is not None):
        R1 = utility.rotation_matrix_from_A_to_B(_unit(tgt_ucd), _unit(org_ucd))
        t1 = utility.vec(org) - (R1 @ utility.vec(tgt))

##############  3点がほぼ直線の時、曲率中心への方向ベクトルが定義できない。
############## 曲率の増分が “最大” になった点IDが, originalにおいて 共線で円が作れない点(直線)だった場合
    else:
        # フォールバック：接線だけで合わせる
        # 接線は unit_center_dir が無くても計算できる
        org.calc_tangentvec(original_centerline_nodes)
        tgt.calc_tangentvec(target_centerline_nodes)

        org_tan = _unit(org.tangentvec)
        tgt_tan = _unit(tgt.tangentvec)

        if org_tan is None or tgt_tan is None:
            raise ValueError(f"tangentvec is invalid at id={i0} (cannot fallback to tangent-only)")

        R1 = utility.rotation_matrix_from_A_to_B(tgt_tan, org_tan)
        t1 = utility.vec(org) - (R1 @ utility.vec(tgt))


    target_centerline_nodes_transformed = []
    for i in range(len(original_centerline_nodes)):
        p_rot1 = R1 @ utility.vec(target_centerline_nodes[i]) + t1
        target_centerline_nodes_transformed.append(node.CenterlineNode(i, p_rot1[0], p_rot1[1], p_rot1[2]))
    # if (org_ucd is not None) and (tgt_ucd is not None) のとき: ここまでで、曲率中心方向は合っているが、接線方向にずれがある。(同一球上で2本の曲線が交差しているイメージ)
    # else: 接線方向が一致。これでalignment終了。

    # -----------------------
    # 追加の roll 補正（unit_center_dir がある場合のみ）
    # -----------------------
    if (org_ucd is not None) and (tgt_ucd is not None):
        target_centerline_nodes_transformed[i0].calc_tangentvec(target_centerline_nodes_transformed)
        org.calc_tangentvec(original_centerline_nodes)

        # 回転軸 unit_center_dir (曲線の交差点 → 球心 の方向ベクトル )が必要なので、あるときだけ呼ぶ
        # 曲線の接線が一致するまで回転させる。これにより、2つの曲線と回転軸が同一平面(coplanar)に並ぶ
        R2, theta, B_rot = utility.rotation_about_C_to_make_coplanar(
            org.tangentvec,
            target_centerline_nodes_transformed[i0].tangentvec,
            _unit(org_ucd)
        )
        P  = np.array([[nd.x, nd.y, nd.z] for nd in target_centerline_nodes_transformed], dtype=float)
        p0 = np.asarray(utility.vec(org), dtype=float).reshape(3,)
        P2 = (R2 @ (P - p0).T).T + p0

        target_centerline_nodes_transformed = [
            type(target_centerline_nodes_transformed[0])(nd.id, p[0], p[1], p[2])
            for nd, p in zip(target_centerline_nodes_transformed, P2)
        ]
    else:
        # tangent-only のときは roll は決めない（仕様通り）
        pass
    ###

    inlet_outlet_info = myio.write_csv_centerline(target_centerline_nodes_transformed,radius_list_target,target_centerline_filepath,output_dir)
    return target_centerline_nodes_transformed,inlet_outlet_info



def alignment_by_two_node_ids(
    original_centerline_nodes,
    target_centerline_nodes,
    org_id: int,
    tgt_id: int,
):
    """
    original の org_id と target の tgt_id を対応づけて位置合わせする版
    - unit_center_dir: target[tgt_id] -> original[org_id] に合わせる
    - 点: target[tgt_id] が original[org_id] に重なるように平行移動
    - tangentvec: 上記変換後の target[tgt_id] と original[org_id] を coplanar 化
    """
    n_org = len(original_centerline_nodes)
    n_tgt = len(target_centerline_nodes)

    if not (0 <= org_id < n_org):
        raise IndexError(f"org_id が範囲外です: org_id={org_id}, N_original={n_org}")
    if not (0 <= tgt_id < n_tgt):
        raise IndexError(f"tgt_id が範囲外です: tgt_id={tgt_id}, N_target={n_tgt}")

    if org_id == 0 or org_id == n_org - 1:
        raise ValueError("org_id は端点(0, N-1)以外を指定してください（i-1,i+1 が必要）")
    if tgt_id == 0 or tgt_id == n_tgt - 1:
        raise ValueError("tgt_id は端点(0, N-1)以外を指定してください（i-1,i+1 が必要）")

    # --- 1) 基準点の unit_center_dir を得る（circumcircle）
    original_centerline_nodes[org_id].calc_circumcircle(
        original_centerline_nodes[org_id - 1],
        original_centerline_nodes[org_id + 1],
    )
    target_centerline_nodes[tgt_id].calc_circumcircle(
        target_centerline_nodes[tgt_id - 1],
        target_centerline_nodes[tgt_id + 1],
    )

    # --- 2) unit_center_dir を一致させる回転（target[tgt_id] -> original[org_id]）
    R1 = utility.rotation_matrix_from_A_to_B(
        target_centerline_nodes[tgt_id].unit_center_dir,
        original_centerline_nodes[org_id].unit_center_dir,
    )

    # --- 3) 基準点が一致するよう平行移動（target[tgt_id] が original[org_id] に重なる）
    t1 = utility.vec(original_centerline_nodes[org_id]) - (R1 @ utility.vec(target_centerline_nodes[tgt_id]))

    # --- 4) 1回目の変換を全点へ適用
    target_centerline_nodes_transformed = []
    for i in range(len(target_centerline_nodes)):
        p = R1 @ utility.vec(target_centerline_nodes[i]) + t1
        target_centerline_nodes_transformed.append(node.CenterlineNode(i, p[0], p[1], p[2]))

    # --- 5) tangentvec を使って追加回転（coplanar化）
    target_centerline_nodes_transformed[tgt_id].calc_tangentvec(target_centerline_nodes_transformed)
    original_centerline_nodes[org_id].calc_tangentvec(original_centerline_nodes)

    R2, theta, B_rot = utility.rotation_about_C_to_make_coplanar(
        original_centerline_nodes[org_id].tangentvec,
        target_centerline_nodes_transformed[tgt_id].tangentvec,
        original_centerline_nodes[org_id].unit_center_dir,
    )

    # 回転中心は original[org_id] にする（=その点を固定）
    P = np.array([[nd.x, nd.y, nd.z] for nd in target_centerline_nodes_transformed], dtype=float)
    p0 = np.asarray(utility.vec(original_centerline_nodes[org_id]), dtype=float).reshape(3,)
    P_rot2 = (R2 @ (P - p0).T).T + p0

    target_centerline_nodes_transformed = [
        type(target_centerline_nodes_transformed[0])(nd.id, p[0], p[1], p[2])
        for nd, p in zip(target_centerline_nodes_transformed, P_rot2)
    ]

    return target_centerline_nodes_transformed

def write_centerline_csv(csv_path: Path, nodes, radius_list):
    """
    CSV: x,y,z,radius で保存
    """
    csv_path = Path(csv_path).resolve()
    radius_list_new=[]
    for i in range(len(radius_list)-1):
        radius_list_new.append(radius_list[i])
    if len(nodes) != len(radius_list_new):
        raise ValueError("nodes , radius_list : Length mismatch ")

    out = pd.DataFrame(
        {
            "x": [nd.x for nd in nodes],
            "y": [nd.y for nd in nodes],
            "z": [nd.z for nd in nodes],
            "radius": radius_list_new,
        }
    )
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(csv_path, index=False)

# =========================
# GUI runner
# =========================
def run_alignment_gui():
    centerline_filepath = Path(myio.select_csv("original"))
    centerline_nodes    = myio.read_original_centerline(centerline_filepath)
    target_centerline_filepath = Path(myio.select_csv("target"))
    target_centerline_nodes, radius_list_target, inlet_outlet_info   = myio.read_target_centerline(target_centerline_filepath)

    n_org = len(centerline_nodes)
    n_tgt = len(target_centerline_nodes)

    # 入力: original 側 org_id
    org_id = simpledialog.askinteger(
        "Original Node ID",
        "[Original]\n"
        "Enter the Node ID to be used as the alignment reference.\n\n"
        f"Valid range: 1 to {n_org-2}\n"
        f"(End points 0 and {n_org-1} are not allowed)",
        minvalue=1,
        maxvalue=max(1, n_org - 2),
    )
    if org_id is None:
        return

    # 入力: target 側 tgt_id
    tgt_id = simpledialog.askinteger(
        "Target Node ID",
        "[Target]\n"
        "Enter the Node ID to be used as the alignment reference.\n\n"
        f"Valid range: 1 to {n_tgt-2}\n"
        f"(End points 0 and {n_tgt-1} are not allowed)",
        minvalue=1,
        maxvalue=max(1, n_tgt - 2),
    )
    if tgt_id is None:
        return

    # 入力: 出力CSV（保存先）
    default_name = f"{target_centerline_filepath.stem}_aligned_org{org_id}_tgt{tgt_id}.csv"
    out_path = filedialog.asksaveasfilename(
        title="Select output CSV file name",
        defaultextension=".csv",
        initialfile=default_name,
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
    )
    if not out_path:
        return

    out_path = Path(out_path).resolve()

    try:
        aligned_nodes = alignment_by_two_node_ids(
            centerline_nodes,
            target_centerline_nodes,
            org_id=org_id,
            tgt_id=tgt_id,
        )

        # 半径は target のものをそのまま付与して保存
        write_centerline_csv(out_path, aligned_nodes, radius_list_target)

    except Exception as e:
        messagebox.showerror("Error",
            f"An error occurred during processing:\n\n{e}",)
        return

    
    messagebox.showinfo(
        "Completed",
        f"The aligned centerline has been saved successfully:\n\n{out_path}",
    )


if __name__ == "__main__":
    run_alignment_gui()
