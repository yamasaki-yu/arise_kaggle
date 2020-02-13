import os
import os.path as osp
import json
import argparse
from glob import glob
from tqdm import tqdm
import cv2 as cv
import face_recognition as farec

def movie_info(movie_path):
    '''get information of the movie
    
    Args:
        movie_path: path to a movie
    
    Return:
        {
            'fps': frames per second,
            'num_frames': frame counts,
            'height': height of frames,
            'width': width of frames,
            'channel': channels of frames
        }
    '''
    cap = cv.VideoCapture(movie_path)
    
    fps = cap.get(cv.CAP_PROP_FPS)
    num_frames = cap.get(cv.CAP_PROP_FRAME_COUNT)
    height = cap.get(cv.CAP_PROP_FRAME_HEIGHT)
    width = cap.get(cv.CAP_PROP_FRAME_WIDTH)
    channel = cap.get(cv.CAP_PROP_CHANNEL)
    
    cap.release()
    
    return {
        'fps': fps,
        'num_frames': num_frames,
        'height': height,
        'width': width,
        'channel': channel
    }
    
def read_frames(movie_path):
    '''read frames from a movie
    
    Args:
        movie_path: path to movie file
        
    Return:
        yield (frame_index:int, frame: shape of (height, width, channel))
    '''
    cap = cv.VideoCapture(movie_path)
    
    index = 1
    while(cap.isOpened):
        has_frame, frame = cap.read()
        if has_frame:
            yield (index, frame)
            index += 1
        else:
            cap.release()
            break
        
def extract_faces(image):
    '''extract face image from an image
    
    Args:
        image: an image with shape of (height, width, channel)
        
    Return:
        face image with shape of (height, width, channel)
    '''
    res = []
    detected = farec.face_locations(image)
    for det in detected:
        ymin, xmax, ymax, xmin = det
        face = image[ymin:ymax, xmin:xmax]
        res.append(face)
        
    return res

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser('extract face images from a movie')
    parser.add_argument('-m', '--movie', help='path to movie file or directory')
    parser.add_argument('-o', '--out-dir', help='path to output directory')
    
    args = parser.parse_args()
    
    # check output directory is not a file
    assert osp.isfile(args.out_dir) == False
    
    # check the specified movie exists and get list of target movies
    assert osp.isfile(args.movie) or osp.isdir(args.movie)
    movies = []
    if osp.isfile(args.movie):
        movies = [args.movie]
    else:
        movies = list(glob(osp.join(osp.abspath(args.movie), '**', '*'), recursive=True))
    
    
    for movie in tqdm(movies, desc='ITER FRAMES'):
        
        # create output directory
        movie_name = osp.splitext(osp.basename(movie))[0]
        os.makedirs(osp.join(args.out_dir, movie_name), exist_ok=True)
        
        # get meta information of the movie
        info = movie_info(movie)
        json.dump(info, open(osp.join(args.out_dir, movie_name, 'info.json'), 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        
        # extract faces
        for frame_idx, frame in tqdm(read_frames(movie), desc=movie_name, total=int(info['num_frames'])):
            faces = extract_faces(frame)

            for idx, face in enumerate(faces):
                out_file = 'FRAME-{}__FACE-{}.png'.format(frame_idx, idx+1)
                out_path = osp.join(args.out_dir, movie_name, out_file)
                cv.imwrite(out_path, face)
        