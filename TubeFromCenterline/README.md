# TubeFromCenterline
離散曲線を入力として、チューブ形状の3D表面データを出力するC++コード。

## Features
- 入力ファイルの形式は (*.csv) 出力ファイルの形式は (*.stl)
- 点群にそって半径も定義でき、半径可変のチューブが作れる
- 出力されるチューブの両端は開放されている

## Environment
- Windows11
  - VisualStudio 2022

## setup
本コードはVTKライブラリを利用しているので、事前に [VTKをビルド](https://qiita.com/ononono73/items/f336cea22c3f0813406d)
する必要がある

## usage
VTKのSDKのビルドに用いたツールチェーンと揃える必要があるので、C++ソースコードのビルドも `x64 Native Tools Command Prompt for VS 2022` で行ってください <br>
Copy `TubeFromCenterline.cpp` and `CMakeLists.txt` in your directory, and build by below commands
```
mkdir build
cd build
cmake ..
cmake --build . --config Release
```

and execute <br>
(実行は、どのCLIでもいい)
```
cd Release
.\TubeFromCenterline.exe
```

### メッシュ分割について
管軸方向の分割数は、読み込む曲線点群(*.csv) の点群数で決まる <br>
円周方向の分割数は、コード内の
```
const unsigned int nTv = 64;
```
で制御しており、実行時にも入力できる。<br>

### 半径について
読み込んだ曲線点群(*.csv)が`radius`カラムを持つ場合、点群に沿って変化する半径で表面が出力される。
<br>
csvファイルに半径情報がない場合、半径は一律になり、コード内の
```
double tubeRadius = 0.8;
```
で制御する。これは実行時にも入力できる。

