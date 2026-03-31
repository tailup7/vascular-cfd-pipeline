import os
import re
import csv
import shutil
from pathlib import Path
from typing import Literal
import pandas as pd
import numpy as np
from numpy.polynomial.polynomial import Polynomial
from commonlib import node, cell, utility

class InletOutletInfo:
    def __init__(self, inlet_point, outlet_point):
        self.inlet_point   = inlet_point
        self.outlet_point  = outlet_point
    def add_radius_info(self, inlet_radius, outlet_radius):
        self.inlet_radius  = inlet_radius
        self.outlet_radius = outlet_radius

# get absolute path of input centerline (*.csv)
def select_csv(message):
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw() 
    root.attributes("-topmost", True)
    filepath  = filedialog.askopenfilename(
        title     = f"Select {message} centerline file (*.csv)",
        filetypes = [("CSV files", "*.csv")], 
        parent    = root
    )
    root.destroy()
    return filepath

# get absolute path of input stl
def select_stl():
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)  
    filepath = filedialog.askopenfilename(
        title     = "Select surface file",
        filetypes = [("stl files", "*.stl")],  
        parent    = root
    )
    root.destroy()
    return filepath

# 絶対パスの取得
def select_vtk():
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)  
    filepath = filedialog.askopenfilename(
        title     = "Select surface vtk file",
        filetypes = [("vtk files", "*.vtk")],
        parent    = root  
    )
    root.destroy()
    return filepath

# 絶対パスの取得
def select_msh():
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)  
    filepath = filedialog.askopenfilename(
        title     = "Select original msh file",
        filetypes = [("msh files", "*.msh")],
        parent    = root  
    )
    root.destroy()
    return filepath

# TODO: original と targetで中心線の点数が違う時にerror出すように
def read_original_centerline(filepath):
    df = pd.read_csv(filepath)
    centerline_nodes    = [node.CenterlineNode(index, row['x'], row['y'], row['z']) for index, row in df.iterrows()]
    return centerline_nodes

# TODO: original と targetで中心線の点数が違う時にerror出すように
def read_target_centerline(filepath):
    df = pd.read_csv(filepath)
    centerline_nodes    = [node.CenterlineNode(index, row['x'], row['y'], row['z']) for index, row in df.iterrows()]
    inlet_outlet_info   = InletOutletInfo(centerline_nodes[0], centerline_nodes[-1])
    # radius_listの総数を、【点群の数+1】 にする
    if "radius" in df.columns:
        radius_list = df["radius"].tolist()
        last_x = np.array([len(radius_list)-3, len(radius_list)-2, len(radius_list)-1])
        last_y = radius_list[-3:]
        polynominal_func = Polynomial.fit(last_x, last_y, 1)
        additional_radius = polynominal_func(len(radius_list))
        radius_list.append(additional_radius)
        inlet_outlet_info.add_radius_info(radius_list[0], radius_list[-1])
        expansion_list = None
    elif "expansion" in df.columns:
        expansion_list = df["expansion"].tolist()
        last_x = np.array([len(expansion_list)-3, len(expansion_list)-2, len(expansion_list)-1])
        last_y = expansion_list[-3:]
        polynominal_func = Polynomial.fit(last_x, last_y, 1)
        additional_expansion = polynominal_func(len(expansion_list))
        expansion_list.append(additional_expansion)
        radius_list=None
    else:
        radius_list    = None
        expansion_list = None
    return centerline_nodes, radius_list, inlet_outlet_info, expansion_list

def read_msh_tetra(filepath):
    tetra_list = []
    with open(filepath, 'r') as file:
        lines = file.readlines()
        for line in lines:
            columns = line.split()
            if len(columns) == 9 and columns[1] == '4':
                tetra = [int(columns[i]) for i in range(5, 9)]
                tetra_list.append(tetra)
    print("info_myio    : num of tetra is",len(tetra_list))
    return tetra_list

def write_csv_radius(radius_list, filename, output_dir):
    filepath = output_dir / f"{filename}_radius.csv"
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        f.write("radius\n") 
        for i in range(len(radius_list)):
            f.write(f"{radius_list[i]}\n")

def write_pos_bgm(tetra_list,nodeany_dict,filename, output_dir):
    filepath = str(output_dir / f"bgm_{filename}.pos")
    with open(filepath, 'w') as f:
        f.write('View "background mesh" {\n')
        coords_list=[]
        scalars_list=[]
        for tetra in tetra_list:
            coords=[]
            scalars=[]
            for i in range(len(tetra)):
                coords.append(nodeany_dict[tetra[i]].x)
                coords.append(nodeany_dict[tetra[i]].y)
                coords.append(nodeany_dict[tetra[i]].z)
                scalars.append(nodeany_dict[tetra[i]].scalar_forbgm)
            coords_list.append(coords)
            scalars_list.append(scalars)
        for i in range(len(tetra_list)):
            c = coords_list[i]
            s = scalars_list[i]
            f.write(f"SS({c[0]},{c[1]},{c[2]},{c[3]},{c[4]},{c[5]},{c[6]},{c[7]},{c[8]},{c[9]},{c[10]},{c[11]})"
                    f"{{{s[0]:.2f},{s[1]:.2f},{s[2]:.2f},{s[3]:.2f}}};\n")
        f.write('};')
    print(f"output bgm_{filename}.pos")

def rewrite_pos_bgm_for_tetra(filename, config, output_dir):
    input_pos_path  = output_dir / f"bgm_{filename}.pos"
    output_pos_path = output_dir / f"bgm_{filename}_for_tetra.pos"
    # SS(...) { ... }; を検出する正規表現
    pattern = re.compile(
        r'(SS\s*\([^)]*\)\s*\{)([^}]*)\}(;)'
    )
    with open(input_pos_path, 'r') as fin, open(output_pos_path, 'w') as fout:
        for line in fin:
            match = pattern.search(line)
            if match:
                prefix = match.group(1)   # SS(...) {
                scalar_str = match.group(2)  # s0,s1,s2,s3
                suffix = match.group(3)   # ;
                # スカラーを float に変換
                scalars = [float(x) for x in scalar_str.split(',')]
                # 定数倍
                scaled_scalars = [s * config.TETRA_SCALING for s in scalars]
                # フォーマットを揃えて書き戻す
                new_scalar_str = ",".join(f"{s:.2f}" for s in scaled_scalars)
                new_line = f"{prefix}{new_scalar_str}}}{suffix}\n"
                fout.write(new_line)
            else:
                # View 行や }; 行などはそのまま
                fout.write(line)
    print(f"scaled pos file written to: {output_pos_path}")
    return output_pos_path

def write_csv_centerline(centerline_nodes,radius_list,filepath,output_dir):
    out_dir = Path(output_dir)
    input_dir = out_dir / "inputs"
    input_dir.mkdir(parents=True, exist_ok=True)
    path = Path(filepath)
    new_filename = f"{path.stem}_transformed{path.suffix}"
    out_path = input_dir / new_filename

    has_radius = radius_list is not None
    header = ["x", "y", "z"] + (["radius"] if has_radius else [])
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for i, nd in enumerate(centerline_nodes):
            row = [nd.x, nd.y, nd.z]
            if has_radius:
                row.append(radius_list[i])
            writer.writerow(row)
    print(f"[OK] wrote: {out_path}")
    inlet_outlet_info   = InletOutletInfo(centerline_nodes[0], centerline_nodes[-1])
    if has_radius:
        inlet_outlet_info.add_radius_info(radius_list[0], radius_list[-1])
    return inlet_outlet_info

# vtk の file formatでは node番号は0スタートだが、gmsh のmesh format 2.2 0 8 は1スタートで、コード内では gmsh に合わせて node_idを1スタートにする
def read_vtk_surfacemesh(filepath_vtk):
    with open(filepath_vtk, 'r') as file:
        lines = file.readlines()
    points_section = False
    cells_section = False

    for line in lines:
        line = line.strip()
        if line.startswith("POINTS"):
            points_section = True
            node_id=1
            surface_node_dict = {}
            surface_nodes = []
            continue
        if line.startswith("CELLS"):
            points_section = False
            cells_section = True
            triangle_id=1   
            surface_triangles = []
            continue

        if points_section:
            if not line: # 「行が空なら」
                points_section = False
                continue
            coords = list(map(float, line.split()))
            x=coords[0]
            y=coords[1]
            z=coords[2]
            surface_node=node.NodeAny(node_id,x,y,z)
            # vtk形式ではnodeIDは0スタートだが、本コード内では1スタートにしているので id+1 をキーとして辞書作成 
            surface_node_dict[node_id]= surface_node
            surface_nodes.append(surface_node)
            node_id+=1
        if cells_section:
            if not line: # 「行が空なら」
                cells_section = False
                continue
            cell_data = list(map(int, line.split()))
            if cell_data[0] == 3:
                node0 = surface_node_dict[cell_data[1]+1]
                node1 = surface_node_dict[cell_data[2]+1]
                node2 = surface_node_dict[cell_data[3]+1]
                surface_triangle = cell.Triangle(triangle_id, node0, node1, node2)
                v0 = np.array([node1.x - node0.x, node1.y - node0.y, node1.z - node0.z ])
                v1 = np.array([node2.x - node0.x, node2.y - node0.y, node2.z - node0.z ])
                normal = np.cross(v0, v1)
                unit_normal = normal / np.linalg.norm(normal)
                surface_triangle.unitnormal_out = unit_normal
                surface_triangle.unitnormal_in  = - unit_normal
                surface_triangles.append(surface_triangle)
                triangle_id += 1
    print("info_myio    : num of outersurface points is ",node_id-1)
    print("info_myio    : num of outersurface triangles is ",triangle_id-1)
    
    return surface_nodes,surface_triangles

def read_msh_original_WALL(filepath_msh, mesh):
    """
    Gmsh v2 ASCII .msh を読み込んで、
    - PhysicalName "WALL" の三角形要素だけを抽出し
    - それに登場するノードだけで NodeAny / Triangle を作る。

    戻り値:
        surface_nodes, surface_triangles
    """
    # 1. まず PhysicalNames から "WALL" の physical ID を探す
    wall_physical_id = None

    with Path(filepath_msh).open("r") as f:
        lines = f.readlines()

    i = 0
    n_lines = len(lines)

    while i < n_lines:
        line = lines[i].strip()
        if line == "$PhysicalNames":
            i += 1
            n_phys = int(lines[i].strip())
            i += 1
            for _ in range(n_phys):
                parts = lines[i].strip().split()
                dim = int(parts[0])
                phys_id = int(parts[1])
                name = " ".join(parts[2:]).strip('"')
                if dim == 2 and name == "WALL":
                    wall_physical_id = phys_id
                i += 1
        else:
            i += 1

    if wall_physical_id is None:
        raise RuntimeError('PhysicalName "WALL" が見つかりませんでした。')

    i = 0
    allnode_dict = {}
    while i < n_lines:
        line = lines[i].strip()
        if line == "$Nodes":
            i += 1
            n_nodes = int(lines[i].strip())
            i += 1
            for _ in range(n_nodes):
                parts = lines[i].strip().split()
                nid = int(parts[0])
                x   = float(parts[1])
                y   = float(parts[2])
                z   = float(parts[3])
                allnode = node.NodeAny(nid,x,y,z)
                allnode_dict[nid] = allnode
                i += 1
        else:
            i += 1

    # 3. Elements セクションから WALL の三角形(type=2)だけ抜き出す
    i = 0
    surface_nodes = []
    surface_triangles = [] 
    while i < n_lines:
        line = lines[i].strip()
        if line == "$Elements":
            i += 1
            n_elems = int(lines[i].strip())
            i += 1
            surface_node_dict = {}
            for _ in range(n_elems):
                parts = lines[i].strip().split()
                elem_id = int(parts[0])     # elementのID
                elem_type = int(parts[1])   # 2(三角形),3(四角形),4(テトラ), 6(プリズム) のいずれか
                num_tags = int(parts[2])    # 後ろに続く情報の数。通常はphysicalname と geometryIDの2つなので 2の固定値         
                tags = list(map(int, parts[3:3+num_tags]))
                node_ids = list(map(int, parts[3+num_tags:]))

                # Gmsh v2: tags[0] が physical ID
                if elem_type == 2 and tags[0] == wall_physical_id:
                    # 三角形でかつ WALL のものだけを保持
                    if len(node_ids) != 3:
                        raise RuntimeError("三角形なのにノード数が3ではありません。")
                    node0_id = node_ids[0]
                    node1_id = node_ids[1]
                    node2_id = node_ids[2]
                    surface_triangle = cell.Triangle(elem_id, allnode_dict[node0_id],allnode_dict[node1_id], allnode_dict[node2_id])
                    for nid in (node0_id, node1_id, node2_id):
                        if nid not in surface_node_dict:
                            surface_node_dict[nid] = allnode_dict[nid]
                    v0 = np.array([allnode_dict[node1_id].x - allnode_dict[node0_id].x, 
                                    allnode_dict[node1_id].y - allnode_dict[node0_id].y, 
                                    allnode_dict[node1_id].z - allnode_dict[node0_id].z ])
                    v1 = np.array([allnode_dict[node2_id].x - allnode_dict[node0_id].x, 
                                    allnode_dict[node2_id].y - allnode_dict[node0_id].y, 
                                    allnode_dict[node2_id].z - allnode_dict[node0_id].z ])
                    normal = np.cross(v0, v1)
                    unit_normal = normal / np.linalg.norm(normal)
                    surface_triangle.unitnormal_out = unit_normal
                    surface_triangle.unitnormal_in  = - unit_normal
                    surface_triangles.append(surface_triangle)
                i += 1
            surface_nodes = [surface_node_dict[nid] for nid in sorted(surface_node_dict.keys())]
        else:
            i += 1
    mesh.num_of_surfacenodes     = len(surface_nodes)
    mesh.num_of_surfacetriangles = len(surface_triangles)
    return surface_nodes, surface_triangles

def write_stl_innersurface(mesh,layernode_dict,config,output_dir):
    filename = "innersurface_" + str(config.NUM_OF_LAYERS) + ".stl"
    filepath = str( output_dir / filename)
    start = mesh.num_of_surfacetriangles*(config.NUM_OF_LAYERS-1)
    end   = mesh.num_of_surfacetriangles*config.NUM_OF_LAYERS -1
    triangle_list=[]
    for i in range(start,end+1):
        id0 = mesh.prisms_INTERNAL[i].id0
        id1 = mesh.prisms_INTERNAL[i].id1
        id2 = mesh.prisms_INTERNAL[i].id2
        node0 = layernode_dict[id0]
        node1 = layernode_dict[id1]
        node2 = layernode_dict[id2]
        triangle = cell.Triangle(i, node0, node1, node2)
        triangle.calc_unitnormal()
        triangle_list.append(triangle)
    with open(filepath, 'w') as f:
        f.write("solid model\n")
        for triangle in triangle_list:
            f.write(f"  facet normal {triangle.unitnormal_out[0]} {triangle.unitnormal_out[1]} {triangle.unitnormal_out[2]}\n")
            f.write("    outer loop\n")
            f.write(f"      vertex {triangle.node0.x} {triangle.node0.y} {triangle.node0.z}\n")
            f.write(f"      vertex {triangle.node1.x} {triangle.node1.y} {triangle.node1.z}\n")
            f.write(f"      vertex {triangle.node2.x} {triangle.node2.y} {triangle.node2.z}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")
        f.write("endsolid model\n")
    return filepath

def write_stl_surfacetriangles(surface_triangles,filename, output_dir):
    filepath = str(output_dir / filename)
    with open(filepath, 'w') as f:
        f.write("solid model\n")
        for triangle in surface_triangles:
            f.write(f"  facet normal {triangle.unitnormal_out[0]} {triangle.unitnormal_out[1]} {triangle.unitnormal_out[2]}\n")
            f.write("    outer loop\n")
            f.write(f"      vertex {triangle.node0.x} {triangle.node0.y} {triangle.node0.z}\n")
            f.write(f"      vertex {triangle.node1.x} {triangle.node1.y} {triangle.node1.z}\n")
            f.write(f"      vertex {triangle.node2.x} {triangle.node2.y} {triangle.node2.z}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")
        f.write("endsolid model\n")
    return filepath

def write_vtk_surfacemesh_with_ccnID(surface_nodes,surface_triangles, message, output_dir):
    filepath=output_dir / f"surfacemesh_{message}_with_ccnID.vtk"
    point_header=f"""# vtk DataFile Version 2.0
WALL_0, Created by Gmsh 4.11.1 
ASCII
DATASET UNSTRUCTURED_GRID
POINTS {len(surface_nodes)} double\n"""
    cell_header=f"""CELLS {len(surface_triangles)} {4*len(surface_triangles)}\n"""
    celltypes_header = f"""CELL_TYPES {len(surface_triangles)}\n"""
    celldata_header=f"""CELL_DATA {len(surface_triangles)}
SCALARS ccnID float 1
LOOKUP_TABLE default\n"""
    
    with open(filepath, "w") as f:
        f.write(point_header)
        for pt in surface_nodes:
            f.write(f"{pt.x} {pt.y} {pt.z}\n")
        f.write(cell_header)
        for tri in surface_triangles:
            # コード内ではnodeのIDは1スタートにしているので、vtk形式(0スタート)に合わせる
            f.write(f"3 {tri.node0.id-1} {tri.node1.id-1} {tri.node2.id-1}\n")
        f.write(celltypes_header)
        for tri in surface_triangles:
            f.write("5\n")
        f.write(celldata_header)
        for tri in surface_triangles:
            # コード内では、中心線NodeのIDは0スタート
            f.write(f"{tri.correspond_centerlinenode.id}\n")

def read_msh_innermesh(filepath,mesh,config):
    node_innermesh_dict={}
    nodesid_composing_innerwalltriangle=set()
    nodesid_composing_inlettriangle=set()
    nodesid_composing_outlettriangle=set()
    triangle_inlet_list=[]
    triangle_outlet_list=[]
    tetra_list=[]

    with open(filepath, "r") as file:
        lines = file.readlines()

    node_section = False
    skip_next_line_n = False
    skip_next_line_e=False
    element_section = False

    for i, line in enumerate(lines):
        line = line.strip()

        if line.startswith("$Nodes"):
            node_section = True
            skip_next_line_n = True 
            continue

        if skip_next_line_n:
            skip_next_line_n = False  
            mesh.num_of_innermeshnodes=int(line)
            continue

        if line.startswith("$EndNodes"):
            node_section = False
            continue

        if node_section:
            parts = line.split()
            if len(parts) < 4:
                continue  
            
            node_id = int(parts[0])
            x, y, z = map(float, parts[1:4])
            node_innermesh = node.NodeAny(node_id, x, y, z) 
            node_innermesh_dict[node_id]=node_innermesh

        if line.startswith("$Elements"):
            element_section = True
            skip_next_line_e = True  
            continue
        if skip_next_line_e:
            skip_next_line_e = False
            continue
        if line.startswith("$EndElements"):
            element_section = False
            continue

        if element_section:
            parts = line.split()
            if len(parts) < 5:
                continue 

            elem_id = int(parts[0])  # 要素ID
            elem_type = int(parts[1])  # 要素のタイプ
            physical_group = int(parts[3])  # physical number（4列目）

            if  elem_type == 2: 
                node0 = node_innermesh_dict[int(parts[-3])]
                node1 = node_innermesh_dict[int(parts[-2])]
                node2 = node_innermesh_dict[int(parts[-1])]

                if physical_group == 99 :
                    nodesid_composing_innerwalltriangle.update(map(int, parts[-3:])) #除外にもこれを使える

                elif physical_group == 20:
                    triangle_inlet = cell.Triangle(elem_id, node0, node1, node2)
                    nodesid_composing_inlettriangle.update(map(int, parts[-3:])) 
                    triangle_inlet_list.append(triangle_inlet)

                elif physical_group == 30:
                    triangle_outlet = cell.Triangle(elem_id, node0, node1, node2)
                    nodesid_composing_outlettriangle.update(map(int, parts[-3:]))
                    triangle_outlet_list.append(triangle_outlet)

            if  elem_type == 4: 
                id0 = int(parts[-4])
                id1 = int(parts[-3])
                id2 = int(parts[-2])
                id3 = int(parts[-1])
                tetra = cell.Tetra(id0,id1,id2,id3)
                tetra_list.append(tetra)

# 既存の最深層とinnerwalltriangleを重ね合わせ、辞書を作る
    nodes_mostinner=[]
    start = mesh.num_of_surfacenodes*config.NUM_OF_LAYERS
    end   = mesh.num_of_surfacenodes*(config.NUM_OF_LAYERS+1)-1
    for i in range(start,end+1):
        nodes_mostinner.append(mesh.nodes[i])
    nodes_innerwalltriangle=[]
    for nodeid in nodesid_composing_innerwalltriangle:
        nodes_innerwalltriangle.append(node_innermesh_dict[nodeid])
    nearestpairs = utility.find_nearest_neighbors(nodes_innerwalltriangle,nodes_mostinner)
    nodes_innerwall_dict={}
    cumulative_error=0
    for i in range(len(nearestpairs)):
        nodes_innerwall_dict[nearestpairs[i][0].id] = nearestpairs[i][1]
        cumulative_error+=nearestpairs[i][2]
    print("cumulative error is",cumulative_error)

    # 99(innerwall)と20or30(端面)を構成するNodeはboundaryNodeとして抽出する
    nodesid_on_inlet_boundaryedge = nodesid_composing_innerwalltriangle & nodesid_composing_inlettriangle
    nodesid_on_outlet_boundaryedge= nodesid_composing_innerwalltriangle & nodesid_composing_outlettriangle
    print("num of nodesid_composing_innerwalltriangle is ",len(nodesid_composing_innerwalltriangle))
    print("num of nodesid_on_inlet_boundaryedge is ",len(nodesid_on_inlet_boundaryedge))
    for nodeid in nodesid_on_inlet_boundaryedge:
        nodes_innerwall_dict[nodeid].on_inlet_boundaryedge = True
    for nodeid in nodesid_on_outlet_boundaryedge:
        nodes_innerwall_dict[nodeid].on_outlet_boundaryedge = True

    # node id を書き換え,mesh info に追加
    node_countor=1
    for i in range(1,mesh.num_of_innermeshnodes+1):
        if i in nodesid_composing_innerwalltriangle:
            node_innermesh_dict[i].id = nodes_innerwall_dict[i].id
            continue
        node_innermesh_dict[i].id = node_countor+mesh.num_of_boundarylayernodes
        mesh.nodes.append(node_innermesh_dict[i])
        mesh.num_of_nodes += 1
        node_countor += 1

    # element情報をmesh infoに追加
    for triangle in triangle_inlet_list:
        triangle.id = mesh.num_of_elements + 1
        mesh.triangles_INLET.append(triangle)
        mesh.num_of_elements+=1
    for triangle in triangle_outlet_list:
        triangle.id = mesh.num_of_elements + 1
        mesh.triangles_OUTLET.append(triangle)
        mesh.num_of_elements+=1
    for tetra in tetra_list:
        tetra.id0=node_innermesh_dict[tetra.id0].id
        tetra.id1=node_innermesh_dict[tetra.id1].id
        tetra.id2=node_innermesh_dict[tetra.id2].id
        tetra.id3=node_innermesh_dict[tetra.id3].id
        mesh.tetras_INTERNAL.append(tetra)
        mesh.num_of_elements+=1

def write_msh_allmesh(mesh,filename,output_dir):
    filepath = str(output_dir / f"{filename}_mesh.msh")
    with open(filepath, "w") as f:
        # $MeshFormat 
        f.write("$MeshFormat\n")
        f.write("2.2 0 8\n")
        f.write("$EndMeshFormat\n")
        f.write("$PhysicalNames\n")
        f.write("4\n")  
        f.write("2 10 \"WALL\"\n")
        f.write("2 20 \"INLET\"\n")
        f.write("2 30 \"OUTLET\"\n")
        f.write("3 100 \"INTERNAL\"\n")
        f.write("$EndPhysicalNames\n")
        # $Nodes 
        f.write("$Nodes\n")
        f.write(f"{mesh.num_of_nodes}\n")  
        nodes_sorted = sorted(mesh.nodes, key=lambda obj: obj.id)   # mesh.nodesを、idの昇順に並べ替える
        for node in nodes_sorted:
                f.write(f"{node.id} {node.x} {node.y} {node.z}\n")
        f.write("$EndNodes\n")
        # elements
        f.write("$Elements\n")
        f.write(f"{mesh.num_of_elements}\n")
        elements_countor=0
        for triangle in mesh.triangles_WALL:
            f.write(f"{triangle.id} 2 2 10 10 {triangle.node0.id} {triangle.node1.id} {triangle.node2.id}\n")
            elements_countor+=1

        for triangle in mesh.triangles_INLET:
            elements_countor+=1
            f.write(f"{elements_countor} 2 2 20 11 {triangle.node0.id} {triangle.node1.id} {triangle.node2.id}\n")
        for triangle in mesh.triangles_OUTLET:
            elements_countor+=1
            f.write(f"{elements_countor} 2 2 30 13 {triangle.node0.id} {triangle.node1.id} {triangle.node2.id}\n")
        for quad in mesh.quadrangles_INLET:
            elements_countor+=1
            f.write(f"{elements_countor} 3 2 20 12 {quad.id0} {quad.id1} {quad.id2} {quad.id3}\n")
        for quad in mesh.quadrangles_OUTLET:
            elements_countor+=1
            f.write(f"{elements_countor} 3 2 30 14 {quad.id0} {quad.id1} {quad.id2} {quad.id3}\n")
        for tetra in mesh.tetras_INTERNAL:
            elements_countor+=1
            f.write(f"{elements_countor} 4 2 100 1 {tetra.id0} {tetra.id1} {tetra.id2} {tetra.id3}\n")
        for prism in mesh.prisms_INTERNAL:
            elements_countor+=1
            f.write(f"{elements_countor} 6 2 100 1 {prism.id0} {prism.id1} {prism.id2} {prism.id3} {prism.id4} {prism.id5}\n")
        f.write("$EndElements\n")

def copy_files_to_dir(
    *src_files: str | Path,
    output_dir: str | Path,
    meshing_or_deform: Literal["meshing", "deform"],
    overwrite: bool = False,
    keep_metadata: bool = True,
    ) :
    """
    複数のファイル（2個・3個など）を、指定フォルダにコピーする。
    Parameters
    ----------
    *src_files : str | Path
        コピー元ファイルの絶対パス（2個でも3個でも可）
    output_dir : str | Path

    overwrite : bool
        True の場合、同名ファイルがあれば上書き
    keep_metadata : bool
        True の場合、メタデータを保持（shutil.copy2）
    Returns
    -------
    list[Path]
        コピーされたファイルのパス一覧
    """
    # 入力ファイルを runs / <case> / inputs にコピーする
    if len(src_files) < 2:
        raise ValueError("please select src_files more than two.")
    out = Path(output_dir).expanduser().resolve()
    dst = out / "inputs"
    dst.mkdir(parents=True, exist_ok=True)
    copier = shutil.copy2 if keep_metadata else shutil.copy
    for src_file in src_files:
        src = Path(src_file).expanduser().resolve()
        if not src.is_file():
            raise FileNotFoundError(f"the file doesn't exist : {src}")
        dst_file = dst / src.name
        if dst_file.exists() and not overwrite:
            raise FileExistsError(f"same name file already exists: {dst_file}")
        copier(src, dst_file)
    # config.py ファイルを runs / <case> にコピーする
    THIS_FILEPATH = Path(__file__).resolve()
    SRC_DIR       = THIS_FILEPATH.parent.parent
    if meshing_or_deform == "meshing":
        CONFIG_FILEPATH = SRC_DIR / "meshing" / "config.py"
    elif meshing_or_deform == "deform":
        CONFIG_FILEPATH = SRC_DIR / "deform" / "config.py"
    else:
        raise ValueError(f"invalid meshing_or_deform: {meshing_or_deform!r}")
    if not CONFIG_FILEPATH.is_file():
        raise FileNotFoundError(f"config.py not found: {CONFIG_FILEPATH}")
    dst_config = out / "config.py"
    copier(CONFIG_FILEPATH, dst_config)
