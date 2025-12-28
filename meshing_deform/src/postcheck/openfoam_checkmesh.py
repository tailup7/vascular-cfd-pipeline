import subprocess
import os
import shutil
from pathlib import Path

SRC_DIR             = Path(__file__).resolve().parent.parent
PROJECT_ROOT_PARENT = SRC_DIR.parent.parent
case_dir            = PROJECT_ROOT_PARENT / "openfoam_case" / "simpleFoam"

def run_checkmesh(mesh_path):
    """
    Parameters
    ----------
    mesh_path : str or Path
        チェックしたい .msh ファイルの絶対パス
    case_dir : str or Path
        OpenFOAM の case ディレクトリ（constant/, system/ がある場所）
    """
    
    global case_dir
    mesh_path = Path(mesh_path).resolve()
    case_dir  = Path(case_dir).resolve()

    if not mesh_path.is_file():
        raise FileNotFoundError(f"mesh file not found: {mesh_path}")

    if not case_dir.is_dir():
        raise FileNotFoundError(f"case directory not found: {case_dir}")

    # コピー先（同名）
    dst_msh = case_dir / mesh_path.name

    print(f"Copying mesh:")
    print(f"  {mesh_path} -> {dst_msh}")
    shutil.copy2(mesh_path, dst_msh)

    # OpenFOAM 環境を読んで実行
    if os.environ.get("FUGAKU"):
        cmd = (
            f"cd '{case_dir}' && "
            f"gmshToFoam '{dst_msh.name}' && "
            "checkMesh"
        )
    else:
        cmd = (
            "source /usr/lib/openfoam/openfoam2506/etc/bashrc && "
            f"cd '{case_dir}' && "
            f"gmshToFoam '{dst_msh.name}' && "
            "checkMesh"
        )

    print("Running gmshToFoam + checkMesh in:")
    print(f"  {case_dir}")

    result = subprocess.run(
        ["bash", "-lc", cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # --- ログファイル出力 ---
    log_path = case_dir / "checkMesh.log"

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("===== gmshToFoam + checkMesh output =====\n")
        f.write(result.stdout)
        f.write("\n\n===== gmshToFoam + checkMesh error =====\n")
        f.write(result.stderr)

    print(f"checkMesh log written to: {log_path}")

    # --- checkMesh.log を .msh のあったディレクトリへコピー ---
    dst_log = mesh_path.parent / "checkMesh.log"
    shutil.copy2(log_path, dst_log)
    print(f"checkMesh log copied to: {dst_log}")

    print("===== gmshToFoam + checkMesh output =====")
    print(result.stdout)
    print("===== gmshToFoam + checkMesh error =====")
    print(result.stderr)

    # --- 判定ロジック ---
    if "Mesh OK" in result.stdout:
        print("checkMesh OK")
        return "checkMesh OK"
    else:
        print("checkMesh FAILED")
        return "checkMesh FAILED"
