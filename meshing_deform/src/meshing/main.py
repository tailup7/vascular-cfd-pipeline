from pathlib import Path
import gmsh
import meshing.config as config
from commonlib import meshinfo, myio, func
from postcheck.openfoam_checkmesh import run_checkmesh
from postcheck.visualize_surfacetriangle_with_correspond_centerlinenode import visualize_correspondence

def run(
    centerline_filepath = None,
    stl_filepath        = None,
    output_dir          = None,
    interactive         = True,
    ):
    mesh  = meshinfo.Mesh() 

    # get input files
    if centerline_filepath is None:
        centerline_filepath = myio.select_csv("original")
    if stl_filepath is None:
        stl_filepath = myio.select_stl()
    centerline_nodes, radius_list, inlet_outlet_info = myio.read_target_centerline(centerline_filepath)

    # prepare output folder 
    if output_dir is None:
        THIS_FILEPATH         = Path(__file__).resolve()    
        PROJECT_ROOT = THIS_FILEPATH.parent.parent.parent.parent   
        DATA_DIR     = PROJECT_ROOT / "runs"
        DATA_DIR.mkdir(exist_ok = True)
        centerline_filename = Path(centerline_filepath).stem 
        output_dir = DATA_DIR / f"m-{centerline_filename}"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok = True)

    # copy input files and setting file to output folder for backup
    myio.copy_files_to_dir(centerline_filepath, stl_filepath, output_dir=output_dir, meshing_or_deform="meshing", overwrite = True)

    # 入力ファイルにradiusカラムが無ければ計算する。このとき、中心線上の各点での垂直断面における最小内接円の半径としてradiusを計算する
    if radius_list == None:
        for i in range(len(centerline_nodes)):
            centerline_nodes[i].calc_tangentvec(centerline_nodes)
        radius_list = func.radius_by_perp_section(stl_filepath, centerline_nodes, centerline_filename, inlet_outlet_info, output_dir) 

    # generate background mesh and surface mesh
    func.generate_pos_bgm(stl_filepath, centerline_nodes, radius_list,"original", 40, config, output_dir)  
    surface_nodes, surface_triangles = func.make_surfacemesh(stl_filepath, mesh, "original", output_dir)

    # 今後の処理には不要。単なる可視化・確認のため。
    visualize_correspondence(surface_triangles=surface_triangles, surface_nodes=surface_nodes, centerline_nodes=centerline_nodes, message="original", output_dir=output_dir,)

    # prism の押し出し量を決めるために、surface_node に radius を与える
    surface_node_dict = {}
    for surface_node in surface_nodes:
        surface_node.find_closest_centerlinenode(centerline_nodes)
        surface_node.find_projectable_centerlineedge(centerline_nodes)    
        surface_node.set_edgeradius(radius_list,config)
        surface_node_dict[surface_node.id] = surface_node

    # generate inner mesh (prism & tetra)
    mesh, layernode_dict = func.make_prismlayer(surface_node_dict,surface_triangles,mesh,config)
    func.make_tetramesh(layernode_dict,mesh,inlet_outlet_info,"original",config, output_dir)
    mesh = func.naming_inlet_outlet(mesh,centerline_nodes,config)

    # output and visualize the mesh
    myio.write_msh_allmesh(mesh,"original", output_dir)
    try:
        if not gmsh.isInitialized(): 
            gmsh.initialize()
        gmsh.merge(str(output_dir / "original_mesh.msh"))
        gmsh.write(str(output_dir / "original_mesh.vtk"))
        if interactive:
            func.GUI_setting()
            gmsh.fltk.run()
    finally:       
        gmsh.finalize()
    return output_dir

def main():
    output_dir = run()
    check = run_checkmesh(str(output_dir / "original_mesh.msh"))

if __name__ == "__main__":
    main()