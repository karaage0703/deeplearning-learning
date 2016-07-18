#!/usr/bin/env python
"""
Realtime image inspection 
Author shi3z https://github.com/shi3z/chainer_imagenet_tools
modified by karaage0703 2016/07/10
"""
from __future__ import print_function
import argparse
import os
import sys
import random

import cv2
import numpy as np
from PIL import Image

import chainer
from chainer import cuda
import chainer.functions as F
from chainer.functions import caffe
import cPickle as pickle

import subprocess

def jtalk(t):
    open_jtalk=['open_jtalk']
    mech=['-x','/usr/local/Cellar/open-jtalk/1.09/dic']
    htsvoice=['-m','/usr/local/Cellar/open-jtalk/1.09/voice/miku/miku.htsvoice']
    speed=['-r','1.0']
    outwav=['-ow','open_jtalk.wav']
    cmd=open_jtalk+mech+htsvoice+speed+outwav
    c = subprocess.Popen(cmd,stdin=subprocess.PIPE)
    c.stdin.write(t)
    c.stdin.close()
    c.wait()
    aplay = ['afplay','open_jtalk.wav']
    wr = subprocess.Popen(aplay)

parser = argparse.ArgumentParser(
    description='Evaluate a Caffe reference model on ILSVRC2012 dataset')
parser.add_argument('model_type', choices=('alexnet', 'caffenet', 'googlenet'),
                    help='Model type (alexnet, caffenet, googlenet)')
parser.add_argument('model', help='Path to the pretrained Caffe model')
parser.add_argument('--mean', '-m', default='ilsvrc_2012_mean.npy',
                    help='Path to the mean file')
parser.add_argument('--gpu', '-g', type=int, default=-1,
                    help='Zero-origin GPU ID (nevative value indicates CPU)')
args = parser.parse_args()

root, ext = os.path.splitext(args.model)

if ext == ".caffemodel":
    print('Loading Caffe model file %s...' % args.model, file=sys.stderr)
    func = caffe.CaffeFunction(args.model)
    print('Loaded', file=sys.stderr)
elif ext == ".pkl":
    print('Loading Caffe model file %s...' % args.model, file=sys.stderr)
    func = pickle.load(open(args.model, 'rb'))
    print('Loaded', file=sys.stderr)
else:
    print('model format is wrong. Choose modelname.caffemodel or modelname.pkl')
    quit()

if args.gpu >= 0:
    cuda.init(args.gpu)
    func.to_gpu()

if args.model_type == 'alexnet' or args.model_type == 'caffenet':
    in_size = 227
    mean_image = np.load(args.mean)

    def predict(x):
        y, = func(inputs={'data': x}, outputs=['fc8'], train=False)
        return F.softmax(y)
elif args.model_type == 'googlenet':
    in_size = 224
    # Constant mean over spatial pixels
    mean_image = np.ndarray((3, 256, 256), dtype=np.float32)
    mean_image[0] = 104
    mean_image[1] = 117
    mean_image[2] = 123

    def predict(x):
        y, = func(inputs={'data': x}, outputs=['loss3/classifier'],
                  disable=['loss1/ave_pool', 'loss2/ave_pool'],
                  train=False)
        return F.softmax(y)


cropwidth = 256 - in_size
start = cropwidth // 2
stop = start + in_size
mean_image = mean_image[:, start:stop, start:stop].copy()
target_shape = (256, 256)
output_side_length=256

categories = np.loadtxt('labels_jp.txt', str, delimiter="\t")

cam = cv2.VideoCapture(0)
count=0
tmp_name=''

while True:
    ret, capture = cam.read()
    if not ret:
        print('error')
        break
    cv2.imshow('chainer inspector', capture)
    count += 1
    if count == 30:
        image = capture.copy()
    #    image = cv2.imread(args.image)
        height, width, depth = image.shape
        new_height = output_side_length
        new_width = output_side_length
        if height > width:
            new_height = output_side_length * height / width
        else:
            new_width = output_side_length * width / height
        resized_img = cv2.resize(image, (new_width, new_height))
        height_offset = (new_height - output_side_length) / 2
        width_offset = (new_width - output_side_length) / 2
        image= resized_img[height_offset:height_offset + output_side_length,
        width_offset:width_offset + output_side_length]

        image = image.transpose(2, 0, 1)
        image = image[:, start:stop, start:stop].astype(np.float32)
        image -= mean_image
        x_batch = np.ndarray(
                (1, 3, in_size,in_size), dtype=np.float32)
        x_batch[0]=image

        if args.gpu >= 0:
          x_batch=cuda.to_gpu(x_batch)
        x = chainer.Variable(x_batch, volatile=True)
        score = predict(x)

        if args.gpu >= 0:
          score=cuda.to_cpu(score.data)

        top_k = 1
        prediction = zip(score.data[0].tolist(), categories)
        prediction.sort(cmp=lambda x, y: cmp(x[0], y[0]), reverse=True)

        for rank, (score, name) in enumerate(prediction[:top_k], start=1):
            print(name)
            if name != tmp_name:
                jtalk(name)

            tmp_name = name
            
        count=0

cam.release()
cv2.destroyAllWindows()
