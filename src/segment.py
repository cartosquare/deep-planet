from skimage import io
caffe_root = './caffe-segnet-cudnn5/'
import sys
sys.path.insert(0, caffe_root + 'python')
import caffe
from config import DeepPlanetConfig
import json
import os
import numpy as np


def parseOptions(config_file):
    with open(config_file) as json_data:
        d = json.load(json_data)
        return d

if __name__ == '__main__':
    # Parse command line options
    if len(sys.argv) < 3:
        print('need config file!!! and a image path!!!\n')
        exit()
    
    config_cmd = parseOptions(sys.argv[1])
    config = DeepPlanetConfig()
    if not config.Initialize(config_cmd):
        print('initialize fail! exist...')
        exit()
    
    model_def = str(config.inference_net)
    model_weights = str(config.test_weights)

    image_file = sys.argv[2]
    output_image = './out.png'

    if config.use_gpu:
        caffe.set_mode_gpu()
        caffe.set_device(config.gpu)
    else:
        caffe.set_mode_cpu()

    net = caffe.Net(model_def, model_weights, caffe.TEST)

    image = caffe.io.load_image(image_file)

    # create transformer for the input called 'data'
    transformer = caffe.io.Transformer({'data': net.blobs['data'].data.shape})

    transformer.set_transpose('data', (2,0,1))  # move image channels to outermost dimension
    #transformer.set_mean('data', mu)            # subtract the dataset-mean value in each channel
    transformer.set_raw_scale('data', 255)      # rescale from [0, 1] to [0, 255]
    transformer.set_channel_swap('data', (2,1,0))  # swap channels from RGB to BGR

    transformed_image = transformer.preprocess('data', image)

    # copy the image data into the memory allocated for the net
    net.blobs['data'].data[...] = transformed_image

    ### perform segmentation
    net.forward()

    predicted = net.blobs['prob'].data
    output = np.squeeze(predicted[0,:,:,:])
    ind = np.argmax(output, axis=0)

    r = ind.copy()
    g = ind.copy()
    b = ind.copy()
    a = ind.copy()

    label_colours = config.class_colors
    for l in range(0, len(label_colours)):
        r[ind==l] = label_colours[l][0]
        g[ind==l] = label_colours[l][1]
        b[ind==l] = label_colours[l][2]
        a[ind==l] = label_colours[l][3]

    rgba = np.zeros((ind.shape[0], ind.shape[1], 4))
    rgba[:,:,0] = r / 255.0
    rgba[:,:,1] = g / 255.0
    rgba[:,:,2] = b / 255.0
    rgba[:,:,3] = a / 255.0

    io.imsave(output_image, rgba)