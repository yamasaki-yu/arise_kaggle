# DeepFace Detection

### Tools

#### extract\_face\_image.py

動画が格納されているディレクトリから，各動画の顔画像をフレームごとに抽出する

- Usage

  ```
  usage: extract face images from a movie [-h] [-m MOVIE] [-o OUT_DIR]
                                          [-g GROUND_TRUTH]
  
  optional arguments:
    -h, --help            show this help message and exit
    -m MOVIE, --movie MOVIE
                          path to movie file or directory
    -o OUT_DIR, --out-dir OUT_DIR
                          path to output directory
    -g GROUND_TRUTH, --ground-truth GROUND_TRUTH
                          path to ground truth json
  ```

- Example  
  ```
  > python extract_face_image.py -m /tmp/deepfake-detection-challenge/train_sample_videos -o /tmp/faces -g /tmp/metadata.json
  ```
