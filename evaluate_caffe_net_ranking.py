#!/usr/bin/env python
"""Example code of evaluating a Caffe reference model for ILSVRC2012 task.

Prerequisite: To run this example, crop the center of ILSVRC2012 validation
images and scale them to 256x256, and make a list of space-separated CSV each
column of which contains a full path to an image at the fist column and a zero-
origin label at the second column (this format is same as that used by Caffe's
ImageDataLayer).

"""
from __future__ import print_function
import argparse
import os
import sys

import numpy as np
from PIL import Image

import chainer
from chainer import cuda
import chainer.functions as F
from chainer.links import caffe


parser = argparse.ArgumentParser(
    description='Evaluate a Caffe reference model on ILSVRC2012 dataset')
parser.add_argument('imagefile', help='Path to validation image-label list file')
parser.add_argument('model_type',
                    choices=('alexnet', 'caffenet', 'googlenet', 'resnet'),
                    help='Model type (alexnet, caffenet, googlenet, resnet)')
parser.add_argument('model', help='Path to the pretrained Caffe model')
parser.add_argument('--basepath', '-b', default='/',
                    help='Base path for images in the dataset')
parser.add_argument('--mean', '-m', default='ilsvrc_2012_mean.npy',
                    help='Path to the mean file')
# parser.add_argument('--batchsize', '-B', type=int, default=100,
                    # help='Minibatch size')
parser.add_argument('--gpu', '-g', type=int, default=-1,
                    help='Zero-origin GPU ID (nevative value indicates CPU)')
args = parser.parse_args()
if args.gpu >= 0:
    cuda.check_cuda_available()
xp = cuda.cupy if args.gpu >= 0 else np

print('Load file='+ args.imagefile)

categories = np.loadtxt('synset_words.txt', str, delimiter="\t")
top_k=5

print('Loading Caffe model file %s...' % args.model, file=sys.stderr)
func = caffe.CaffeFunction(args.model)
print('Loaded', file=sys.stderr)
if args.gpu >= 0:
    cuda.get_device(args.gpu).use()
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

    def forward(x, t):
        y, = func(inputs={'data': x}, outputs=['loss3/classifier'],
                  disable=['loss1/ave_pool', 'loss2/ave_pool'],
                  train=False)
        return F.softmax_cross_entropy(y, t), F.accuracy(y, t)
elif args.model_type == 'resnet':
    in_size = 224
    mean_image = np.load(args.mean)

    def forward(x, t):
        y, = func(inputs={'data': x}, outputs=['prob'], train=False)
        return F.softmax_cross_entropy(y, t), F.accuracy(y, t)


cropwidth = 256 - in_size
start = cropwidth // 2
stop = start + in_size
mean_image = mean_image[:, start:stop, start:stop].copy()

x_batch = np.ndarray((1, 3, in_size, in_size), dtype=np.float32)
y_batch = np.ndarray((1,), dtype=np.int32)

image = Image.open(args.imagefile).resize((256,256,))
image = np.asarray(image).transpose(2, 0, 1)[::-1]
image = image[:, start:stop, start:stop].astype(np.float32)
image -= mean_image

x_batch[0] = image
x_data = xp.asarray(x_batch)

x = chainer.Variable(x_data, volatile=True)

score = predict(x)
prediction = zip(score.data[0].tolist(), categories)
prediction.sort(cmp=lambda x,y: cmp(x[0],y[0]),reverse=True)
for rank,(score,name) in enumerate(prediction[:top_k],start=1):
    print('%d | %s | %4.1f%%' % (rank,name,score *100))

