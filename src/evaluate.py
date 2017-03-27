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

from progressbar import *


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
    log(flog, 'evaluating, go to have a rest:) ...')

    gt_dir = config.test_gt_dir
    pd_dir = config.test_pd_dir

    if config.test_iter:
        iter = config.test_iter
    else:
        with open(os.path.join(config.deploy_dir, 'test.txt'), 'r') as f:
            iter = 0
            for line in f:
                iter = iter + 1

    num_classes = config.classes
    print('iters', iter)
    if config.ignore_background:
        unknown_classes = config.classes + 1
    else:
        # assume no more than 1000 classes
        unknown_classes = 1000

    total_points = 0
    cf = np.zeros((iter, num_classes, num_classes))
    print('shape of confuse matrix: ', cf.shape)

    global_acc = 0
    widgets = [Bar('>'), ' ', Percentage(), ' ', Timer(), ' ', ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=iter).start()

    for i in range(0, iter):
        #print('iter %d' % i)
        pbar.update(i)

        pred = io.imread(os.path.join(pd_dir, '%d.png' % i))
        pred = pred + 1
        annot = io.imread(os.path.join(gt_dir, '%d.png' % i))
        annot = annot + 1

        
        pixels_ingore = (annot == unknown_classes)
        pred[pixels_ingore] = 0
        annot[pixels_ingore] = 0

        total_points = total_points + np.sum(annot > 0)

        # global and class accuracy computation
        for j in range(1, num_classes + 1):
            c1 = (annot == j)
            for k in range(1, num_classes + 1):
                c1p = (pred == k)
                index = np.multiply(c1, c1p)
                cf[i][j - 1][k - 1] = cf[i][j - 1][k - 1] + np.sum(index > 0)
        
            c1p = (pred == j)
            index = index = np.multiply(c1, c1p)
            global_acc = global_acc + np.sum(index > 0)
    
    cf = sum(cf)

    # compute confusion matrix
    conf = np.zeros((num_classes, num_classes))
    for i in range(1, num_classes + 1):
        if i != unknown_classes and sum(cf[i - 1,:]) > 0:
            conf[i - 1, :] = cf[i - 1, :] / sum(cf[i - 1, :])

    # compute intersection over union for each class and ites mean  
    iou = np.zeros(num_classes)
    for i in range(1, num_classes + 1):
        if i != unknown_classes and np.sum(conf[i - 1]) > 0:
            iou[i - 1] = cf[i - 1][i - 1] / (np.sum(cf[i - 1, :]) + np.sum(cf[:, i - 1]) - cf[i - 1][i - 1])

    global_acc = float(global_acc) / total_points
    class_avg_acc = np.sum(np.diag(conf)) / num_classes
    mean_iou = sum(iou) / num_classes
    print('Global acc = %f, Class average acc = %f, Mean Int over Union = %f' % (global_acc, class_avg_acc, mean_iou))

    with open(config.test_statistic_file, 'w') as f:
        f.write('Global acc = %f, Class average acc = %f, Mean Int over Union = %f\n' % (global_acc, class_avg_acc, mean_iou))