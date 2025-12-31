from __future__ import annotations

from pathlib import Path
import sys
import shutil

# --------------------
# project paths
# --------------------
BATCH_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BATCH_DIR.parent
SRC_DIR = PROJECT_ROOT / "meshing_deform" / "src"

if not SRC_DIR.exists():
    raise FileNotFoundError(f"[batch] src dir not found: {SRC_DIR}")

sys.path.insert(0, str(SRC_DIR))

from meshing.main import run as run_meshing
from deform.main import run as run_deform
from postcheck.openfoam_checkmesh import run_checkmesh


def list_files_exactly_one(dirpath: Path, pattern: str) -> Path:
    dirpath = dirpath.resolve()
    files = sorted([p for p in dirpath.glob(pattern) if p.is_file()])
    if len(files) != 1:
        raise RuntimeError(
            f"[batch] Expected exactly 1 file '{pattern}' in {dirpath}, found {len(files)}:\n"
            + "\n".join(f"  - {p.name}" for p in files)
        )
    return files[0].resolve()


def ensure_original_mesh(original_dir: Path) -> Path:
    """
    inputs/original に *.msh があればそれを使う。
    無ければ inputs/original の *.csv と *.stl を使って run_meshing し、
    生成された original_mesh.msh を inputs/original にコピーして返す。
    """
    original_dir = original_dir.resolve()
    msh_files = sorted([p for p in original_dir.glob("*.msh") if p.is_file()])

    if len(msh_files) >= 2:
        raise RuntimeError(
            f"[batch] Found 2+ msh files in {original_dir}. Please keep exactly 1.\n"
            + "\n".join(f"  - {p.name}" for p in msh_files)
        )

    if len(msh_files) == 1:
        print(f"[batch] Found existing mesh: {msh_files[0]}")
        return msh_files[0].resolve()

    # msh が無い場合は meshing 実行
    centerline_filepath = list_files_exactly_one(original_dir, "*.csv")
    stl_filepath = list_files_exactly_one(original_dir, "*.stl")

    print("[batch] No msh found. Run meshing once.")
    print(f"  centerline : {centerline_filepath}")
    print(f"  stl        : {stl_filepath}")

    output_dir = run_meshing(
        centerline_filepath=str(centerline_filepath),
        stl_filepath=str(stl_filepath),
        interactive=False,
    )

    generated_mesh = (output_dir / "original_mesh.msh").resolve()
    if not generated_mesh.is_file():
        raise FileNotFoundError(f"[batch] meshing output not found: {generated_mesh}")
    # inputs/original へコピー（ファイル名はそのままにする）
    copied_mesh = (original_dir / generated_mesh.name).resolve()
    shutil.copy2(generated_mesh, copied_mesh)
    print(f"[batch] Copied mesh to: {copied_mesh}")
    check = run_checkmesh(str(copied_mesh))
    print(f"[batch] checkMesh: {check}")
    return copied_mesh


def run_deform_all(original_dir: Path, target_dir: Path):
    """
    inputs/target の *.csv を順番に target_centerline として deform する。
    centerline_filepath と mesh は inputs/original のものを使う。
    出力: runs/d-<target_stem>
    """
    original_dir = original_dir.resolve()
    target_dir = target_dir.resolve()

    # original 側：centerline は 1つだけ
    centerline_filepath = list_files_exactly_one(original_dir, "*.csv")

    # original 側：mesh は ensure_original_mesh で「必ず1つ」用意される
    mesh_filepath = ensure_original_mesh(original_dir)

    # target 側：複数 csv を順番に処理
    target_csvs = sorted([p for p in target_dir.glob("*.csv") if p.is_file()])
    if len(target_csvs) == 0:
        raise RuntimeError(f"[batch] No target csv found in {target_dir}")

    log_path = (PROJECT_ROOT / "runs" / "log.txt").resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    print("[batch] Start deform loop")
    print(f"  original CL : {centerline_filepath}")
    print(f"  mesh        : {mesh_filepath}")
    print(f"  targets     : {len(target_csvs)} files in {target_dir}")

    for i, target_centerline_filepath in enumerate(target_csvs, start=1):
        target_centerline_filepath = target_centerline_filepath.resolve()

        print(f"\n[batch][{i}/{len(target_csvs)}] Deform")
        print(f"  target CL : {target_centerline_filepath}")

        try:
            output_dir = run_deform(
                centerline_filepath=str(centerline_filepath),
                target_centerline_filepath=str(target_centerline_filepath),
                original_mesh_filepath=str(mesh_filepath),
                interactive=False,
            )

            deformed_mesh = (output_dir / "deformed_mesh.msh").resolve()
            if not deformed_mesh.is_file():
                raise FileNotFoundError(f"[batch] deformed mesh not found: {deformed_mesh}")

            check = run_checkmesh(str(deformed_mesh))

            with log_path.open("a", encoding="utf-8") as f:
                f.write(f"[OK] d-{target_centerline_filepath.stem} check={check}\n")

        except Exception as e:
            print(f"[ERROR] target={target_centerline_filepath.name} : {e}", file=sys.stderr)
            with log_path.open("a", encoding="utf-8") as f:
                f.write(f"[NG] d-{target_centerline_filepath.stem} error={e}\n")
            # 続行
            continue


def main():
    original_dir = PROJECT_ROOT / "inputs" / "original"
    target_dir = PROJECT_ROOT / "inputs" / "target"

    if not original_dir.is_dir():
        print(f"[batch] original dir not found: {original_dir}", file=sys.stderr)
        sys.exit(1)

    if not target_dir.is_dir():
        print(f"[batch] target dir not found: {target_dir}", file=sys.stderr)
        sys.exit(1)

    run_deform_all(original_dir, target_dir)


if __name__ == "__main__":
    main()
