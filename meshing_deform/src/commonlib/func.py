import commonlib.node as node
import commonlib.myio as myio
import commonlib.boundarylayer as boundarylayer
import deform.smooth.edgeswap as edgeswap
import deform.smooth.smoother_vtk as smoother_vtk
import gmsh
import os
import numpy as np
import sys
import trimesh
import commonlib.utility as utility
import commonlib.cell as cell

class PairDict:
    def __init__(self):
        self.pair_dict = {}

    def _normalize_pair(self, a, b):
        return tuple(sorted((a, b)))  

    def add_pair(self, a, b, value):
        self.pair_dict[self._normalize_pair(a, b)] = value

    def remove_pair(self, a, b):
        key = self._normalize_pair(a, b)
        if key in self.pair_dict:
            del self.pair_dict[key]

    def get_value(self, a, b):
        return self.pair_dict.get(self._normalize_pair(a, b))

# この関数は消す、使わないようにする。代わりにvmtkで出力される最大内接球の半径を使う
def calc_radius(stl_filepath, centerline_nodes, inlet_outlet_info,config, output_dir):
    # 半径計算のため、読み込んだ表面形状を細かく再メッシュ
    try:
        if not gmsh.isInitialized():
            gmsh.initialize()
        path = os.path.dirname(os.path.abspath(__file__))
        gmsh.merge(os.path.join(path, stl_filepath)) 
        gmsh.model.mesh.classifySurfaces(angle = 40 * np.pi / 180, boundary=True, forReparametrization=True)
        gmsh.model.mesh.createGeometry()
        gmsh.model.geo.synchronize()
        gmsh.option.setNumber("Mesh.OptimizeNetgen", 1)
        gmsh.option.setNumber("Mesh.OptimizeThreshold", 0.9)
        gmsh.option.setNumber('Mesh.Algorithm', 1)
        gmsh.option.setNumber("Mesh.MeshSizeMin", config.MESHSIZE*0.5)
        gmsh.option.setNumber("Mesh.MeshSizeMax", config.MESHSIZE*0.5)
        gmsh.model.mesh.generate(2)

        stl_filepath = str( output_dir / f"for_calculate_radius.stl" )
        gmsh.write(stl_filepath)

        mesh = trimesh.load_mesh(stl_filepath)
        vertices = mesh.vertices 
        unique_nodes = np.unique(vertices, axis=0)
        surface_nodes = unique_nodes.tolist()

        radius_list=[]
        countor=[]    
        radius_list_smooth = []
        for i in range(len(centerline_nodes)+1):
            radius_list.append(0.0)
            countor.append(0)
            radius_list_smooth.append(0.0)

        for i in range(len(surface_nodes)):
            surface_node=node.NodeAny(i,surface_nodes[i][0],surface_nodes[i][1],surface_nodes[i][2])
            surface_node.find_closest_centerlinenode(centerline_nodes)
            surface_node.find_projectable_centerlineedge(centerline_nodes)
            if surface_node.projectable_centerlineedge_id != None:
                radius_list[surface_node.projectable_centerlineedge_id+1] += surface_node.projectable_centerlineedge_distance
                countor[surface_node.projectable_centerlineedge_id+1]+=1
            else:
                if surface_node.closest_centerlinenode_id==0:
                    radius_list[0] += utility.calculate_PH_length(surface_node,centerline_nodes[0],centerline_nodes[1])
                    countor[0] += 1
                elif surface_node.closest_centerlinenode_id==len(centerline_nodes)-1:
                    radius_list[len(centerline_nodes)] += utility.calculate_PH_length(surface_node,centerline_nodes[-2],centerline_nodes[-1])
                    countor[len(centerline_nodes)] += 1
                else:
                    radius_list[surface_node.closest_centerlinenode_id]+=surface_node.closest_centerlinenode_distance
                    countor[surface_node.closest_centerlinenode_id] += 1
                    radius_list[surface_node.closest_centerlinenode_id+1]+=surface_node.closest_centerlinenode_distance
                    countor[surface_node.closest_centerlinenode_id+1] += 1

        for i in range(len(radius_list)):
            if countor[i]!=0:
                radius_list[i] /= countor[i]

        radius_list_smooth[0]  = (radius_list[0]+radius_list[1])/2
        radius_list_smooth[-1] = (radius_list[-1]+radius_list[-2])/2
        for i in range(1,len(radius_list)-1):
            radius_list_smooth[i] = (radius_list[i-1]+radius_list[i]+radius_list[i+1])/3

        inlet_outlet_info.add_radius_info(radius_list_smooth[0], radius_list_smooth[-1])

    finally:
        if gmsh.isInitialized():
            gmsh.finalize()

    return radius_list_smooth

# generate background mesh
def generate_pos_bgm(filepath, centerline_nodes,radius_list,filename, classify_parameter, config, output_dir):
    try :
        if not gmsh.isInitialized():
            gmsh.initialize()
        gmsh.merge(filepath)  
        # ここのclassifySurface関数の1つ目の引数が 通常の感覚と逆なので注意。値が大きいほど、判定が厳しくなる。
        # classify_parameter の値を小さく設定するほど、三角形パッチの法線同士の成す角が大きくても、連続する面とみなす。
        gmsh.model.mesh.classifySurfaces(angle = classify_parameter * np.pi / 180, boundary=True, forReparametrization=True)
        gmsh.model.mesh.createGeometry()
        gmsh.model.geo.synchronize()
        # メッシュオプション
        gmsh.option.setNumber("Mesh.OptimizeNetgen", 1)
        gmsh.option.setNumber("Mesh.OptimizeThreshold", 0.9)
        gmsh.option.setNumber('Mesh.Algorithm', 1)
        gmsh.option.setNumber("Mesh.MeshSizeMin", config.MESHSIZE)
        gmsh.option.setNumber("Mesh.MeshSizeMax", config.MESHSIZE)
        wall = gmsh.model.getEntities(2)
        gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
        wall_id = [e[1] for e in wall]
        print("wall=",wall)
        print("wall_id=",wall_id)

        boundary_curv = gmsh.model.getBoundary(wall)
        print("1D entities which make boundary_curv are",boundary_curv)
        boundary_curv_id = [e[1] for e in boundary_curv]
        print("IDs of 1D entities which make boundary_curv are ",boundary_curv_id)

        boundary_curv_id_list = gmsh.model.geo.addCurveLoops(boundary_curv_id)
        print("Remake curve loops . These IDs are ",boundary_curv_id_list)

        for i in boundary_curv_id_list:
            a=gmsh.model.geo.addPlaneSurface([i])
        print("Curve loops makes closed plane surface. IDs of plane surfaces are",a)

        gmsh.model.geo.synchronize()  
        check = gmsh.model.getEntities(2)
        print(check)
        surfaceAll_id = [e[1] for e in check]
        print("All 2D surface entities IDs are ",surfaceAll_id)
        surfaceLoop = gmsh.model.geo.addSurfaceLoop(surfaceAll_id)
        gmsh.model.geo.addVolume([surfaceLoop])
        gmsh.model.geo.synchronize()  
        gmsh.model.mesh.generate(3) 
        nodeids, coords, _ = gmsh.model.mesh.getNodes()
        nodes_any=node.coords_to_nodes(nodeids,coords)

        vtk_file = str( output_dir / f"bgm_{filename}.vtk" )
        msh_file = str( output_dir / f"bgm_{filename}.msh" )
        gmsh.write(vtk_file)                  
        gmsh.write(msh_file)                  
        print(f"output bgm_{filename}.vtk")   
        print(f"output bgm_{filename}.msh")   

        nodeany_dict={}                                          
        for node_any in nodes_any:
            nodeany_dict[node_any.id] = node_any  
            node_any.find_closest_centerlinenode(centerline_nodes)
            node_any.find_projectable_centerlineedge(centerline_nodes)
            node_any.set_edgeradius(radius_list, config)
        tetra_list   = myio.read_msh_tetra(msh_file)
        myio.write_pos_bgm(tetra_list,nodeany_dict,filename, output_dir) 
    finally:
        if gmsh.isInitialized():
            gmsh.finalize()

def make_surfacemesh(stl_filepath, mesh, filename, output_dir):  
    try:
        if not gmsh.isInitialized():
            gmsh.initialize()
        gmsh.merge(stl_filepath)
        gmsh.model.mesh.classifySurfaces(angle = 40 * np.pi / 180, boundary=True, forReparametrization=True)
        gmsh.model.mesh.createGeometry()
        gmsh.model.geo.synchronize()
        gmsh.option.setNumber("Mesh.OptimizeThreshold", 0.9)
        gmsh.option.setNumber('Mesh.Algorithm', 1)
        gmsh.option.setNumber("Mesh.Optimize", 10)
    
        filepath_pos = str(output_dir / "bgm_original.pos")
        gmsh.merge(filepath_pos)             
        bg_field = gmsh.model.mesh.field.add("PostView")    
        gmsh.model.mesh.field.setNumber(bg_field, "ViewIndex", 0) 
        gmsh.model.mesh.field.setAsBackgroundMesh(bg_field) 
        gmsh.model.geo.synchronize()
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)      
        gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)     
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    
        gmsh.model.mesh.generate(2)
        gmsh.model.mesh.optimize()
    
        output_vtk_filepath = str(output_dir / f"surfacemesh_{filename}.vtk")
        output_stl_filepath = str(output_dir / f"surfacemesh_{filename}.stl")
        gmsh.write(output_vtk_filepath)
        gmsh.write(output_stl_filepath)
        print(f"output surfacemesh_{filename}.vtk")
        print(f"output surfacemesh_{filename}.stl")
        surface_nodes,surface_triangles = myio.read_vtk_surfacemesh(output_vtk_filepath)    
        for surface_node in surface_nodes:
            mesh.nodes.append(surface_node)
            mesh.num_of_nodes += 1
        mesh.num_of_surfacenodes = len(surface_nodes)
        for surface_triangle in surface_triangles:
            mesh.triangles_WALL.append(surface_triangle)
            mesh.num_of_elements += 1
        mesh.num_of_surfacetriangles = len(surface_triangles)
    finally:
        if gmsh.isInitialized():
            gmsh.finalize()
    return surface_nodes, surface_triangles

# 表面triangleの重心から見て、最近接する中心線nodeを探して対応付け
# さらに表面nodeから見て、表面node → その表面nodeを頂点に持つ表面triangle → その表面triangleと対応する中心線node 
# として、表面node → 中心線node (1 → N) の対応付けをする
def map_surfacenode_to_centerlinenodes(surface_triangles, centerline_nodes):
    print("info_func    : start corresponding surface mesh triangles to centerline nodes") 
    for surface_triangle in surface_triangles:
        # vtkファイルは、三角形の頂点の記述順が反時計回りになっており、法線ベクトルの向きは暗示的に示されている。
        # gmsh は そのルールを守ってvtkを出力してくれるので、stlを読み込んで中心線情報も使いながら自分で法線ベクトルを計算するのではなく、
        # gmsh で出力されたvtkの法線ベクトルを使う。(断面が円形でない扁平な形状などだと、中心線を使っても法線ベクトルが外を向かないことがある)
        #
        # ↑ STLも法線(facet normal)と整合するように頂点を記述する。どちらかというと、make_surfacemeshでvtkとして出力するのは、
        # vtkは頂点をID管理するが、STLはしないため、頂点にIDを与えて重複排除する処理が面倒だったから。
        surface_triangle.calc_centroid()                                  #
        surface_triangle.find_closest_centerlinenode(centerline_nodes)    #
        surface_triangle.assign_correspondcenterlinenode_to_surface_node()
    print("info_func    : finish corresponding surface nodes to centerline nodes")

def make_prismlayer(surface_node_dict,surface_triangles,mesh,config):
    print("start generating prism layer")
    # 内側 1 ~ n 層を作成
    for i in range(1,config.NUM_OF_LAYERS+1):
        mesh,layernode_dict = boundarylayer.make_nthlayer_surface_node(i, surface_node_dict, surface_triangles, mesh,config)
        mesh = boundarylayer.make_nthlayer_prism(i,surface_triangles,mesh)
        mesh.num_of_boundarylayernodes = mesh.num_of_nodes
    print("finished generating prism layer")
    return mesh, layernode_dict

def make_tetramesh(layernode_dict, mesh, inlet_outlet_info, filename,config, output_dir):
    stl_filepath_mostinner = myio.write_stl_innersurface(mesh,layernode_dict, config, output_dir)
    try:
        if not gmsh.isInitialized():
            gmsh.initialize()
        gmsh.merge(stl_filepath_mostinner)

        gmsh.model.mesh.createTopology() # 境界面上のNodeに接続する形でメッシュを作るという制約

        innerwall = gmsh.model.getEntities(2)
        gmsh.model.geo.synchronize()
        innerwall_id=[]
        for i in innerwall:
            innerwall_id.append(i[1])
        gmsh.model.addPhysicalGroup(2, innerwall_id, 99)
        gmsh.model.setPhysicalName(2, 99, "INNERWALL")

        surfaceids_aroundvolume=[]
        for i in range(len(innerwall)):
            surfaceids_aroundvolume.append(innerwall[i][1])

        boundary_lines = gmsh.model.getBoundary(innerwall)

        boundary_line_id=[]
        for boundary_line in boundary_lines:
            boundary_line_id.append(boundary_line[1])

        boundary_curves = gmsh.model.geo.addCurveLoops(boundary_line_id)
        for boundary_curve in boundary_curves:
            boundary_surface_id = gmsh.model.geo.addPlaneSurface([boundary_curve])
            surfaceids_aroundvolume.append(boundary_surface_id)

        innerSurfaceLoop = gmsh.model.geo.addSurfaceLoop(surfaceids_aroundvolume)
        gmsh.model.geo.addVolume([innerSurfaceLoop])
        gmsh.model.geo.synchronize()

        # 先にメッシング
        gmsh.option.setNumber("Mesh.OptimizeThreshold", 0.9)
        gmsh.option.setNumber('Mesh.Algorithm', 1)
        gmsh.option.setNumber("Mesh.Optimize", 10)
        gmsh.merge(str(output_dir / f'bgm_{filename}.pos'))           
        bg_field = gmsh.model.mesh.field.add("PostView")    
        gmsh.model.mesh.field.setNumber(bg_field, "ViewIndex", 0) 
        gmsh.model.mesh.field.setAsBackgroundMesh(bg_field) 

        gmsh.model.geo.synchronize()

        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)      
        gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)     
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)

        gmsh.model.mesh.generate(3)
        gmsh.model.mesh.optimize()

        # 後から physical naming
        surfaces_after_voluming = gmsh.model.getEntities(2)
        something = []
        for surface_after_voluming in surfaces_after_voluming:
            something.append(surface_after_voluming[1])
        something = list(set(something)-set(innerwall_id))

        inletlist=[]
        outletlist=[]
        for i in range(len(something)):
            node_ids, node_coords, _ = gmsh.model.mesh.getNodes(2,something[i],True)
            center_x = 0.0
            center_y = 0.0
            center_z = 0.0
            for j in range(len(node_coords)):
                if j%3==0:
                    center_x+=node_coords[j]
                elif j%3==1:
                    center_y+=node_coords[j]
                else:
                    center_z+=node_coords[j]
            center_x=float(center_x/len(node_ids))
            center_y=float(center_y/len(node_ids))
            center_z=float(center_z/len(node_ids))
            center=[center_x,center_y,center_z]
            inletsurface_center = np.array([inlet_outlet_info.inlet_point.x,   inlet_outlet_info.inlet_point.y,  inlet_outlet_info.inlet_point.z])
            outletsurface_center = np.array([inlet_outlet_info.outlet_point.x, inlet_outlet_info.outlet_point.y, inlet_outlet_info.outlet_point.z])
            distance_frominlet = np.linalg.norm(inletsurface_center-np.array(center))
            distance_fromoutlet = np.linalg.norm(outletsurface_center-np.array(center))
            if distance_frominlet < inlet_outlet_info.inlet_radius: 
                inletlist.append(something[i])
            if distance_fromoutlet < inlet_outlet_info.outlet_radius:
                outletlist.append(something[i])
        print("INLET entities are ",inletlist)
        print("inlet_radius=",inlet_outlet_info.inlet_radius)
        print("OUTLET entities are ",outletlist)
        print("outlet_radius=",inlet_outlet_info.outlet_radius)
        if inletlist == []:
            print("can't find inlet surface.")
            sys.exit()
        if outletlist == []:
            print("can't find outlet surface.")
            sys.exit()

        gmsh.model.addPhysicalGroup(2, inletlist, 20)
        gmsh.model.setPhysicalName(2, 20, "INLET")

        gmsh.model.addPhysicalGroup(2, outletlist, 30)
        gmsh.model.setPhysicalName(2, 30, "OUTLET")

        volumeAll = gmsh.model.getEntities(3)
        three_dimension_list = []
        for i in range(len(volumeAll)):
            three_dimension_list.append(volumeAll[i][1])
        gmsh.model.addPhysicalGroup(3, three_dimension_list, 100)
        gmsh.model.setPhysicalName(3, 100, "INTERNAL")
        gmsh.model.geo.synchronize()

        gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
        vtk_file = str(output_dir / f"innermesh_{filename}.vtk")
        stl_file = str(output_dir / f"innermesh_{filename}.stl")
        msh_file = str(output_dir / f"innermesh_{filename}.msh")
        gmsh.write(vtk_file)
        gmsh.write(stl_file)
        gmsh.write(msh_file)
        print(f"output innermesh_{filename}.vtk")
        print(f"output innermesh_{filename}.stl")
        print(f"output innermesh_{filename}.msh")
        myio.read_msh_innermesh(msh_file,mesh,config)
    finally:
        if gmsh.isInitialized():
            gmsh.finalize()
    return mesh

def naming_inlet_outlet(mesh,centerline_nodes,config):
    nodes_on_inletboundaryedge=[]
    nodes_on_outletboundaryedge=[]
    start = mesh.num_of_surfacenodes*config.NUM_OF_LAYERS
    end   = mesh.num_of_surfacenodes*(config.NUM_OF_LAYERS+1)-1
    for i in range(start,end+1):
        if mesh.nodes[i].on_inlet_boundaryedge == True:
            nodes_on_inletboundaryedge.append(mesh.nodes[i])
        if mesh.nodes[i].on_outlet_boundaryedge == True:
            nodes_on_outletboundaryedge.append(mesh.nodes[i])
    for i in range(1,config.NUM_OF_LAYERS+1):
        mesh = boundarylayer.make_nthlayer_quad(i,centerline_nodes, nodes_on_inletboundaryedge, nodes_on_outletboundaryedge,mesh,config)
    print("naming INLET OUTLET to quadrangles on surface.")
    return mesh

def deform_surface(target_centerline_nodes, radius_list_target, centerline_nodes,surface_nodes,surface_triangles,mesh,config, output_dir):
    print("start deforming surface mesh")
    for i in range(len(centerline_nodes)):
        centerline_nodes[i].calc_tangentvec(centerline_nodes)
        target_centerline_nodes[i].calc_tangentvec(target_centerline_nodes)
        
    utility.moving_average_for_tangentvec(centerline_nodes)
    utility.moving_average_for_tangentvec(target_centerline_nodes)
    for i in range(len(centerline_nodes)):
        target_centerline_nodes[i].calc_parallel_vec(centerline_nodes)
        target_centerline_nodes[i].calc_rotation_matrix(centerline_nodes)
    # 移動後の表面を作成
    surface_nodes_moved = []
    moved_nodes_dict   = {}
    for surface_node in surface_nodes:
        surface_node_moved=node.NodeMoved(surface_node.id,0,0,0)
        countor=0
        for correspond_centerlinenode in surface_node.correspond_centerlinenodes:   ### ここ
            surface_node_moved.x += correspond_centerlinenode.x # 複数のcorrespond_centerlinenode がある場合、起点が複数になる。
            surface_node_moved.y += correspond_centerlinenode.y
            surface_node_moved.z += correspond_centerlinenode.z
            localvec = utility.vector(surface_node) - utility.vector(correspond_centerlinenode)
            movementvec = (target_centerline_nodes[correspond_centerlinenode.id].parallel_vec +
                                target_centerline_nodes[correspond_centerlinenode.id].rotation_matrix @ localvec)
            surface_node_moved.x += movementvec[0]
            surface_node_moved.y += movementvec[1]
            surface_node_moved.z += movementvec[2]
            countor += 1
        surface_node_moved.x = surface_node_moved.x/countor
        surface_node_moved.y = surface_node_moved.y/countor
        surface_node_moved.z = surface_node_moved.z/countor

        surface_node_moved.find_closest_centerlinenode(target_centerline_nodes)
        if radius_list_target != None:
            surface_node_moved.find_projectable_centerlineedge(target_centerline_nodes)
            surface_node_moved.set_edgeradius(radius_list_target,config)
            surface_node_moved.execute_deform_radius(radius_list_target,target_centerline_nodes)

        mesh.nodes.append(surface_node_moved)
        mesh.num_of_nodes += 1
        moved_nodes_dict[surface_node.id]=surface_node_moved
        surface_nodes_moved.append(surface_node_moved)

    moved_surface_triangles=[]
    moved_surface_triangle_dict = {}   ### edgeswapのための変数を追加
    
    for surface_triangle in surface_triangles:
        node0 = moved_nodes_dict[surface_triangle.node0.id]
        node1 = moved_nodes_dict[surface_triangle.node1.id]
        node2 = moved_nodes_dict[surface_triangle.node2.id]
        moved_surface_triangle = cell.Triangle(surface_triangle.id,node0,node1,node2)
        moved_surface_triangle.calc_unitnormal() 
        moved_surface_triangle_dict[surface_triangle.id] = moved_surface_triangle
        moved_surface_triangle.correspond_centerlinenode = surface_triangle.correspond_centerlinenode 
        moved_surface_triangles.append(moved_surface_triangle)

    # edgeswap を実行
    if config.EDGESWAP :
        edgeswap_count     = 0
        edgeswap_count_pre = None
        while edgeswap_count_pre != edgeswap_count : 
            moved_surface_triangles, edgeswap_count, edgeswap_count_pre = edgeswap.edgeswap(
                                                                        moved_surface_triangles, 
                                                                        moved_surface_triangle_dict, 
                                                                        moved_nodes_dict,
                                                                        edgeswap_count,
                                                                        edgeswap_count_pre)

    # vtkWindowedSincPolyDataFilter を実行
    if config.SMOOTHER_VTK :
        surface_nodes_moved, moved_surface_triangles = smoother_vtk.vtkWindowedSincPolyDataFilter(surface_nodes_moved, moved_surface_triangles)
    
    for moved_surface_triangle in moved_surface_triangles :   
        mesh.triangles_WALL.append(moved_surface_triangle)
        mesh.num_of_elements += 1

    deformed_surface_filepath = myio.write_stl_surfacetriangles(moved_surface_triangles,"deformed_surface.stl", output_dir)
    print("finished deforming surface mesh. output deformed_surface.stl")
    # myio.write_vtk_surfacemesh_with_ccnID(surface_nodes_moved,moved_surface_triangles)
    # print("output deformed_surface_with_ccnID.vtk")
    return deformed_surface_filepath,moved_nodes_dict,moved_surface_triangles,mesh

def GUI_setting():
    gmsh.option.setNumber("Mesh.SurfaceFaces", 1)
    gmsh.option.setNumber("Mesh.Lines", 1)
    gmsh.option.setNumber("Geometry.PointLabels", 1)
    gmsh.option.setNumber("Mesh.LineWidth", 2)
    gmsh.option.setNumber("General.MouseInvertZoom", 1)
    gmsh.option.setNumber("General.Axes", 3)
    gmsh.option.setNumber("General.Trackball", 0)
    gmsh.option.setNumber("General.RotationX", 0)
    gmsh.option.setNumber("General.RotationY", 0)
    gmsh.option.setNumber("General.RotationZ", 0)
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.model.setColor([(2, 10)], 160,  32, 240) # purple   wall
    gmsh.model.setColor([(2, 11)], 155, 188,   0) # yellow   inlet  tri
    gmsh.model.setColor([(2, 12)], 255,   0,   0) # red      inlet  quad
    gmsh.model.setColor([(2, 13)],  89, 245, 250) # skyblue  outlet tri
    gmsh.model.setColor([(2, 14)],   0,   0, 255) # blue     outlet quad