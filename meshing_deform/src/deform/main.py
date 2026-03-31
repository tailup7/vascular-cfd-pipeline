from pathlib import Path
import time
import logging
import gmsh
import deform.config as deform_config
import meshing.config as meshing_config
from commonlib import meshinfo, myio, func, time_logging
from .centerline.alignment import alignment

# gmsh.model.mesh.classifySurfaces の引数はどう設定するべきか

def run(
    centerline_filepath        = None,
    target_centerline_filepath = None,
    original_mesh_filepath     = None,
    output_dir                 = None,
    interactive                = True,
    ):
    deformed_mesh = meshinfo.Mesh()

    # select and read input files
    if centerline_filepath is None :
        centerline_filepath     = myio.select_csv("original")
    if target_centerline_filepath is None :
        target_centerline_filepath       = myio.select_csv("target")
    if original_mesh_filepath is None :
        original_mesh_filepath = myio.select_msh()
    centerline_nodes      = myio.read_original_centerline(centerline_filepath) 
    target_centerline_nodes, radius_list_target, inlet_outlet_info, expansion_list = myio.read_target_centerline(target_centerline_filepath)
    surface_nodes,surface_triangles              = myio.read_msh_original_WALL(original_mesh_filepath,deformed_mesh)

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

    # logfile setting
    logfile = DATA_DIR / "time.log"
    logger  = time_logging.setup_logger(logfile)
    total_start = time.perf_counter()
    logger.info("=== Deform started ===")
    logger.info(f"=== d-{target_centerline_filename} ===")

    # centerline alignment
    if deform_config.ALIGNMENT == True:
        target_centerline_nodes, inlet_outlet_info = alignment(centerline_nodes, target_centerline_nodes, radius_list_target, target_centerline_filepath, output_dir)

    # copy input files and setting file to output folder for backup 
    start = time.perf_counter()
    myio.copy_files_to_dir(centerline_filepath, target_centerline_filepath,original_mesh_filepath, output_dir=output_dir, meshing_or_deform="deform", overwrite=True)
    # output original surface for func.radius_by_perp_section()
    surfacemesh_original_filepath = myio.write_stl_surfacetriangles(surface_triangles, "surfacemesh_original.stl", output_dir)
    end = time.perf_counter()
    logger.info(f"copy input files : {end - start:.3f} sec")
    
    # deform surface mesh
    start = time.perf_counter()
    func.map_surfacenode_to_centerlinenodes(surface_triangles, centerline_nodes)
    end = time.perf_counter()
    logger.info(f"map surface nodes to centerline nodes: {end - start:.3f} sec")
    # deform (及び平滑化) のログは関数側でとる
    deformed_surface_filepath, moved_nodes_dict, moved_surface_triangles, deformed_mesh = func.deform_surface(target_centerline_nodes,  
                                                                                                    radius_list_target,
                                                                                                    expansion_list,
                                                                                                    centerline_nodes,
                                                                                                    surface_nodes,
                                                                                                    surface_triangles,deformed_mesh, deform_config,output_dir)


    # 入力ファイルにradiusカラムが無ければ計算する。このとき、中心線上の各点での垂直断面における最小内接円の半径としてradiusを計算する
    start = time.perf_counter()
    if radius_list_target == None:
        radius_list_target = func.radius_by_perp_section(surfacemesh_original_filepath, centerline_nodes, target_centerline_filename, inlet_outlet_info, output_dir) 
        for i in range(1,deformed_mesh.num_of_surfacenodes+1):
            moved_nodes_dict[i].find_projectable_centerlineedge(target_centerline_nodes)
    # radiusをedgeradiusに割り当てる。edgeradiusは、BGMの各nodeに与えられてスカラー場を作る + プリズム層の押し出しの際の参照直径にもなる。
    if deform_config.USE_MESHING_CONFIG :
        config = meshing_config
    else:
        config = deform_config
    for i in range(1,deformed_mesh.num_of_surfacenodes+1):
        moved_nodes_dict[i].set_edgeradius(radius_list_target, config)
    end = time.perf_counter()
    logger.info(f"calc or set radius : {end - start:.3f} sec")

    # generate BackGroundMesh 
    # func.generate_pos_bgm(deformed_surface_filepath,target_centerline_nodes, radius_list_target,"deform", 40, config, output_dir) # ここの引数angle_classifyはいくつにするべきか
    time_logging.timed(
    logger,
    "generate_pos_bgm",
    func.generate_pos_bgm,
    deformed_surface_filepath, target_centerline_nodes, radius_list_target,
    "deform", 40, config, output_dir
    )


    # generate inner mesh (prism & tetra)
    deformed_mesh, layernode_dict = time_logging.timed(
    logger,
    "make_prismlayer",
    func.make_prismlayer,
    moved_nodes_dict, moved_surface_triangles, deformed_mesh, config
    )
    # deformed_mesh = func.make_tetramesh(layernode_dict, deformed_mesh, inlet_outlet_info, "deform",config,output_dir) ## make_tetramesh()で仮にconfig=deform_configを読み込んでも、BGMはすでに
    time_logging.timed(
    logger,
    "make_tetramesh",
    func.make_tetramesh,
    layernode_dict, deformed_mesh, inlet_outlet_info,
    "deform", config, output_dir
    )
    func.naming_inlet_outlet(deformed_mesh,target_centerline_nodes,config)                           ## 作成されているので、意味がない。(テトラ部分を細かく切ることはできない)
                                                                                                                    ## TODO : なので書き直す
    # output and visualize the mesh
    start = time.perf_counter()
    myio.write_msh_allmesh(deformed_mesh,"deformed",output_dir)
    try:
        if not gmsh.isInitialized():
            gmsh.initialize()    
        gmsh.merge(str(output_dir / "deformed_mesh.msh"))
        gmsh.write(str(output_dir / "deformed_mesh.vtk"))
        end = time.perf_counter()
        logger.info(f"merge and output tetra-prism mesh : {end - start:.3f} sec")
        if interactive:
            func.GUI_setting()
            gmsh.fltk.run()
    finally:       
        gmsh.finalize()

    total_end = time.perf_counter()
    logger.info(f"TOTAL TIME : {total_end - total_start:.3f} sec")
    logger.info("=== Deform finished ===")

    return output_dir

def main():
    output_dir = run()

if __name__ == "__main__":
    main()