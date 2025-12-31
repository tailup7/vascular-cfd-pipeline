import time
import gmsh
import commonlib.meshinfo as meshinfo
from postcheck.openfoam_checkmesh import run_checkmesh
import deform.config as config
import commonlib.func as func
import commonlib.myio as myio
from .centerline.alignment import alignment # 関数をimport
from pathlib import Path

# gmsh.model.mesh.classifySurfaces の引数はどう設定するべきか

def run(
    centerline_filepath        = None,
    target_centerline_filepath = None,
    original_mesh_filepath     = None,
    output_dir                 = None,
    interactive                = True,
    ):
    start = time.time()
    print("-------- Start Deform Mesh --------")
    deformed_mesh = meshinfo.Mesh()

    # select and read input files
    if centerline_filepath is None :
        centerline_filepath     = myio.select_csv("original")
    if target_centerline_filepath is None :
        target_centerline_filepath       = myio.select_csv("target")
    if original_mesh_filepath is None :
        original_mesh_filepath = myio.select_msh()
    centerline_nodes      = myio.read_original_centerline(centerline_filepath) 
    target_centerline_nodes, radius_list_target, inlet_outlet_info = myio.read_target_centerline(target_centerline_filepath)
    surface_nodes,surface_triangles              = myio.read_msh_original_WALL(original_mesh_filepath,deformed_mesh)
    if config.ALIGNMENT == True:
        target_centerline_nodes, inlet_outlet_info = alignment(centerline_nodes, target_centerline_nodes, radius_list_target, target_centerline_filepath, output_dir)

    # prepare output folder 
    if output_dir is None:
        THIS_FILEPATH         = Path(__file__).resolve()    
        PROJECT_ROOT = THIS_FILEPATH.parent.parent.parent.parent 
        DATA_DIR     = PROJECT_ROOT / "runs"
        DATA_DIR.mkdir(exist_ok = True)
        target_centerline_filename = Path(target_centerline_filepath).stem 
        output_dir = DATA_DIR / f"d-{target_centerline_filename}"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)

    # copy input files to output folder for backup
    myio.copy_files_to_dir(centerline_filepath, target_centerline_filepath,original_mesh_filepath, dst_dir = output_dir / "input", overwrite=True)

    # deform
    func.map_surfacenode_to_centerlinenodes(surface_triangles, centerline_nodes)
    deformed_surface_filepath, moved_nodes_dict, moved_surface_triangles, deformed_mesh = func.deform_surface(target_centerline_nodes,  
                                                                                                    radius_list_target,
                                                                                                    centerline_nodes,
                                                                                                    surface_nodes,
                                                                                                    surface_triangles,deformed_mesh, config,output_dir)
    if radius_list_target == None:
        radius_for_bgm = func.calc_radius(deformed_surface_filepath,target_centerline_nodes,inlet_outlet_info,config, output_dir)
        for i in range(1,deformed_mesh.num_of_surfacenodes+1):
            moved_nodes_dict[i].find_projectable_centerlineedge(target_centerline_nodes)
            moved_nodes_dict[i].set_edgeradius(radius_for_bgm,config)
    else:
        radius_for_bgm = radius_list_target
    func.generate_pos_bgm(deformed_surface_filepath,target_centerline_nodes, radius_for_bgm,"deform", 40,config,output_dir) # ここの最後の引数、angle_classifyは
    deformed_mesh, layernode_dict = func.make_prismlayer(moved_nodes_dict,moved_surface_triangles,deformed_mesh,config)  # いくつにするべきか
    deformed_mesh = func.make_tetramesh(layernode_dict, deformed_mesh, inlet_outlet_info, "deform",config,output_dir)
    deformed_mesh = func.naming_inlet_outlet(deformed_mesh,target_centerline_nodes,config)

    # output the mesh
    myio.write_msh_allmesh(deformed_mesh,"deformed",output_dir)
    end = time.time()
    elapsed_time = end-start
    # visualize the mesh
    try:
        if not gmsh.isInitialized():
            gmsh.initialize()    
        gmsh.merge(str(output_dir / "deformed_mesh.msh"))
        gmsh.write(str(output_dir / "deformed_mesh.vtk"))
        if interactive:
            func.GUI_setting()
            gmsh.fltk.run()
    finally:       
        gmsh.finalize()
    print("-------- Finished Deform Mesh --------")
    print(f"elapsed time : {elapsed_time:.4f} s")
    return output_dir

def main():
    output_dir = run()
    run_checkmesh(str(output_dir / "deformed_mesh.msh"))

if __name__ == "__main__":
    main()