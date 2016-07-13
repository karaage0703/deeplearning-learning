#!/usr/bin/env python
from __future__ import print_function
import sys
from chainer.functions import caffe
import cPickle as pickle

import_model = "bvlc_googlenet.caffemodel"

print('Loading Caffe model file %s...' % import_model, file=sys.stderr)

model = caffe.CaffeFunction(import_model)
print('Loaded', file=sys.stderr)


pickle.dump(model, open('chainer.pkl', 'wb'), -1)
print('Convert is done')
