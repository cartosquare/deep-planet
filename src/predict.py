# -*- coding: utf-8 -*-

import numpy as np
#import matplotlib.pyplot as plt
import os
import os.path
import json
import scipy
import math
import shutil
from PIL import Image
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

def predict():
    model = str(os.path.join(config.deploy_dir, config.predict_net))
    weights = str(os.path.join(config.deploy_dir, config.test_weights))
    if config.test_iter:
        iter = config.test_iter
    else:
        with open(os.path.join(config.deploy_dir, 'predict.txt'), 'r') as f:
            iter = 0
            for line in f:
                iter = iter + 1

    pd_dir = config.predict_dir
    label_colours = config.label_colours

    log(flog, 'predicting %d images using model %s and weights %s to %s' % (iter, model, weights, pd_dir))
    print('Model: %s' % model)
    print('Weights: %s' % weights)
    
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
	    g = ind.copy()
	    b = ind.copy()
	    a = ind.copy()

	    for l in range(0, config.classes):
		    r[ind==l] = label_colours[l]['color'][0]
		    g[ind==l] = label_colours[l]['color'][1]
		    b[ind==l] = label_colours[l]['color'][2]
		    a[ind==l] = label_colours[l]['color'][3]

	    rgba = np.zeros((ind.shape[0], ind.shape[1], 4))
	    rgba[:,:,0] = r / 255.0
	    rgba[:,:,1] = g / 255.0
	    rgba[:,:,2] = b / 255.0
	    rgba[:,:,3] = a / 255.0

	    io.imsave('%s/%d.png' % (pd_dir, i), rgba)

def convert_predict():
    log(flog, 'converting filename from %s to %s' % (config.predict_dir, config.predict_tiles_dir))
    if not os.path.exists(config.predict_tiles_dir):
        os.mkdir(config.predict_tiles_dir)

    with open(os.path.join(config.deploy_dir, 'predict.txt'), 'r') as f:
        count = 0
        for line in f:
            newline = line.strip().split()
            filename, file_extension = os.path.splitext(newline[0])
            items = filename.split('/')

            old_file = os.path.join(config.predict_dir, '%d.png' % count)
            new_file = os.path.join(config.predict_tiles_dir, '%s.png' % items[len(items) - 1])
            print '%s -> %s' % (old_file, new_file)

            shutil.copy(old_file, new_file)

            count = count + 1


def get_file(filename):
    file_path = os.path.join(config.predict_fusion_tiles_dir, filename)
    if not os.path.exists(file_path):
        return os.path.join(config.predict_tiles_dir, filename)
    else:
        return file_path

def color_equal(a, b):
    return (a[0] == b[0] and a[1] == b[1] and a[2] == b[2])

def fusion():
    log(flog, 'converting filename from %s to %s' % (config.predict_tiles_dir, config.predict_fusion_tiles_dir))

    if not os.path.exists(config.predict_fusion_tiles_dir):
        os.mkdir(config.predict_fusion_tiles_dir)

    tiles = os.listdir(config.predict_tiles_dir)
    inf = 1000000000
    minx = inf
    maxx = -inf
    miny = inf
    maxy = -inf
    for tile in tiles:
        z_x_y_str = tile.strip().split('.')[0]
        z_x_y = z_x_y_str.split('_')
        z = int(z_x_y[0])
        x = int(z_x_y[1])
        y = int(z_x_y[2])

        if minx > x:
            minx = x
        if maxx < x:
            maxx = x
        if miny > y:
            miny = y
        if maxy < y:
            maxy = y

    print(minx, miny, maxx, maxy)

    debug_break = False
    total_tiles = (maxy - miny + 1) * (maxx - minx + 1)
    cnt = 0
    for y in range(maxy, miny - 1, -1):
        for x in range(maxx, minx - 1, -1):
            cnt = cnt + 1
            if cnt % 300 == 0:
                print('%d of %d' % (cnt, total_tiles))

            current_tile = '%d_%d_%d.png' % (z, x, y)
            left_tile = '%d_%d_%d.png' % (z, x - 1, y)
            top_tile = '%d_%d_%d.png' % (z, x, y - 1)

            current_tile_file = get_file(current_tile)
            if os.path.exists(current_tile_file):
                debug_break = True
                #print('process %s' % (current_tile_file))
                current_img = io.imread(current_tile_file)

                left_tile_file = get_file(left_tile)
                if os.path.exists(left_tile_file):
                    #print('update %s using %s' % (left_tile, current_tile))

                    left_tile_img = io.imread(left_tile_file)
                    for k in range(0, image_size):
                        pixel_value = current_img[k][overlap]
                        new_pixel_value = current_img[k][overlap - 1]
                        continue_pixels = 0
                        while color_equal(new_pixel_value, pixel_value) and (overlap - 1 - continue_pixels) >= 0:
                            left_tile_img[k][image_size - continue_pixels - 1] = pixel_value

                            continue_pixels = continue_pixels + 1
                            new_pixel_value = current_img[k][overlap - 1 - continue_pixels]
    
                    # save
                    update_left_tile_file = os.path.join(config.predict_fusion_tiles_dir, left_tile)
                    #print('saving updated left tile file %s' % (update_left_tile_file))
                    #if os.path.exists(update_left_tile_file):
                    #    print('warning: already exist')
                    io.imsave(update_left_tile_file, left_tile_img)
                else:
                    debug_break = False
            
                top_tile_file = get_file(top_tile)
                if os.path.exists(top_tile_file):
                    #print('update %s using %s' % (top_tile, current_tile))
                    top_tile_img = io.imread(top_tile_file)
                    for k in range(0, image_size):
                        pixel_value = current_img[overlap][k]
                        new_pixel_value = current_img[overlap - 1][k]
                        continue_pixels = 0
                        while color_equal(new_pixel_value, pixel_value) and (overlap - 1 - continue_pixels) >= 0:
                            top_tile_img[image_size - continue_pixels - 1][k] = pixel_value

                            continue_pixels = continue_pixels + 1
                            new_pixel_value = current_img[overlap - 1 - continue_pixels][k]
                        
                    # save 
                    update_top_tile_file = os.path.join(config.predict_fusion_tiles_dir, top_tile)
                    #print('saving updated top tile file %s' % (update_top_tile_file))
                    #if os.path.exists(update_top_tile_file):
                    #    print('warning: already exist')
                
                    io.imsave(update_top_tile_file, top_tile_img)
                else:
                    debug_break = False
            
            #if debug_break:
                #break
        #if debug_break:
            #break

def is_png(file):
    filename, file_extension = os.path.splitext(file)
    return (file_extension == '.png')

def crop():
    log(flog, 'croping tiles from %s to %s' % (config.predict_fusion_tiles_dir, config.predict_crop_image_dir))
    if not os.path.exists(config.predict_crop_image_dir):
        os.mkdir(config.predict_crop_image_dir)
    
    tiles = os.listdir(config.predict_fusion_tiles_dir)
    cnt = 0
    total_tiles = len(tiles)
    for tile in tiles:
        if not is_png(tile):
            continue
        
        tile_file = os.path.join(config.predict_fusion_tiles_dir, tile)
        tile_image = Image.open(tile_file)
        new_im = Image.new('RGB', (image_size - overlap, image_size - overlap))
        new_im.paste(tile_image, (-overlap, -overlap))

        new_im_file = os.path.join(config.predict_crop_image_dir, tile)
        new_im.save(new_im_file, "PNG")

        cnt = cnt + 1
        if cnt % 300 == 0:
            print('%d of %d' % (cnt, total_tiles))


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
    log(flog, 'predicting, this may take a long time ...')

    image_size = config.image_dim + config.overlap
    overlap = config.overlap

    # Step 1, predict images
    predict()

    # Step 2, convert image names
    convert_predict()

    # Step 3, fusion to avoid gaps
    fusion()

    # Step 4, crop margins
    crop()

    # happy ending
    log(flog, 'success.')
    print 'Success!'