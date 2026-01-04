from commonlib.func import map_surfacenode_to_centerlinenodes
import commonlib.myio as myio
from pathlib import Path

# meshing実行時には func.make_surfacemesh()内の myio.read_vtk_surfacemesh()で "surfacemesh_original.vtk" から読み込んだ surface_triangles を受け取る 
# deform実行時には、myio.read_msh_original_WALL()で "original_mesh.msh" から読み込んだ surface_triangles を受け取る
# (これら2つのsurface_triangles は、まったく同じ順番、構成のはず(要確認))
# このスクリプトを直接実行したときには、GUIでsurfacemesh_original.vtkか surfacemesh_deformed.vtk (? 今のところ出力されるようにできていない) と
# centerline.csvをGUIで選択する。batch_auto.py実行時には、
def visualize_correspondence(
    surfacemesh_vtk_filepath   = None,
    surface_triangles          = None,
    surface_nodes              = None,
    centerline_nodes           = None,
    centerline_filepath        = None,
    original_mesh_filepath     = None,
    message                    = "message",
    output_dir                 = None,
    ):


    # meshing.main実行中にmain.pyから呼び出される場合
    map_surfacenode_to_centerlinenodes(surface_triangles, centerline_nodes)
    myio.write_vtk_surfacemesh_with_ccnID(surface_nodes,surface_triangles, message, output_dir)


    # 直接実行する場合。GUIでsurfacemesh_original.vtkを選択する
    # if surfacemesh_vtk_filepath is None and surface_triangles is None:

    # prepare output folder 
    # if output_dir is None:
    #     THIS_FILEPATH         = Path(__file__).resolve()    
    #     PROJECT_ROOT = THIS_FILEPATH.parent.parent.parent.parent 
    #     DATA_DIR     = PROJECT_ROOT / "runs"
    #     DATA_DIR.mkdir(exist_ok = True)
    #     target_centerline_filename = Path(centerline_filepath).stem 
    #     output_dir = DATA_DIR / f"d-{target_centerline_filename}"
    # output_dir = Path(output_dir)
    # output_dir.mkdir(parents=True,exist_ok=True)





