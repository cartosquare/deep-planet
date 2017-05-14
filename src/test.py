# -*- coding: utf-8 -*-

import numpy as np
#import matplotlib.pyplot as plt
import os
import os.path
import json
import scipy
import math
from skimage import io
import datetime

from config import DeepPlanetConfig
import sys
sys.path.insert(0, DeepPlanetConfig.caffe_root + 'python')
import caffe

def log(file_handle, message):
    current_time = datetime.datetime.now()
    flog.write('[%s] %s\n' % (current_time.strftime('%Y-%m-%d %H:%M:%S'), message))
    flog.flush()

def parseOptions(config_file):
    with open(config_file) as json_data:
        d = json.load(json_data)
        return d

if __name__ == '__main__':
    # Parse command line options
    if len(sys.argv) < 2:
        print('need config file!!!\n')
        exit()

    config_cmd = parseOptions(sys.argv[1])
    config = DeepPlanetConfig()
    if not config.Initialize(config_cmd):
        print('initialize fail! exist...')
        exit()

    # Step 0, Open log file
    flog = open(config.log_file, 'w')
    log(flog, 'testing, this may take a long time ...')

    # Import arguments
    model = str(config.test_net)
    weights = str(config.test_weights)
    if config.test_iter:
        iter = config.test_iter
    else:
        with open(os.path.join(config.deploy_dir, 'test.txt'), 'r') as f:
            iter = 0
            for line in f:
                iter = iter + 1

    gt_dir = config.test_gt_dir
    pd_dir = config.test_pd_dir

    print('Model: %s' % model)
    print('Weights: %s' % weights)
    print('iters: %d' % iter)

    if not os.path.exists(pd_dir):
        os.mkdir(pd_dir)
    if not os.path.exists(gt_dir):
        os.mkdir(gt_dir)

    if config.use_gpu:
        caffe.set_mode_gpu()
        caffe.set_device(config.gpu)
    else:
        caffe.set_mode_cpu()

    net = caffe.Net(model, weights, caffe.TEST)
    for i in range(0, iter):
        print('iter %d' % i)
        net.forward()

        label = net.blobs['label'].data
        label = np.squeeze(label[0, :, :, :])
        label = label.astype(int)

        predicted = net.blobs['prob'].data
        output = np.squeeze(predicted[0, :, :, :])
        ind = np.argmax(output, axis=0)
        ind = ind.astype(int)

        io.imsave('%s/%d.png' % (pd_dir, i), ind)
        io.imsave('%s/%d.png' % (gt_dir, i), label)

    log(flog, 'success.')

    print 'Success!'
