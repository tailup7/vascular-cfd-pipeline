# OpenFOAMをソースからビルドする
[dynamicCode](#付録)や[自作ソルバ](#付録)を使う方向けのOpenFOAMの環境構築手順です。ここでの手順は、[HPCI 富岳ユーザポータル OpenFOAM-v2412構築手順](https://www.hpci-office.jp/info/pages/viewpage.action?pageId=419594375)に準拠しています。このサイトを閲覧するにはHPCIアカウントを取得しているかローカルアカウントを作成している必要があります。

## 手順

+ **1.** ログインノードに接続します(手順略)

+ **2.** [HPCI 富岳ユーザポータル OpenFOAM-v2412構築手順](https://www.hpci-office.jp/info/pages/viewpage.action?pageId=419594375)の **0.準備** 、**1.展開** 、**2.修正** 、**3. ビルド** まで行います。この手順書にも書かれているように、データ領域(`/vol0002/mdt1/data/hp000000/u00000/`) で行うとよいです。

+ **3.** 計算ノード上で`wmake`ツール群を作り直します

   以下のコマンドで計算ノードに入る
   ``` bash
   pjsub --interact -g hp000000 -x PJM_LLIO_GFSCACHE=/vol0002:/vol0004 -L "node=1,elapse=01:00:00" --sparam wait-time=300
   ```
   OpenFOAM環境を読み込んでから、wmakeツール群をビルドしなおす
   ``` bash
   # ソースビルドしたOpenFOAMの環境を読み込む。自身のOpenFOAMをビルドしたパスに書き直してください。
   cd /vol0002/mdt1/data/hp000000/u00000/OpenFOAM/OpenFOAM-v2412
   source etc/bashrc
   # wmakeツール群のビルド
   (cd wmake/src; make clean; make)
   ```

### 動作確認 チュートリアルケースの実行(dynamicCode)

dynamicCodeを使えるかの確認として、`tutorials/incompressible/simpleFoam/pipeCyclic`を実行してみてください。このケースはINLET条件にdynamicCodeを使用しています。ジョブ投入するときのジョブスクリプト中で、SpackのOpenFOAMではなく、今回ビルドしたOpenFOAMをsourceするのを忘れないでください。

### 動作確認 カスタムソルバ
**カスタムソルバとは**

自分の解析したい物理モデルや数値スキームが標準ソルバにない場合に、自分でソルバを作ったり、標準ソルバを改変して対応することがある。これを自作ソルバとかカスタムソルバと呼ぶ。(ただしほとんどの場合は設定ファイルの変更だけで対応できる。)


筆者の試した限りでは**Spack版OpenFOAMでは自作ソルバのビルド・実行ができず**、**ソースビルドしたOpenFOAMではビルド・実行できる**ことを確認した。以下では検証のために、標準ソルバ(例えばsimpleFoam)のmainファイルに1行だけコードを追加し、計算ノードでビルド・実行ができるかを、Spack版OpenFOAMとソースビルドOpenFOAMのそれぞれで試し、その手順を書いた。

**Spack版OpenFOAMの場合**

1. 標準ソルバである`\applications\solvers\incompressible\simpleFoam`フォルダを、ユーザー作業ディレクトリに自作ソルバ用のフォルダをつくり、そこにコピーする(フォルダ名は`mySimpleFoam`とかにしておく)
   ``` bash
   # ログインノードで
   . /vol0004/apps/oss/spack/share/spack/setup-env.sh
   spack load openfoam@2412 arch=linux-rhel8-a64fx

   # 確認コマンド。飛ばしてよいです。
   echo $WM_PROJECT_DIR
   # /vol0004/apps/oss/spack-v1.0.1/opt/spack/linux-a64fx/openfoam-2412-khy4ckt7vcqv5ssnc5vnqevlxydx4uzn
   echo $WM_PROJECT_USER_DIR
   # /home/u00000/OpenFOAM/u00000-v2412
   echo $FOAM_APPBIN
   # /vol0004/apps/oss/spack-v1.0.1/opt/spack/linux-a64fx/openfoam-2412-khy4ckt7vcqv5ssnc5vnqevlxydx4uzn/platforms/linux64FujitsuDPInt32-spack/bin
   echo $FOAM_USER_APPBIN
   # /home/u00000/OpenFOAM/u00000-v2412/platforms/linux64FujitsuDPInt32-spack/bin

   mkdir -p $WM_PROJECT_USER_DIR/applications/solvers
   cd $WM_PROJECT_USER_DIR/applications/solvers
   cp -r $WM_PROJECT_DIR/applications/solvers/incompressible/simpleFoam mySimpleFoam
   cd mySimpleFoam
   ```
   
2. メインファイルの名前を変更し、合わせて`Make/files`の中身も書き換える
   ``` bash
   mv simpleFoam.C mySimpleFoam.C
   ```

   ``` bash
   sed -i 's/simpleFoam.C/mySimpleFoam.C/' Make/files
   sed -i 's|\$(FOAM_APPBIN)/simpleFoam|\$(FOAM_USER_APPBIN)/mySimpleFoam|' Make/files
   ```

   下2行のコマンドでやっていることは、`Make/files`の中身を以下のように変更している

   変更前
   ``` files
   simpleFoam.C

   EXE = $(FOAM_APPBIN)/simpleFoam
   ```
   変更後
   ``` files
   mySimpleFoam.C

   EXE = $(FOAM_USER_APPBIN)/mySimpleFoam
   ```

3. `mySimpleFoam.C`に1行追加する
   ``` bash
   sed -i '/int main(int argc, char \*argv\[\])/{n; a\
   #(Enterを入力する)
       Info << "=== My modified solver is running ===" << endl;
   #(Enterを入力する)
   }' mySimpleFoam.C
   ```
   以下のように変更されていればOK

   変更前
   ``` mySimpleFoam.C
   int main(int argc, char *argv[])
   {
       argList::addNote
       (
           "Steady-state solver for incompressible, turbulent flows."
       );
   ```
   変更後
   ``` mySimpleFoam.C
   int main(int argc, char *argv[])
   {
       Info << "=== My modified solver is running ===" << endl;

       argList::addNote
       (
           "Steady-state solver for incompressible, turbulent flows."
       );
   ```
4. `wmake`を実行する
   ``` bash
   wmake
   ```
   以下のようなエラーが出る
   ``` bash 
   /vol0004/apps/oss/spack-v1.0.1/opt/spack/linux-a64fx/openfoam-2412-khy4ckt7vcqv5ssnc5vnqevlxydx4uzn/wmake/rules/General/general:48: /vol0004/apps/oss/spack-v1.0.1/opt/
   spack/linux-a64fx/openfoam-2412-khy4ckt7vcqv5ssnc5vnqevlxydx4uzn/wmake/rules/linux64Fujitsu/general: No such file or directory
   make: *** No rule to make target '/vol0004/apps/oss/spack-v1.0.1/opt/spack/linux-a64fx/openfoam-2412-khy4ckt7vcqv5ssnc5vnqevlxydx4uzn/wmake/rules/linux64Fujitsu/general'. Stop.
   Make/linux64FujitsuDPInt32-spack/options:8: *** missing separator.  Stop.
   wmake error: file 'Make/linux64FujitsuDPInt32-spack/sourceFiles' could not be created in /home/u14406/OpenFOAM/u14406-v2412/applications/solvers/mySimpleFoam
   ```

**ソースビルドしたOpenFOAMの場合**

1. 自作ソルバを用意する

   `$WM_PROJECT_USER_DIR/applications/solvers/`に改変したソルバ(`mysimpleFoam`)を作っておく(**Spack版OpenFOAMの場合** の 1. , 2. , 3., と同様の手順でよい。すでにやっていたら何もしなくてよい)

2. ソースビルドしたOpenFOAM環境を読み込み、`/wmake/rules/$WM_OPTIONS`があるか確認する

   もしすでに`spack load openfoam`していたら、念のためシェルを接続しなおしてから
   ``` bash
   source /vol0002/mdt1/data/hp000000/u00000/OpenFOAM/OpenFOAM-v2412/etc/bashrc
   ```
   でソースビルドした方のOpenFOAMの環境を読み込む。そして以下のコマンドで`/wmake/rules/$WM_OPTIONS`が存在するか確認する
   ``` bashrc
   echo "WM_PROJECT_DIR=$WM_PROJECT_DIR"  #/vol0002/.../OpenFOAM-v2412 となればOK
   echo "FOAM_APPBIN=$FOAM_APPBIN"
   echo "FOAM_USER_APPBIN=$FOAM_USER_APPBIN"
   echo "WM_OPTIONS=$WM_OPTIONS"
   ls -l $WM_PROJECT_DIR/wmake/rules
   ls -d $WM_PROJECT_DIR/wmake/rules/$WM_OPTIONS 2>/dev/null || echo "rules not found!"
   ```
   筆者が試した限りだと、`WM_OPTIONS=linuxARM64FujitsuDPInt32Opt`であるが、`wmake/rules/`にあるのは`linuxARM64Fujitsu`までで、上記コマンド(`ls -d ...`)の実行結果は`rules not found!` となる。現状だと`wmake`が`.../wmake/rules/linuxARM64FujitsuDPInt32Opt/...`を探すため、`wmake`が通らない。したがってシンボリックリンクを作成し`linuxARM64Fujitsu`を`linuxARM64FujitsuDPInt32Opt`として見せる。
   
   > ちなみにSpack版だと`WM_OPTIONS=linuxARM64FujitsuDPInt32-spack`で、`wmake/rules/`にあるのは`linuxARM64Fujitsu`までであるが、`$WM_PROJECT_DIR`(spack インストール先)には書き込み権限がないため、この方法は使えない
   
   ``` bash
   cd $WM_PROJECT_DIR/wmake/rules
   ln -s linuxARM64Fujitsu linuxARM64FujitsuDPInt32Opt
   ```
   再度確認
   ``` bash
   ls -d $WM_PROJECT_DIR/wmake/rules/$WM_OPTIONS 2>/dev/null || echo "rules not found!"
   ```
   これで`rules not found!`が出なければOK。
3. 自作ソルバをビルドし、実行する

   **計算ノードに入り**、`wmake`を実行する
   データ領域に移動し、計算ノードに入る
   ``` bash
   cd /vol0002/mdt1/data/hp000000/u00000
   pjsub --interact -g hp000000 -x PJM_LLIO_GFSCACHE=/vol0002:/vol0004 -L "node=1,elapse=01:00:00" --sparam wait-time=300
   ```
   自作ソルバをビルドする。
   ``` bash
   source /vol0002/mdt1/data/hp000000/u00000/OpenFOAM/OpenFOAM-v2412/etc/bashrc
   cd $WM_PROJECT_USER_DIR/applications/solvers/mySimpleFoam
   wclean
   wmake
   ```
   ログの最後が以下のようになれば正しくビルドできている
   ``` bash
   -o /home/u00000/OpenFOAM/u00000-v2412/platforms/linuxARM64FujitsuDPInt32Opt/bin/mySimpleFoam
   ```
   ソルバ実行できるか確認する。
   ``` bash
   mkdir -p $WM_PROJECT_USER_DIR/run
   cd $WM_PROJECT_USER_DIR/run
   cp -r $WM_PROJECT_DIR/tutorials/incompressible/simpleFoam/pitzDaily .
   cd pitzDaily
   blockMesh
   $FOAM_USER_APPBIN/mySimpleFoam | tee log.mySimpleFoam # 計算が実行される  
   grep -n "My modified solver" log.mySimpleFoam
   # 1:=== My modified solver is running === と出力されればOK
   ```
   以降は、`mySimpleFoam`というソルバを実行できるようになる。
</details>
