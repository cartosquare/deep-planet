# -*- coding: utf-8 -*-

import numpy as np
#import matplotlib.pyplot as plt
import os
import os.path
import json
import scipy
import math
from skimage import io
#import pylab
#from sklearn.preprocessing import normalize
caffe_root = './caffe-segnet/' 			# Change this to the absolute directoy to SegNet Caffe
import sys
sys.path.insert(0, caffe_root + 'python')

import caffe
import datetime
from config import DeepPlanetConfig


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
    log(flog, 'training, this may take a long time ...')

    # Import arguments
    model = str(os.path.join(config.deploy_dir, config.inference_net))
    weights = str(os.path.join(config.deploy_dir, config.test_weights))
    if config.test_iter:
        iter = config.test_iter
    else:
        with open(os.path.join(config.deploy_dir, 'test.txt'), 'r') as f:
            iter = 0
            for line in f:
                iter = iter + 1

    gt_dir = config.test_gt_dir
    pd_dir = config.test_pd_dir
    #pd_prob_dir = config.test_pd_dir + '_prob'
    #img_dir = config.test_img_dir
    label_colours = config.label_colours

    print('Model: %s' % model)
    print('Weights: %s' % weights)

    # if not os.path.exists(pd_prob_dir):
    #     os.mkdir(pd_prob_dir)
    
    if not os.path.exists(pd_dir):
        os.mkdir(pd_dir)

    if config.use_gpu:
        caffe.set_mode_gpu()
    else:
        caffe.set_mode_cpu()

	net = caffe.Net(model, weights, caffe.TEST)
	for i in range(0, iter):
		print 'iter %d' % i

		net.forward()

		image = net.blobs['data'].data
		label = net.blobs['label'].data
		predicted = net.blobs['prob'].data

		image = np.squeeze(image[0,:,:,:])
		output = np.squeeze(predicted[0,:,:,:])
		ind = np.argmax(output, axis=0)

		r = ind.copy()
		r_gt = label.copy()

		for l in range(0, config.classes):
			r[ind==l] = label_colours[l]['label']
			r_gt[label==l] = label_colours[l]['label']

		rgb = np.zeros((ind.shape[0], ind.shape[1]))
		rgb[:,:] = r
		rgb_gt = np.zeros((ind.shape[0], ind.shape[1]))
		rgb_gt[:,:] = r_gt
	
		rgb = rgb.astype(int)
		rgb_gt = rgb_gt.astype(int)

		#image = image/255.0

		#image = np.transpose(image, (1,2,0))
		#output = np.transpose(output, (1,2,0))
		#image = image[:,:,(2,1,0)]

		#scipy.misc.toimage(image, cmin=0.0, cmax=1).save('image.png')
		#scipy.misc.toimage(rgb_gt, cmin=0.0, cmax=1).save('%s/%d.png' % (gt_dir, i))
		#scipy.misc.toimage(rgb, cmin=0.0, cmax=1).save('%s/%d.png' % (pd_dir, i))
		io.imsave('%s/%d.png' % (gt_dir, i), rgb_gt)
		io.imsave('%s/%d.png' % (pd_dir, i), rgb)

	print 'Success!'

