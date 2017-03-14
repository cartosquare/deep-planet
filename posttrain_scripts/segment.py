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
#gt_dir = config.test_gt_dir
pd_dir = config.test_pd_dir
pd_prob_dir = config.test_pd_dir + '_prob'
#img_dir = config.test_img_dir
label_colours = config.label_colours

print('Model: %s' % model)
print('Weights: %s' % weights)

iter = 5041

if not os.path.exists(pd_prob_dir):
    os.mkdir(pd_prob_dir)
    
if not os.path.exists(pd_dir):
    os.mkdir(pd_dir)

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

	print 'prob shape', output.shape
	ind = np.argmax(output, axis=0)
	print 'index shape', ind.shape

	label_prob = np.max(output, axis=0)
	print 'label prob shape', label_prob.shape

	r = ind.copy()
	g = ind.copy()
	b = ind.copy()
	a = ind.copy()

	# r_gt = label.copy()
	# g_gt = label.copy()
	# b_gt = label.copy()
	# a_gt = label.copy()

	for l in range(0, config.classes):
		r[ind==l] = label_colours[l]['color'][0]
		g[ind==l] = label_colours[l]['color'][1]
		b[ind==l] = label_colours[l]['color'][2]
		a[ind==l] = label_colours[l]['color'][3]

		# r_gt[label==l] = label_colours[l]['color'][0]
        # 	g_gt[label==l] = label_colours[l]['color'][1]
        # 	b_gt[label==l] = label_colours[l]['color'][2]
        # 	a_gt[label==l] = label_colours[l]['color'][3]

	rgba = np.zeros((ind.shape[0], ind.shape[1], 4))
	rgba[:,:,0] = r / 255.0
	rgba[:,:,1] = g / 255.0
	rgba[:,:,2] = b / 255.0
	rgba[:,:,3] = a / 255.0


	# rgba_gt = np.zeros((ind.shape[0], ind.shape[1], 4))
	# rgba_gt[:,:,0] = r_gt
    # 	rgba_gt[:,:,1] = g_gt
    # 	rgba_gt[:,:,2] = b_gt
    # 	rgba_gt[:,:,3] = a_gt
	
	# rgba = rgba.astype(int)
	# rgba_gt = rgba_gt.astype(int)

	#image = image/255.0

	#image = np.transpose(image, (1,2,0))
	#output = np.transpose(output, (1,2,0))
	#image = image[:,:,(2,1,0)]

	scipy.misc.toimage(label_prob, cmin=0.0, cmax=1).save('%s/%d.png' % (pd_prob_dir, i))
	#scipy.misc.toimage(rgb_gt, cmin=0.0, cmax=1).save('%s/%d.png' % (gt_dir, i))
	#scipy.misc.toimage(rgb, cmin=0.0, cmax=1).save('%s/%d.png' % (pd_dir, i))
    #io.imsave('%s/%d.png' % (img_dir, i), image)
	#io.imsave('%s/%d.png' % (gt_dir, i), rgba_gt)

	io.imsave('%s/%d.png' % (pd_dir, i), rgba)

print 'Success!'