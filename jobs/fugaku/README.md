# 概要

`batch/batch_auto.py`を富岳上で実行するためのジョブスクリプトです. 入出力ファイルの動きからOpenFOAM実行まで, ローカルで`batch_auto.py`を実行する場合と同じになります.

# 使い方
前提として, 
+ すでに[vascular-cfd-pipelineの富岳上での環境構築](../../docs/fugaku/environment)が完了していること
+ `run_batch.sh`内の, ユーザIDを示す`u00000`(やグループID`hp000000`) を自分のものに書き換えること

1. 富岳ログインノードにアクセスし, このジョブスクリプト(`run_batch.sh`)のある階層まで移動する
   ``` bash
   cd $PROJECT_ROOT/jobs/fugaku
   ```
2. `run_batch.sh`をジョブ投入する
   ``` bash
   chmod +x run_batch.sh
   pjsub run_batch.sh
   ```

# 処理の流れ

+ **`run_batch.sh`** をジョブ投入する
  
  + 並列数を定義(`export NP=4`)
  
  + 環境設定 (OpenFOAMをsource, Pythonを`spack load`, Gmshをリンク, python venv を activate)

  + **`batch/batch_auto.py`** を呼ぶ
 
     + `inputs/original/`および`inputs/target/`にある入力ファイルを読み込み自動で基準メッシュ, 変形メッシュを生成
     + **`src/postcheck/openfoam_checkmesh.py`** を呼ぶ。
       
        + 流体解析を実行するにあたり`openfoam-case/` にあるどのケースフォルダを使うかを指定し、メッシュ出力先のフォルダにコピーしたうえで、メッシュ生成物に対してOpenFOAMの機能であるcheckMeshを行う。checkMesh OKなら次へ。 
       
     + コピーしてきたケースフォルダ内の **`simpleParallel.sh`** を呼ぶ。
         + `system/decomposeParDict`内の`numberOfSubdomains`を、run_batch.shで設定した並列数に書き直す
         + 必要な前処理・後処理も含め、ソルバの実行を行う。  
