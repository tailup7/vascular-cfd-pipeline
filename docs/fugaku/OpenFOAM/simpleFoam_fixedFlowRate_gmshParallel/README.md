# OpenFOAM parallel processing on Fugaku
使い方 : 

0. 富岳のログインノードにアクセスし自分の作業ディレクトリにこのフォルダをコピーする. (ログインノードへのアクセスは`docs/fugaku/environment`を参照)
1. 解析メッシュのサンプルとして`BH0017L.msh`を `vascular-cfd-pipeline/data/`においています。このディレクトリにコピーしてください. 

2. ログインノードで
   ``` bash
   chmod +x run.sh
   pjsub run.sh
   ```

3. 途中計算は `output...../0/1/stdout.1.0` に出力される.


### 注意点
+ gmshで作成したメッシュファイル用に
  `gmshToFoam foo.msh` および `transformPonits ` のコマンドがジョブスクリプト中に入っているので、ICEM CFDで作成したメッシュで解析したい場合はジョブスクリプトを書き換えてください
+ 富岳の計算ノードは1ノード当たり48コアある。しかし, 並列数(ジョブスクリプト中の`NP`)が多い方が速いとは限らない。例えば, `vascular-cfd-pipeline/data/` 程度のメッシュ数の場合, 並列数8~16が適当だと思われる.
+ `0/U` ファイルについて
