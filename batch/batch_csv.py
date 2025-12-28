from __future__ import annotations
from pathlib import Path
import sys
import csv
BATCH_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = BATCH_DIR.parent
SRC_DIR     = PROJECT_ROOT / "meshing_deform" / "src"
if not SRC_DIR.exists():
    raise FileNotFoundError(f"[batch] src dir not found: {SRC_DIR}")
sys.path.insert(0,str(SRC_DIR))
from meshing.main import run as run_meshing
from deform.main import run as run_deform
from postcheck.openfoam_checkmesh import run_checkmesh

def run_batch(csv_path: Path):
    csv_path = csv_path.resolve()

    log_path = PROJECT_ROOT / "runs" /"log.txt"
    log_path.parent.mkdir(parents=True,exist_ok=True)

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)

        for row_idx, row in enumerate(reader, start=1):
            if not row:
                continue

            # コメント行はスキップ
            if row[0].lstrip().startswith("#"):
                continue

            mode = row[0].strip()

            try:
                if mode == "m":
                    # ------------------
                    # meshing
                    # ------------------
                    input1_rel = row[1]
                    input3_rel = row[3]
                    output_name = row[5]

                    centerline_filepath = (PROJECT_ROOT / "inputs" / "original" / input1_rel).resolve()
                    stl_filepath        = (PROJECT_ROOT / "inputs" / "original" / input3_rel).resolve()

                    output_dir = (PROJECT_ROOT / "runs" / output_name).resolve()

                    print(f"[Batch][Row {row_idx}] Meshing")
                    print(f"  centerline : {centerline_filepath}")
                    print(f"  stl        : {stl_filepath}")
                    print(f"  output     : {output_dir}")

                    run_meshing(
                        centerline_filepath = str(centerline_filepath),
                        stl_filepath        = str(stl_filepath),
                        output_dir          = str(output_dir),
                        interactive         = False,
                    )

                    original_mesh_filepath = str(output_dir / "original_mesh.msh")

                    check = run_checkmesh(original_mesh_filepath)

                    with log_path.open("a", encoding="utf-8") as f:
                        f.write(f"log message : {output_name} {check} \n")


                elif mode == "d":
                    # ------------------
                    # deform
                    # ------------------
                    input1_rel  = row[1]
                    input2_rel  = row[2]
                    input3_rel  = row[3]
                    output_name = row[5]

                    centerline_filepath = (PROJECT_ROOT / "inputs" / "original" / input1_rel).resolve()
                    target_centerline_filepath = (PROJECT_ROOT / "inputs" / "target" /   input2_rel).resolve()
                    filepath_mesh          = (PROJECT_ROOT / "inputs" / "original" /   input3_rel).resolve()

                    output_dir = (PROJECT_ROOT / "runs" / output_name).resolve()

                    print(f"[Batch][Row {row_idx}] Deform")
                    print(f"  original CL : {centerline_filepath}")
                    print(f"  target CL   : {target_centerline_filepath}")
                    print(f"  mesh        : {filepath_mesh}")
                    print(f"  output      : {output_dir}")

                    run_deform(
                        centerline_filepath = str(centerline_filepath),
                        target_centerline_filepath = str(target_centerline_filepath),
                        original_mesh_filepath = str(filepath_mesh),
                        output_dir              = str(output_dir),
                        interactive             = False,
                    )

                    deformed_mesh_filepath = str(output_dir / "deformed_mesh.msh")
                    check = run_checkmesh(deformed_mesh_filepath)
                    
                    with log_path.open("a", encoding="utf-8") as f:
                        f.write(f"log message : {output_name} {check} \n")

                else:
                    raise ValueError(f"Unknown mode '{mode}'")

            except Exception as e:
                print(f"[ERROR][Row {row_idx}] {e}", file=sys.stderr)
                print("→ 次の行へ進みます\n")

def main():
    if len(sys.argv) != 2:
        print("Usage: python batch.py batch_cases.csv")
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        print(f"CSV not found: {csv_path}")
        sys.exit(1)

    run_batch(csv_path)

if __name__ == "__main__":
    main()
