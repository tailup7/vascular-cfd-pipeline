import subprocess
import os
import shutil

def run_checkmesh(case_dir):
    """
    このファイル(openfoam_utils.py)があるディレクトリを基準に、
    - output/allmesh_original.msh を case/allmesh_original.msh にコピー（上書き）
    - case ディレクトリに cd して gmshToFoam allmesh_original.msh コマンド 及び checkMesh コマンド
    を実行する。
    """

    # この python ファイルのあるディレクトリ
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # フォルダのパス
    output_dir = os.path.join(script_dir, "output")
    case_dir   = os.path.join(script_dir, "case")

    # .msh のパス
    src_msh = os.path.join(output_dir, "allmesh_original.msh")
    dst_msh = os.path.join(case_dir, "allmesh_original.msh")

    # 存在チェック
    if not os.path.isfile(src_msh):
        raise FileNotFoundError(f"入力メッシュが見つかりません: {src_msh}")

    if not os.path.isdir(case_dir):
        raise FileNotFoundError(f"case ディレクトリが見つかりません: {case_dir}")

    # case ディレクトリにコピー（同名があれば上書き）
    print(f"Copying {src_msh} -> {dst_msh}")
    shutil.copy2(src_msh, dst_msh)

    # OpenFOAM の環境を読み込んで、case ディレクトリでコマンド実行
    cmd = (
        "source /usr/lib/openfoam/openfoam2506/etc/bashrc && "
        f"cd '{case_dir}' && "
        "gmshToFoam allmesh_original.msh && "
        "checkMesh"
    )

    print("Running gmshToFoam + checkMesh in", case_dir)

    result = subprocess.run(
        ["bash", "-lc", cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    print("===== gmshToFoam + checkMesh output =====")
    print(result.stdout)
    print("===== gmshToFoam + checkMesh error =====")
    print(result.stderr)

    if result.returncode != 0:
        print("checkMesh FAILED!")
        return False
    else:
        print("checkMesh OK.")
        return True
