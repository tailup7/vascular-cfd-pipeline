# Batch Processing
現在、以下の処理をバッチで行える
1. 表面形状(*.stl) からテトラプリズムメッシュを生成する
2. 基準中心線と目標中心線を使い、テトラプリズムメッシュを変形させる
3. 生成あるいは変形させて得たテトラプリズムメッシュをOpenFOAMの`CheckMesh`コマンドで検査する

## Environment
+ **Linux**

## `batch_auto.py` の Usage
先に`meshing_deform`のためのvenv仮想環境を作成しておくこと

0. **入力データの用意**
   + メッシュの生成がしたい場合 : <br>
     `meshing-deformation-cfd-batch/inputs/original/`に、表面(.stl)とその中心線(.csv) を入れる <br>
     **Note**
     + 一回のバッチ処理でメッシュ生成は一回しか行えないので、表面(.stl)と中心線(.csv)は`meshing-deformation-cfd-batch/inputs/original/`に1つずつしか入れられない。
     + 表面(.stl)は両端が開放されている必要がある。中心線(.csv)は形状の両端まで届いている必要がある。
     + 中心線(.csv)ファイルのはじめに記述されている点がある方の面が流体解析時の`INLET`になる
   + メッシュの変形がしたい場合 : <br>
     `meshing-deformation-cfd-batch/inputs/original/`に、基準となるテトラプリズムメッシュ(.msh)とその中心線(.csv)を入れ、`meshing-deformation-cfd-batch/inputs/target/`に変形目標となる中心線(*.csv)を入れる。<br>
     **Note**
     + `meshing-deformation-cfd-batch/inputs/target/`に複数の中心線を入れている場合、`meshing-deformation-cfd-batch/inputs/original/`に入っているメッシュ(*.msh)を基準モデルとして、すべての目標中心線に対して変形メッシュを作成する
     + 中心線(.csv)ファイルのはじめに記述されている点がある方の面が流体解析時の`INLET`になる
     + 基準中心線と目標中心線で点群数が一致している必要がある
   + メッシュの生成 + その変形 がしたい場合 : <br>
     `meshing-deformation-cfd-batch/inputs/original/`に、表面(.stl)とその中心線(.csv) を入れ、`meshing-deformation-cfd-batch/inputs/target/`に目標中心線(.csv) (複数可)を入れる
   
2. 仮想環境を activateする
   ``` bash
   cd meshing-deformation-cfd-batch
   source venv/bin/activate
   ```
3. `batch_auto.py`を実行する
   ``` bash
   cd batch
   python batch_auto.py
   ```
4. 結果の確認 <br>
   `meshing-deformation-cfd-batch/runs/`に結果が出力される。

