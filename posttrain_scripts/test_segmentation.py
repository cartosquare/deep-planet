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
import config

# Import arguments
model = config.test_model
weights = config.test_weights
iter = config.test_iter
gt_dir = config.test_gt_dir
pd_dir = config.test_pd_dir
label_colours = config.label_colours

if not os.path.exists(gt_dir):
    os.mkdir(gt_dir)
    
if not os.path.exists(pd_dir):
    os.mkdir(pd_dir)

caffe.set_mode_gpu()

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

