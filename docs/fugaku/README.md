# 富岳 環境構築
## ログインノードへのアクセス
まずログインノードへアクセスする。方法は2通り
+ OpenOnDemmendでのウェブアクセス
+ CLIからSSH接続

どちらもアクセス結果は同じ。<br>
手順は[スーパーコンピュータ「富岳」スタートアップガイド](https://www.hpci-office.jp/fugaku/user-info/user-guide.pdf)を参照してください。

## 自分の作業環境へ移動する
ログインノードには入れたら、所属するグループ(`hp120306`)のデータ領域(/data)へ移動する。<br>
※ これ以降、GroupID(`hp120306`)やUserID(`u14406`)は各自のものに読み替えてください。
``` bash
pwd     # 出力は /home/u14406
cd /vol0201/data/hp120306
```
あるいは、
``` bash
cd /vol0002/mdt1/data/hp120306
```
どちらも同じ場所を指す。<br>
``` bash
ls
# u00349  u00351  u10032  u10172  u11618  u11621  u11624  u12025  u12733
```
ここに課題参加者の作業ディレクトリがある。自分専用のディレクトリを作り、その中で作業をする。<br>
以下のコマンドで権限の確認ができる
``` bash
ls -ld .
# 出力は drwxrws--T 11 root hp120306 4096 Dec 22 19:24 .
```

自分の作業ディレクトリを作り、その中で環境構築やジョブ投入を行う。
``` bash
mkdir u14406
cd 14406
```

## ローカルとログインノード間のファイルの受け渡し
**WinSCP**を使う。<br>
手順は[スーパーコンピュータ「富岳」スタートアップガイド](https://www.hpci-office.jp/fugaku/user-info/user-guide.pdf)参照

## 計算ノードへ移動する
ここでは、ログインノード上の自身のデータ領域から、計算ノードへ入る方法を説明する。<br>
以下のインタラクティブコマンドを実行する。
``` bash
pwd    # /vol0002/mdt1/data/hp120306
pjsub --interact -g hp120306 -x PJM_LLIO_GFSCACHE=/vol0002:/vol0004 -L "node=1,elapse=00:30:00"
```
各オプションコマンドの意味
| command | 意味 | 備考 |
|---------|------|------|
|`node=1` | 計算ノードを1台確保 | |
|`elapse=00:30:00` |30分を過ぎると接続を切る | 長く設定するほどジョブが後回しにされて通りにくい |
| `-x PJM_LLIO_GFSCACHE=/vol0002:/vol0004` | Volumeの指定 | カレントディレクトリを含む`/vol0002`と、Spackの設定ファイル`setup-env.sh`がある`/vol0004`を指定する(Spack経由でOSSを使う場合に必要)|

(参考 : 利用手引書の5章5節で、「会話型ジョブ」) <br>
計算ノードには入れたら以下のように表示される

``` bash
[INFO] PJM 0000 pjsub Job 44311869 submitted.
[INFO] PJM 0081 .connected.
[INFO] PJM 0082 pjsub Interactive job 44311869 started.
[u14406@c25-5114c u14406]$
```

確認のため以下のコマンドを実行

``` bash
uname -m  # aarch64と表示されれば計算ノードに入れている
```

## Spackの利用 
OpenFOAM, Python, CMakeなどのOSSをSpackから利用する。<br>
+ Spackについては[富岳Spack利用ガイド](https://www.fugaku.r-ccs.riken.jp/doc_root/ja/user_guides/FugakuSpackGuide/)などを参考にしてみて下さい。 <br>
   ( ↑ 富岳アカウントが発行され、富岳ウェブサイトへのアクセスのためのセットアップが済んでいないと閲覧できません) <br>
+ 富岳上でのシステムPythonはPython3.6.8と古く、ユーザーがPythonスクリプトを実行するものとしては不適。また、CMakeも標準インストールされているがcmake3.26.5とやや古いので、CMakeを使う場合もパブリックインスタンスからロードするとよい。<br>
+ Spack上で Python3.12は見つからなかった。
  
### パブリックインスタンスの利用(OpenFOAM-v2412, Python3.13,CMake3.31.8)
1. まず計算ノードに入る。
   ``` bash
   cd /vol0002/mdt1/data/hp120306
   pjsub --interact -g hp120306 -x PJM_LLIO_GFSCACHE=/vol0002:/vol0004 -L "node=1,elapse=00:30:00"
   ```
2. Spackの設定を読み込む。
   ``` bash
   . /vol0004/apps/oss/spack/share/spack/setup-env.sh
   ```
   これで`spack`コマンドが使えるようになる
3. 使いたいOSSをロードする
   ``` bash
   spack find -x
   ```
   で利用可能なOSSの一覧が確認できる。
   
   1. **OpenFOAM-v2412**

      例えばOpenFOAMコマンドを使いたい場合は、
      ``` bash
      spack load  openfoam@2412 arch=linux-rhel8-a64fx # 計算ノード用のopenfoam
      ```
      で、そのシェル内でのみOpenFOAMコマンドが使える。<br>
      OpenFOAMを使うジョブ実行時には、毎回以下のようにジョブスクリプトに書く必要がある
      ``` bash
      #!/bin/bash
      #PJM -g hp120306
      #PJM -L "node=1,elapse=01:00:00"
      #PJM -x PJM_LLIO_GFSCACHE=/vol0002:/vol0004

      . /vol0004/apps/oss/spack/share/spack/setup-env.sh
      spack load openfoam@2412 arch=linux-rhel8-a64fx
      ```
   2. **Python3.13.5** <br>
   
      **Python3.13**を使いたい場合は、以下のコマンドを実行する。
      ``` bash
      spack load python@3.13.5
      ```
      で以下のように返ってくる
      ``` bash
      [u14406@a25-2008c u14406]$ spack load python@3.13.5 ==> Error: python@3.13.5 matches multiple packages.
      Matching packages:
      myari2i python@3.13.5 arch=linux-rhel8-a64fx %gcc@8.5.0
      3mtxbkd python@3.13.5 arch=linux-rhel8-a64fx %gcc@12.2.0
      fgo7g53 python@3.13.5 arch=linux-rhel8-a64fx %gcc@15.1.0
      pqyuuzx python@3.13.5 arch=linux-rhel8-a64fx %gcc@15.1.0
      xwl6x7i python@3.13.5 arch=linux-rhel8-cascadelake %gcc@15.1.0
      ez3yk2d python@3.13.5 arch=linux-rhel8-cascadelake %gcc@15.1.0
      ep364jj python@3.13.5 arch=linux-rhel8-a64fx %fj@4.10.0
      qhm66vh python@3.13.5 arch=linux-rhel8-a64fx %fj@4.12.0
      b44zqag python@3.13.5 arch=linux-rhel8-a64fx %fj@4.12.0
      Use a more specific spec (e.g., prepend '/' to the hash).
      ```
      `a64fx` ... 富岳計算ノード向け、`cascadelake` ...ログインノード向け。`gcc`...GCCでビルドされたもの, `fj`...Fujitsu Complilerでビルドされたもの。富岳ではFujitsu Complilerが基本らしいので`qhm66vh`か`b44zqag`にする。
      ``` bash
      spack load /qhm66vh # 複数のパッケージがある場合はハッシュ番号で指定する
      python --version  # Python3.13.5と返ってくればOK.
      ```
      これで、そのシェルを開いている間だけPython3.13.5が使える。<br>
      Python3.13.5で実行したい処理を含むジョブ実行時には、ジョブスクリプトに以下のように書く
      ``` bash
      #!/bin/bash
      #PJM -g hp120306
      #PJM -L "node=1,elapse=01:00:00"
      #PJM -x PJM_LLIO_GFSCACHE=/vol0002:/vol0004

      . /vol0004/apps/oss/spack/share/spack/setup-env.sh
      spack load /qhm66vh
      ```
   3. **CMake3.31.8**
      
      上2つと同様。本プロジェクトではGmshをソースビルドする際に使うので、一度計算ノードで
      ``` bash
      spack load cmake@3.31.8
      ```
      コマンドを実行しておき、`a64fx` かつ `%fj` のパッケージのハッシュ番号を確認しておく。<br>
      25/12/20時点では `ek66qoi` か `hn27egk` になる。
      
### プライベートインスタンスの利用 (Python3.11)
1. プライベートspackを使うための公式ドキュメントの手順に従う。
   ``` bash
   # ホームディレクトリへ移動
   cd $TMPDIR
   pwd # /home/u14406
   ```
   したあと、`~/.spack/upstreams.taml`を記載の通りの内容で作る
   ``` bash
   mkdir -p ~/.spack
   ls -la   #.spack があればok
   # upstreams.yaml を作成
   cat > ~/.spack/upstreams.yaml << 'EOF'
   upstreams:
     spack-public-instance:
       install_tree: /vol0004/apps/oss/spack/opt/spack
   EOF 
   ```
   ちゃんと作れたか確認
   ``` bash
   cd .spack
   cat upstreams.yaml
   cd ..
   # コンパイラ設定ができているか確認
   spack compilers # 5分くらい時間かかる
   ```
   さらに、4行のコマンドでローカル・リポジトリを追加
   
2. この設定を行って以降は、bashの接続を切って、後日計算ノードに入ったときでも、
   ``` bash
   . /vol0004/apps/oss/spack/share/spack/setup-env.sh
   spack load python@3.11.11
   ```
   で`Python 3.11.11`が3件見つかる。<br>
   25/12/20の時点では`7heyycu`が該当するので
   ``` bash
   spack load /7heyycu
   ```
   
<a id="github-clone"></a>
## ログインノードでGitHubリモートリポジトリをcloneする
富岳ではGitは既にインストールされている。計算ノードにはネットワーク制限があり、外部GitHubへのアクセスはできない。**ログインノードで git clone**すること。<br>

すでにSSH公開鍵をログインノード上で作っているか確認
``` bash
ls -la ~/.ssh
```
`id_ed25519.pub`のような`.pub`ファイルが表示されなければ、まだSSH公開鍵を作成していない。
まだ、`git clone`などしたことなければおそらくない。ので、GitHub用のSSH鍵を作成する。<br>
もしあれば、4. `git clone`する へ。
1. ログインノードで以下のコマンドを実行
   ``` bash
   ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -C "fugaku-login"
   ```
2. GitHubに登録する公開鍵を表示
   ``` bash
   cat ~/.ssh/id_ed25519.pub
   ```
   すると
   ``` bash
   ssh-ed25519 .... fugaku-login
   ```
   と表示されるはずなのでこれをコピーしてGitHubの`settings` → `SSH and GPG Keys` → `New SSH key` に張り付けて保存。(`title`はfugaku.loginとかにしておく)
3. githubへSSH接続テスト
   ``` bash
   ssh -T git@github.com
   ```
   成功のメッセージが出ればok
4. `git clone` する
   ``` bash
   git clone <repository-url>
   ```





## Spackを使わず、自分の領域にGmshをソースビルドする
1. `vascular-cfd-batch/docs/fugaku/`内の`build_gmsh.sh`および`run_python_gmsh.sh`を、自分の作業ディレクトリ`/vol0002/mdt1/data/hp120306/u14406/`にコピーする
2. gmshをソースビルドするジョブスクリプトを実行
   ``` absh
   cd /vol0002/mdt1/data/hp120306/u14406
   pjsub build_gmsh.sh # 30min ~ 1h くらいかかる
   ```
   出力される`build_gmsh.sh.<jobid>.out`ファイルの最後の方をみて、`[INFO] find gmsh.py / libgmsh.so`と出力されていればOK <br>
   **補足** : もし`Permission denied`されるなどErrorが出たら、
   ``` bash
   apck config get config
   ```
   で原因を探す。自分の場合は以前に別の`vol`でspackの設定を行ってしまったため、`install_tree`の設定にError要因があったので、以下のコマンドで修正した。
   ``` bash
   spack config --scope user edit config
   ```
   以下のように書き換えた。
   ``` bash
   # 修正前
   config:
     install_tree: /vol0003/hp120306/data/u14406/spack/opt/spack
   # 修正後
   config:
     install_tree: /volmd0002/mdt1/data/hp120306/u14406/spack/opt/spack
   ```
4. Pythonスクリプトで`import gmsh`が通るか確認
   ``` bash
   pjsub run_python_gmsh.sh
   ```

# meshing_deformプロジェクトのセットアップ
**初回**
1. [ログインノードでGitHubリモートリポジトリをcloneする](#github-clone) 
2. **spackを使わず、自分の領域にgmshをソースビルドする** の手順
3. `pyproject.toml`を`docs/fugaku`のものに置き換える
4. **計算ノードに入って**、必要な`venv`仮想環境を作る。
   ``` bash
   cd /vol0002/mdt1/data/hp120306/u14406/vascular-cfd-batch
   pjsub --interact -g hp120306 -x PJM_LLIO_GFSCACHE=/vol0002:/vol0004 -L "node=1,elapse=00:30:00"
   . /vol0004/apps/oss/spack/share/spack/setup-env.sh
   spack find python@3.11.11  # 複数ヒットしてエラーになる。ハッシュ番号が一覧表示されるはず。
   spack load /7heyycu        # 計算ノードノード向けのもの(a64fx)でfjのものを選ぶ
   python --version           # Python3.11.11
   python3 -m venv venv
   source venv/bin/activate
   pip install -e meshing_deform
   ```
5. ログインノードに戻り、`jobs/fugaku/run_batch.sh`を投げる
   ``` bash
   exit
   cd jobs/fugaku/run_batch.sh
   pjsub run_batch.sh
   ```

**2回目以降**
``` bash
cd jobs/fugaku/run_batch.sh
phsub run_batch.sh
```


## コマンド

|      コマンド     |    意味    |
| ---------------- | ---------- |
| pjstat --summary | 現在自分が投入しているジョブ一覧の確認        |
| pjstat           | 投入したジョブ一覧や、最短の開始予定時刻の表示 |
| pjsub foo.sh     | ジョブ投入コマンド                           |

ただし`pjstat`コマンドは何度か実行していると、最短の開始予定時刻 がより直近になっていたりする。<br>
またpjコマンドはログインノードでないと`commnd not found`となる

<br>
<br>
<br>
<br>

### 余談 : Spackを利用し、`pip install gmsh`でPythonスクリプトからGmshを使えるようにする(失敗)
1. 計算ノードに入り **プライベートspack** を使えるようにする。
   ``` bash
   . /home/u14406/spack/share/spack/setup-env.sh
   ```
   
2. spackにgmshがあるか確認する
   ``` bash
   spack find -lv gmsh     # Error: No package
   spack find -lv py-gmsh  # Error:No pachkages
   ```
   spackに"gmshがインストールされていない" <br>
   
3. gmshパッケージが存在するか確認
   ``` bash
   spack info gmsh
   ```
   表示されるので、
4. gmshをspackにインストールする
   ``` bash
   spack install -j 8 gmsh@4.13.1 ~fltk ~mpi target=a64fx %fj     # 30分以上かかる
   ```
   `-j 8` は並列数8でビルドする、という意味。`~fltk`は、`fltk`を外してビルドする、という意味。これで`gmsh.fltk.run()`などの可視化コマンドは使えなくなる。が、そもそも富岳計算ノードで可視化はできないので問題ない。<br>
   mpi込みでiインストールすると、インストールはできるが`spack load` がうまく行かなかったのでこれも `~mpi` で外す。<br>
   上記コマンドは、インタラクティブで計算ノードに入って実行しても、接続時間内に終了しない可能性が高いので、ログインノードからジョブとして投げる。<br>
   以下のような `install_gmsh.sh`シェルスクリプトを作成する。
   ``` bash
   #!/bin/bash
   #PJM -g hp120306
   #PJM -L "node=1"
   #PJM -L "elapse=03:00:00"
   #PJM -x PJM_LLIO_GFSCACHE=/vol0003:/vol0004

   . /home/u14406/spack/share/spack/setup-env.sh       #u14406の部分は自分のuidに書き換える

   export MAKEFLAGS="-j 8"

   spack install -j 8 gmsh@4.13.1 ~fltk ~mpi target=a64fx %fj
   ```
   **ログインノードで**、ジョブ投入コマンド
   ``` bash
   pjsub install_gmsh.sh
   ```
6. ジョブが終了したら、gmshがspackに入ったか確認し、`spack load`する
   ``` bash
   spack find -lv gmsh
   ```
   表示があれば入っているので
   ``` bash
   spack load /
   ```

→ **どうやってもうまく行かなかった** <br>
Spack経由でのGmshのセットアップは難しそうでした。

