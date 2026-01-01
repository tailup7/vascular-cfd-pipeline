from commonlib.func import map_surfacenode_to_centerlinenodes
import commonlib.myio as myio
from pathlib import Path

# meshing実行時には surfacemesh_vtk_filepath を受け取る, deform実行時には、read_msh_original_WALL()で返されたsurface_triangles を受け取る
# このスクリプトを直接実行したときには、GUIでsurfacemesh_original.vtkか surfacemesh_deformed.vtk (? 今のところ出力されるようにできていない) と
# centerline.csvを受け取る。batch_auto.py実行時には、
def run(
    surfacemesh_vtk_filepath   = None,
    surface_triangles          = None,
    target_centerline_filepath = None,
    original_mesh_filepath     = None,
    output_dir                 = None,
    ):

    # surfacemesh_vtk_filepath を受け取っていなければ、GUIでsurfacemesh_original.vtkを選択する
    if surfacemesh_vtk_filepath is None and surface_triangles is None:

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



