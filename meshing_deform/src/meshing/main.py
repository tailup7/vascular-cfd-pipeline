from pathlib import Path
import logging
import time
import gmsh
import meshing.config as config
from commonlib import meshinfo, myio, func, time_logging
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
    centerline_nodes, radius_list, inlet_outlet_info, expansion_list = myio.read_target_centerline(centerline_filepath)

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

    # logfile setting
    logfile = DATA_DIR / "time.log"
    logger  = time_logging.setup_logger(logfile)
    total_start = time.perf_counter()
    logger.info("=== Meshing started ===")
    logger.info(f"=== m-{centerline_filename} ===")

    # copy input files and setting file to output folder for backup
    myio.copy_files_to_dir(centerline_filepath, stl_filepath, output_dir=output_dir, meshing_or_deform="meshing", overwrite = True)

    # 入力ファイルにradiusカラムが無ければ計算する。このとき、中心線上の各点での垂直断面における最小内接円の半径としてradiusを計算する
    if radius_list == None: # 常にNoneとしてもいい(original_centerlineファイルにはradiusカラムは不要)な気がする
        for i in range(len(centerline_nodes)):
            centerline_nodes[i].calc_tangentvec(centerline_nodes)
        radius_list = func.radius_by_perp_section(stl_filepath, centerline_nodes, centerline_filename, inlet_outlet_info, output_dir) 

    # generate background mesh and surface mesh
    time_logging.timed(
    logger,
    "generate_pos_bgm",
    func.generate_pos_bgm,
    stl_filepath, centerline_nodes, radius_list,
    "original", 40, config, output_dir
    )
      
    surface_nodes, surface_triangles = time_logging.timed(
        logger,
        "make_surfacemesh",
        func.make_surfacemesh,
        stl_filepath, mesh, "original", config, output_dir
    )

    # この後の処理には使わない。中心線Nodeと表面三角形パッチの対応関係の可視化・確認のため。処理に多少時間がかかるので、不要ならコメントアウトして下さい。
    # visualize_correspondence(surface_triangles=surface_triangles, surface_nodes=surface_nodes, centerline_nodes=centerline_nodes, message="original", output_dir=output_dir,)

    # prism の押し出し量を決めるために、surface_node に radius を与える
    start = time.perf_counter()
    surface_node_dict = {}
    for surface_node in surface_nodes:
        surface_node.find_closest_centerlinenode(centerline_nodes)
        surface_node.find_projectable_centerlineedge(centerline_nodes)    
        surface_node.set_edgeradius(radius_list,config)
        surface_node_dict[surface_node.id] = surface_node
    end = time.perf_counter()
    logger.info(f"surface_node preprocessing : {end - start:.3f} sec")

    # generate inner mesh (prism & tetra)
    # mesh, layernode_dict = func.make_prismlayer(surface_node_dict,surface_triangles,mesh,config)
    mesh, layernode_dict = time_logging.timed(
    logger,
    "make_prismlayer",
    func.make_prismlayer,
    surface_node_dict, surface_triangles, mesh, config
    )
    # func.make_tetramesh(layernode_dict,mesh,inlet_outlet_info,"original",config, output_dir)
    time_logging.timed(
    logger,
    "make_tetramesh",
    func.make_tetramesh,
    layernode_dict, mesh, inlet_outlet_info,
    "original", config, output_dir
    )

    func.naming_inlet_outlet(mesh,centerline_nodes,config)

    # output and visualize the mesh
    start = time.perf_counter()
    myio.write_msh_allmesh(mesh,"original", output_dir)
    try:
        if not gmsh.isInitialized(): 
            gmsh.initialize()
        gmsh.merge(str(output_dir / "original_mesh.msh"))
        gmsh.write(str(output_dir / "original_mesh.vtk"))
        end = time.perf_counter()
        logger.info(f"merge and output tetra-prism mesh : {end - start:.3f} sec")
        if interactive:
            func.GUI_setting()
            gmsh.fltk.run()
    finally:       
        gmsh.finalize()

    total_end = time.perf_counter()
    logger.info(f"TOTAL TIME : {total_end - total_start:.3f} sec")
    logger.info("=== Meshing finished ===")

    return output_dir

def main():
    output_dir = run()

if __name__ == "__main__":
    main()