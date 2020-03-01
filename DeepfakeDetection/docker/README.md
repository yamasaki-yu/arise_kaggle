# KAGGLE用分析環境の構築

## 操作の流れ

1. [GCEのVMインスタンスの立ち上げ](#GCEのVMインスタンス立ち上げ)
1. [GCE内の処理](#GCE内の処理)

    1. [GCSとマウント](#GCSとマウント)
    1. [GitHubとの連携](#GitHubとの連携)
    1. [kaggle用のimageを取得](#kaggle用のimageを取得)
    1. [containerの起動](#containerの起動)

1. [コンテナ内の処理](#コンテナ内の処理)
1. [500Gデータのダウンロード](#データのダウンロード)

## GCEのVMインスタンス立ち上げ

* リージョン

    us-central,east,westが安い

* マシンの構成

    * マシンタイプ

        60GBあった方がよい(30GBでも動くは動く)
    
* CPUプラットフォーム

    自動でよい
    
* GPU(追加)

    * GPUのタイプ

        TeslaK80じゃないと高い
    
    * GPUの数

        2個は欲しい
    
* ブートディスク

    * OS

        OSはなんでもよい(Deep Learning on Linuxがおすすめらしい)

    * サイズ

        100GBは欲しい

* IDとAPIへのアクセス

    各APIにアクセス権を設定

    * ストレージ

        フル(これじゃないとGCSに書き込めない)

* ファイアウォール

    HTTP,HTTPSを許可

## GCE内の処理

### GCSとマウント

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

* 公開鍵の生成

```bash
ssh-keygen -t rsa

# このあと3回Enter
```

* 公開鍵の確認
```bash
cat ./.ssh/id_rsa.pub

# 出力結果をGITHUBに貼り付け
```

### kaggle用のimageを取得

```bash
# clone
git clone git@github.com:Kaggle/docker-python.git
cd docker-python

# --gpuオプションでビルド
./build --gpu

# イメージを確認
docker images
```

### containerの起動
```bash
docker run -itd --name [CONTAINER_NAME] -p 8888:8888 -v ${PATH_TO_DIR}:${WORK_DIR} kaggle/python-gpu-build # PATH_TO_DIRはマウント元、WORKDIRはマウント先
docker exec -it [CONTAINER_NAME] /bin/bash
```

## コンテナ内の処理

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

