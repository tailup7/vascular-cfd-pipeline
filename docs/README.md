# meshing_deformのアルゴリズム

ここではmeshing_deformの仕様について説明する。自分用に書き残している部分が多い。

## 構成
``` bash
  vascular-cfd-pipeline/meshing_deform/src (root)
   ├─ meshing/                       
   │       ├─ main.py                   
   │       └─ config.py
   ├─ deform/
   │       ├─ centerline/ 
   │       │      ├─ adjust_num_of_cl.py # TODO:バッチ処理に組み込む
   │       │      └─ alignment.py        # 単体でも実行可能
   │       ├─ smooth/
   │       │      ├─ edgeswap.py         # TODO:単体で実行可能にする
   │       │      └─ smoother_vtk.py     # TODO:単体で実行可能にする
   │       ├─ main.py
   │       └─ config.py
   ├─ postcheck/  
   │       ├─ hausdorff.py
   │       ├─ openfoam_checkmesh.py      # TODO:単体で実行可能にする
   │       └─ visualize_surfacetriangle_with_correspond_centerlinenode.py  
   └─ commonlib/
           ├─ node.py          
           ├─ cell.py      
           ├─ boundarylayer.py
           ├─ meshinfo.py   
           ├─ func.py            
           └─ utility.py
```


## ファイル形式
gmshファイルでは、nodeIDは1スタート。<br>
vtkファイルでは、nodeIDは0スタート。<br>
コード内では、表面NodeのIDは1スタートに統一している<br>
なので、`myio.read_vtk_surfacemesh()` ではnodeIDを1スタートにしてNodeインスタンス生成、`mesh.nodes`への格納をしている

+ 本コードで変形時に読み込む(*.msh)ファイルの中身の形式について必要なこととして、例えばWALL三角形パッチを構成するnodeが(重複を許さずに)100個あったとして、それらのnodeIDがすべて1~100に収まっている(IDが飛び飛びではない、つまり、WALLを構成するnode群の並びのなかに例えばINTERNALなどのnodeが混じっていない)こと。それため、本コードのmeshing実行時には、`$Node`セクションにおいて、表面(WALL)上のNodeは最初に列挙される。 ( ← この制約を利用しているのは、たしか、変形後の押し出しなどでnodeを追加していくときに、変形後の表面nodeのIDが例えば 1 ~ 100 に収まってくれていることで 変形後.mshファイルのnodeIDが素直に追加していけるようになっている点。)
+ 三角形の頂点の並びは、反時計回り。三角形自体の並びには規則性はないが、一応 WALLの三角形パッチが最初に列挙してある。
+ コード内では、中心線NodeのIDは0スタートに統一している


```
$MeshFormat
2.2 0 8
$EndMeshFormat
$PhysicalNames
4
2 10 "WALL"      
2 20 "INLET"
2 30 "OUTLET"
3 100 "INTERNAL"
$EndPhysicalNames
$Nodes
14424
1 -1.1668802499771118 17.204805374145508 -7.967270851135254
2 -7.390712738037109 10.74311351776123 -6.541959285736084
... 省略
19885 0.0517762725573398 -2.298874032157622 0.1428839143356736
19886 -1.715317027358849 -1.467006516647876 11.84414823215792
$EndNodes
$Elements
37141
1 2 2 10 10 98 100 99
2 2 2 10 10 101 103 102
... 省略
4580 2 2 10 10 76 1849 2213
4581 2 2 20 11 11556 11555 13859
... 省略
4626 2 2 20 11 13861 13853 13856
4627 2 2 30 13 11545 11637 13873
... 省略
4668 2 2 30 13 13874 13875 13871
4669 3 2 20 12 1 22 2330 2309
... 省略
4758 3 2 20 12 9254 9253 11561 11562
4759 3 2 30 14 5 81 2389 2313
... 省略
4848 3 2 30 14 9329 9237 11545 11637
4849 4 2 100 1 11693 14020 12086 14035
... 省略
14241 4 2 100 1 12688 14149 12794 14342
14242 6 2 100 1 2406 2408 2407 98 100 99
... 省略
37141 6 2 100 1 11616 13389 13753 9308 11081 11445
$EndElements



Gmshの `$Elements` の形式
element_id   elem_type   num_tags   tag1   tag2 ... tagN   node1   node2   node3 ...

```

| フィールド                        | 意味                               |
| ---------------------------- | -------------------------------- |
| elem_id                      | Gmsh が要素に付けた連番                   |
| elem_type                    | 2=三角形, 3=四角形, 4=テトラ, 6=プリズム      |
| num_tags                     | 後ろに続く tag の数                     |
| **tag1 = Physical Group ID** | WALL, INLET, OUTLET, INTERNAL など |
| tag2                         | elementary entity（ジオメトリID）       |
| tag3,4…                      | 他にも Gmsh は追加情報を置ける               |
| node_ids                     | 要素を構成するノードの Gmsh ノードID           |


```
Gmshのプリズムは頂点を次の順で記述する
「反時計回り, かつ, 底面→上面」
   
         外側
             
      3 ー ー 5
      | \   / |
      |  \ /  | 
      |   4   |
      |   |   |
      0---|---2
       \  |  /
        \ | /
          1

       形状の内部
```

特に本コードで出力する(.msh)ファイルに関しては、表面メッシュ(WALL)のnode及び三角形パッチを最初に格納するので

+ `$Nodes` セクションの最初のnodeはすべてWALLを構成するnode
+ `$elements`セクションの最初のelementは WALL三角形パッチ
+ コード内の変数 `triangles_WALL` リストはそのまま `surface_triangles`リストであり、IDも1スタートで(`myio.read_vtk_surfacemesh()`参照)、`original_mesh.msh`ファイル出力時の `elem_id` にそのまま使われる。
+ meshing処理中の `surface_triangles` リストの順番と、出力される`original_mesh.msh`ファイルのWALL三角形パッチの記述順は同じ。
  
WALL三角形パッチと、それを構成する表面nodeに関しては、(.msh) に記述されるIDをそのままコード内でのidインスタンス変数とすることで、変形前後でIDを保持する。


### vtkファイル形式
vtkファイルでは、`surfacemesh_original.vtk`を見れば分かるが、nodeセクションにはIDが明示的に記述されず、その記述順番(0スタート)を持ってnodeIDとし、のちのcellsセクションでnodeIDによってcellを記述する。<br>
すなわち、**`surface_nodes`の読み書きの順番と、`surface_triangles`の読み書きの順番は対応している必要がある**。<br>
特に注意すべきは、`surface_nodes`をvtkに出力するときは、必ずもともとの`surface_node`インスタンスが持っていたIDの順番に従って出力する。

------


### 0. 基準となる中心線(*.csv)と表面(*.stl)を読み込む<br>
  `node_centerline`のインスタンス変数である`id`は、0はじまり。
### 1. 半径計算 
読み込んだ中心線(*.csv)に`radius`カラムが無い場合、中心線(*.csv)と表面(*.stl)から中心線点群の各点における半径を計算する。radiusカラムがあるときは、1. はスキップ。<br>
  `calc_radius`関数 : <br>

  ---
  
  まず表面メッシュを切りなおす(半径計算において、表面メッシュ切り直しは省略できるかもしれない)。このときメッシュの大きさを `cofig.MESHSIZE(=0.5)` で指定する

  ``` bash
  gmsh.option.setNumber("Mesh.MeshSizeMin", config.MESHSIZE*0.5)
  gmsh.option.setNumber("Mesh.MeshSizeMax", config.MESHSIZE*0.5)
  ```

  の2つめの引数は単位のない絶対値であり、メッシュの実寸をきめる。<br>
  `radius_list` および`radius_list_smooth`変数はリスト型であり、要素の個数は中心線点群数+1 <br>
  再メッシュした各表面Nodeから見て、最近接する中心線Nodeと対応付け(kdtreeの実装余地あり)。<br>
  また、各表面Nodeについて、<br>
  `find_projectable_centerlineedge`インスタンスメソッド : 
  
  ---
  
  中心線Edgeに射影できる場合は、`projectable_centerlineedge_id`および`projectable_centerlineedge_distance` インスタンス変数に値を格納する。(これらのインスタンス変数のデフォルト値は`None`である)<br>
  ここで、`projectable_centerlineedge_id` は0スタートであり`projectable_centerlineedge`の総数は中心線点群数-1 である。<br>
  ※`projectable_H_vec`は何に使う?→変形後の、半径方向への移動? <br>
  いずれの中心線Edgeにも射影できない場合は、特に何もしない
  
  ---
  
  を実行し、射影できる場合に中心線Edgeとの対応付けを行う。その後、すべての表面Nodeに対して、その表面Nodeが対応Edgeを持っている場合には、そのEdgeに`projectable_centerlineedge_distance`の値を加算し、足した回数でわって平均値とし、
``` bash
  radius0 ---- radius1  --------- radius2  -------  radius3 ------ radius4 
  
       Node0 -- Edge0 -- Node1 -- Edge1 -- Node2 -- Edge2 -- Node3 # 中心線
```
によって、Edgeから `radius_list`変数に値を与える。また、例えば表面Nodeが`Node0`より左側にある場合は、`radius0`要素に加算する。また、例えば中心線EdgeがV字に屈曲している場合で、屈曲外側に表面Nodeがあるとき、いずれの中心線Edgeにも射影できないことがある。その場合は、そのVの両方のEdge(すなわち`radius_list`要素)に、最近接中心線Nodeとの距離を加算する。<br>
`radius_list_smooth` は隣接3点で平均化した値。さらにこのリストの最初と最後の要素を`inlet_radius`,`outlet_radius`としてグローバル変数として保存し、後で使う。<br>
入力ファイルである中心線(*.csv)に`radius`カラムを追加し、`radius_list_smooth` の値を格納する。

---

### 2. BGM 生成
  `generate_pos_bgm`関数 :

  ---
  まず3Dメッシュを生成する。この時の大きさは、
  ``` bash
  gmsh.option.setNumber("Mesh.MeshSizeMin", config.MESHSIZE)
  gmsh.option.setNumber("Mesh.MeshSizeMax", config.MESHSIZE)
  ```
  であり、粗くて良い。すべてのNodeに対して `radius_list_smooth`を割り当て、メッシュ生成の時の大きさの目安値とする。(`set_edgeradius`インスタンスメソッドが少し冗長な気もするので、本当にその処理が必要か確認する(2重に平滑化している？))。<br>
  その後、生成した3Dメッシュ(及びスカラー値)を `bgm_original.msh` として出力する。

  
  ---

### 3. BGMに従って表面メッシュ生成
`make_surfacemesh`関数 : 

---

TODO : コード内でここだけ、`classify_parameter` が40で固定されている。コード内で統一していいはずなので、変数化して設定ファイルで指定出るようにした方がいい気がする。
<br>

BGMに従って表面メッシュを生成・ファイル出力した後、再度読み込んで`surfacenodes`,`surfacetriangles`, `filepath_vtk_original` という3つのグローバル変数がここで初めて登場する<br>
`surfacenodes`,`surfacetriangles` は、`make_surfacemesh`で生成したメッシュを`gmsh.write`で出力したものを、再度読み込んだもの。(なので順番はgmshで出力されるvtkファイルの上の行~下の行の順番)

---

### 4. 
`correspond_surface_to_centerlinenode` 関数内で、`mesh.triangles_WALL` に`surfacetriangles` の順番に格納する。メッシュファイルに書き出す時もこの順番。 `correspond_surface_to_centerlinenode` 関数はmeshingでもdeformでも呼び出している。

---

表面(*.vtk) を読み込む。`surfacenode_dict`変数を生成し、返す。`surfacenode` インスタンスの `closest_centerlinenode_id` インスタンス変数は、後の`make_nthlayer_surfacenode` で使う。`surfacetriangle.unitnormal_in` も使う。

---



### TODO
+ 比較のため、edgeswap後、vtkWindowedSincスムージングの後の2段階で表面メッシュを出力する
+ meshingに関しては、optionでoriginalのsurfacemeshのままテトラプリズムが作れるように、分岐を作る。またautoMeshing.pyのように、centerline不要でsurfaceだけからもmeshingできるような分岐も作る
(つまり入力によって3つの選択肢。1. stlのみで、メッシュサイズを絶対値で指定してmeshing(icemに近くオーソドックス), 2. 表面メッシュをそのまま押し出し, 3. 中心線とstlの2つのデータを読み込み、半径に応じてメッシュサイズを変える(中心線を読み込まなくてもいいようにもできるかも))
