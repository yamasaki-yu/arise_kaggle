# KAGGLE用分析環境の構築

## 操作の流れ

1. [GCEのVMインスタンスの立ち上げ](#GCEのVMインスタンス立ち上げ)
1. [ファイアウォールの設定](#ファイアウォールの設定)
1. [GCE内の処理](#GCE内の処理)

    1. [GCSとマウント](#GCSとマウント)
    1. [GitHubとの連携](#GitHubとの連携)
    1. [kaggle用のimageを取得](#kaggle用のimageを取得)
    1. [containerの起動](#containerの起動)

1. [コンテナ内の処理](#コンテナ内の処理)

    1. [GPUの有効化](#GPUの有効化)
    1. [jupyterの起動](#jupyterの起動)
1. [500Gデータのダウンロード](#データのダウンロード)

## GCEのVMインスタンス立ち上げ

https://console.cloud.google.com/compute/instancesAdd

||||
|---|---|---|
|リージョン||us-****|
|マシン構成|マシンタイプ|n1-standard-[8-96]|
|GPUのタイプ||任意|
|GPUの数||任意|
|ブートディスク|オペレーティングシステム|Deep Learning on Linux|
||バージョン|任意|
||サイズ|60以上※1|
|IDとAPIへのアクセス|アクセススコープ|各APIにアクセス権を設定(ストレージを「フル」に変更)※2|
|ファイアウォール||HTTP,HTTPSトラフィックを許可する|

※1 後からでも追加可能らしい

※2 後からでも設定可能

## ファイアウォールの設定

https://console.cloud.google.com/networking/firewalls/add

デフォルトでは、80と443ポートしか公開されていないので、jupyterの8888ポートを公開する

||||
|---|---|---|
|名前||任意|
|ターゲット||任意※1|
|ターゲットタグ||任意※2|
|サービスアカウント||このプロジェクト内※2|
|プロトコルとポート|tcp(チェック)|8888(jupyterの場合)|

※1 セキュリティ的には指定されたターゲットタグもしくはサービスアカウントにした方がよい

※2 「ターゲット」の設定次第。ターゲットがタグしていならば、記載したタグ名をインスタンスの設定にあとでタグを追加。

## GCE内の処理

### GCSとマウント

※前もってストレージを作成しておく必要がある。

https://console.cloud.google.com/storage/browser

* gcsfuseのインストール
```bash
export GCSFUSE_REPO=gcsfuse-`lsb_release -c -s`
echo "deb http://packages.cloud.google.com/apt $GCSFUSE_REPO main" | sudo tee /etc/apt/sources.list.d/gcsfuse.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
sudo apt-get update
sudo apt-get install gcsfuse
```

* マウント場所を作成して、そこにマウントする
```bash
mkdir ${LOCAL_DIR} # LOCAL_DIRはマウント先
gcsfuse ${BACKET_NAME} ${LOCAL_DIR} #BACKET_NAMEはGCSのバケット名
```

### GitHubとの連携

※前もってgithubのアカウントを作成しておく必要がある

https://github.com/

* 公開鍵の生成

```bash
ssh-keygen -t rsa

# このあと3回Enter
```

* 公開鍵の確認
```bash
cat ./.ssh/id_rsa.pub

# 出力結果を自分のGITHUBアカウントの「右上のボタン→Settings→SSH and GPG keys→New SSH key」のKeyに貼り付け
```

### kaggle用のimageを取得

```bash
# clone
git clone git@github.com:Kaggle/docker-python.git
cd docker-python

# Dockerfileの修正
vi gpu.Dockerfile
```
```Docker
# ポートの公開
EXPOSE 8888

# CUDAのversion変更
# 1→0
ENV CUDA_MINOR_VERSION=0
# 243→130
ENV CUDA_PATCH_VERSION=130
```


```bash
# --gpuオプションでビルド
./build --gpu

# イメージを確認
docker images
```

### containerの起動
```bash
docker run --runtime nvidia -itd --name [CONTAINER_NAME] -p 8888:8888 kaggle/python-gpu-build # PATH_TO_DIRはマウント元、WORKDIRはマウント先
docker exec -it [CONTAINER_NAME] /bin/bash
```

## コンテナ内の処理

### GPUの有効化

https://github.com/Kaggle/docker-python/issues/361#issuecomment-448093930

```bash
#環境変数の変更
export LD_LIBRARY_PATH=/usr/local/cuda/lib64

# python内で確認
python
```

```python
import torch
torch.cuda.is_available()

>>>TRUE
```

### jupyterの起動

* 普通に起動(これだと誰でもアクセス可能)
```
jupyter notebook --port 8888 --ip 0.0.0.0 --allow-root
```

* SSL・パスワードの設定(任意)
    *   パスワードのハッシュ値を取得
    ```bash
    jupyter console
    >>> from notebook.auth import passwd
    >>> passwd()
    # この後パスワードを打ち込む


    #==> sha1:*********** 
    ``` 

    * 鍵の設定
    ```bash
    cd ~/.jupyter
    openssl req -x509 -nodes -newkey rsa:2048 -keyout mykey.key -out mycert.pem

    apt-get install vim
    vi ~/.jupyter/jupyter_notebook_config.py
    ```

    * jupyter_notebook_config.py
    ```python
    c = get_config()

    c.NotebookApp.certfile = u'/absolute/path/to/your/certificate/mycert.pem'
    c.NotebookApp.keyfile = u'/absolute/path/to/your/certificate/mykey.key'
    c.NotebookApp.ip = '*'
    c.NotebookApp.password = u'sha1:********************************************'
    c.NotebookApp.open_browser = False
    c.NotebookApp.port = 8888
    ```

    * SSLでjupyterを立ち上げ

    ```
    jupyter notebook --certfile=~/.jupyter/mycert.pem --keyfile ~/.jupyter/mykey.key
    ```

* アクセス先

        http://[PORT]:8888/?token=******  # SSLを設定していない場合

        https://[PORT]:8888/ # SSLを設定した場合


## データのダウンロード

※他にいい方法があると思います

* 前提

    * kaggleにログインし、cookieファイルを取得
↓以下のChromeの拡張機能が良いです
https://chrome.google.com/webstore/detail/cookiestxt/njabckikapfpffapmjgojcnbfjonfjfg

    * GCSにcookieファイルとdata_load.shをダウンロード

```bash
# GCE上
cd ${LOCAL_DIR} # GCSをマウントした場所
sh data_load.sh
```

# まだ改善できること
* Kaggleが作成したDockerFileをそのまま利用しているため、必要のないものもインストールしています。

* dlib・cmake等は手動でインストールする必要があります。

* コンテナから直接GCSのデータを触れないので、GCEでデータの移動(cpコマンド)が必要です。

* こっちの方がスマート(多分高いけど)
https://www.kubeflow.org/docs/gke/

* etc...

# 参考

* Docker
https://qiita.com/yota-p/items/affe6d970ac4896d6e70

* Jupyter
https://jupyter-notebook.readthedocs.io/en/latest/public_server.html

* Cookie
https://blog.goo.ne.jp/dak-ikd/e/ca9a6f1b6c0ec36f3b23fdf3cc234da9

* kaggle
https://github.com/Kaggle/docker-python

