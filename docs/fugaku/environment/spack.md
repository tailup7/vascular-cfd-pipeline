# コマンド
## `spack find foo`コマンド

input
``` bash
spack find openmpi
```
return
``` bash
-- linux-rhel8-cascadelake / %c,cxx,fortran=gcc@15.1.0 ----------
openmpi@5.0.8
-- linux-rhel8-skylake_avx512 / %c,cxx,fortran=gcc@8.5.0 --------
openmpi@5.0.8
==> 2 installed packages
```
## `spack info foo`コマンド
ビルドされていないものも含め, パッケージの定義を表示 . ビルド可能な選択肢一覧

## `which spack` コマンド
input 
``` bash
which spack
```
return
``` bash
[u00000@g25-3207c u00000]$ which spack
spack ()
{ 
    : this is a shell function from: /vol0004/apps/oss/spack/share/spack/setup-env.sh;
    : the real spack script is here: /vol0004/apps/oss/spack/bin/spack;
    _spack_shell_wrapper "$@";
    return $?
}
```
正常

## `spack spec`コマンド
spack specコマンドは, その指定でインストールしたら、最終的にどういう構成になるかを, 実際にビルドする前に完全に展開して見せるコマンド
依存関係の確認(specが成立しているか)
``` bash
spack spec openmpi@5.0.8 %gcc@12.2.0 arch=linux-rhel8-a64fx
```
意味 : 「RHEL8 + A64FX 環境で、
GCC 12.2.0 を使って OpenMPI 5.0.8 をビルドするとしたら、
依存関係を含めて最終的にどういう構成になるかを確認する」
インストール前の事故を防げる
