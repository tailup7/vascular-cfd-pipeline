#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OpenFOAM v1612+ 向けの後処理:
- p (p/rho)                  -> p_Pa (Pa)
- wallShearStress (kinematic)-> wallShearStress_Pa (Pa)
internalField / boundaryField の両方で、uniform と nonuniform ブロックを安全に 1060 倍。
ヘッダの dimensions も Pa に更新。
"""

import argparse, os, re, math, sys

PA_DIM = "[1 -1 -2 0 0 0 0]"
NUM_RE = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")

def list_time_dirs(case_dir):
    ts=[]
    for name in os.listdir(case_dir):
        p=os.path.join(case_dir,name)
        try:
            float(name)
            if os.path.isdir(p): ts.append(name)
        except ValueError:
            pass
    ts.sort(key=lambda x: float(x))
    return ts

def mul_all_numbers(line, scale):
    def rep(m): return f"{float(m.group(0))*scale:.10g}"
    return NUM_RE.sub(rep, line)

def fix_object_line(line, new_object):
    # object 名だけ差し替え
    m = re.match(r'^(\s*)object\s+\S+\s*;\s*$', line)
    if not m: return line
    indent = m.group(1)
    return f"{indent}object      {new_object};\n"

def fix_dimensions_line(line):
    # dimensions だけ差し替え
    m = re.match(r'^(\s*)dimensions\s+\[[^\]]*\]\s*;\s*$', line)
    if not m: return line
    indent = m.group(1)
    return f"{indent}dimensions  {PA_DIM};\n"

def convert_scalar_file(src, dst, new_object, rho):
    with open(src, "r") as f: lines = f.readlines()
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]

        # ヘッダ置換（インデント保持）
        ls = line.lstrip()
        if ls.startswith("object"):
            out.append(fix_object_line(line, new_object)); i+=1; continue
        if ls.startswith("dimensions"):
            out.append(fix_dimensions_line(line)); i+=1; continue

        # uniform スカラー（internalField / value どちらでも）
        # "nonuniform" には反応しないように、" nonuniform " が無いことを確認
        if ("uniform" in line) and ("nonuniform" not in line) and ("(" not in line) and (";" in line):
            out.append(mul_all_numbers(line, rho)); i+=1; continue

        # nonuniform List<scalar> ブロック（行頭でなくても検出）
        if ("nonuniform" in line) and ("List<scalar>" in line):
            out.append(line); i+=1                # " ... nonuniform List<scalar>"
            if i<n: out.append(lines[i]); i+=1    # 個数行（スケールしない）
            if i<n: out.append(lines[i]); i+=1    # "(" 行
            # 値本体（閉じ括弧まで）をスケール
            while i<n and not re.match(r'^\s*\);\s*$', lines[i]):
                out.append(mul_all_numbers(lines[i], rho)); i+=1
            if i<n: out.append(lines[i]); i+=1    # ");"
            continue

        out.append(line); i+=1

    with open(dst, "w") as f: f.writelines(out)

def convert_vector_file(src, dst, new_object, rho):
    with open(src, "r") as f: lines = f.readlines()
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]

        # ヘッダ置換（インデント保持）
        ls = line.lstrip()
        if ls.startswith("object"):
            out.append(fix_object_line(line, new_object)); i+=1; continue
        if ls.startswith("dimensions"):
            out.append(fix_dimensions_line(line)); i+=1; continue

        # uniform ベクトル（internalField / value どちらでも）
        if ("uniform" in line) and ("nonuniform" not in line) and ("(" in line) and (");" in line):
            out.append(mul_all_numbers(line, rho)); i+=1; continue

        # nonuniform List<vector> ブロック
        if ("nonuniform" in line) and ("List<vector>" in line):
            out.append(line); i+=1                # " ... nonuniform List<vector>"
            if i<n: out.append(lines[i]); i+=1    # 個数行
            if i<n: out.append(lines[i]); i+=1    # "(" 行
            while i<n and not re.match(r'^\s*\);\s*$', lines[i]):
                out.append(mul_all_numbers(lines[i], rho)); i+=1
            if i<n: out.append(lines[i]); i+=1    # ");"
            continue

        out.append(line); i+=1

    with open(dst, "w") as f: f.writelines(out)

def first_scalar(fp):
    txt=open(fp,"r").read()
    m=re.search(r'nonuniform\s+List<scalar>.*?\(\s*([-+0-9.eE]+)', txt, re.S)
    if m: return float(m.group(1))
    m=re.search(r'uniform\s+([-+0-9.eE]+)\s*;', txt)
    return float(m.group(1)) if m else float("nan")

def first_vec_mag(fp):
    txt=open(fp,"r").read()
    m=re.search(r'nonuniform\s+List<vector>.*?\(\s*\(\s*([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s*\)', txt, re.S)
    if not m:
        m=re.search(r'uniform\s*\(\s*([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s*\)\s*;', txt)
    if not m: return float("nan")
    x,y,z=map(float,m.groups()); return math.sqrt(x*x+y*y+z*z)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--rho", type=float, default=1060.0)
    ap.add_argument("--case", default=".")
    ap.add_argument("--time", default="latest")
    ap.add_argument("--fields", nargs="+", default=["p","wallShearStress"])
    a=ap.parse_args()

    case=os.path.abspath(a.case)
    if a.time=="latest":
        ts=list_time_dirs(case)
        if not ts:
            print("ERROR: cannot find time directories", file=sys.stderr); return 1
        tdir=ts[-1]
    else:
        tdir=a.time

    tpath=os.path.join(case, tdir)
    if not os.path.isdir(tpath):
        print(f"ERROR: time directory not found: {tpath}", file=sys.stderr); return 1

    print(f"[pa_convert] case={case}")
    print(f"[pa_convert] time={tdir}")
    print(f"[pa_convert] rho={a.rho}")

    if "p" in a.fields:
        src=os.path.join(tpath,"p")
        if os.path.exists(src):
            dst=os.path.join(tpath,"p_Pa")
            convert_scalar_file(src,dst,"p_Pa",a.rho)
            print(f"[pa_convert] wrote {os.path.relpath(dst)}")
            try:
                ratio = first_scalar(dst)/first_scalar(src)
                print(f"[check] p_Pa/p ≈ {ratio:.3f} (期待 1060)")
            except Exception:
                pass
        else:
            print("[pa_convert] skip p: not found")

    if "wallShearStress" in a.fields:
        src=os.path.join(tpath,"wallShearStress")
        if os.path.exists(src):
            dst=os.path.join(tpath,"wallShearStress_Pa")
            convert_vector_file(src,dst,"wallShearStress_Pa",a.rho)
            print(f"[pa_convert] wrote {os.path.relpath(dst)}")
            try:
                ratio = first_vec_mag(dst)/first_vec_mag(src)
                print(f"[check] |wss_Pa|/|wss| ≈ {ratio:.3f} (期待 1060)")
            except Exception:
                pass
        else:
            print("[pa_convert] skip wallShearStress: not found")

    print("[pa_convert] done"); return 0

if __name__=="__main__":
    sys.exit(main())
