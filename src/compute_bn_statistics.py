# -*- coding: utf-8 -*-

import os
import numpy as np
import datetime
import json
from skimage.io import ImageCollection
from config import DeepPlanetConfig
from config import caffe_root
import sys
sys.path.insert(0, caffe_root + 'python')

import caffe
from caffe.proto import caffe_pb2
from google.protobuf import text_format


def log(file_handle, message):
    current_time = datetime.datetime.now()
    flog.write('[%s] %s\n' % (current_time.strftime('%Y-%m-%d %H:%M:%S'), message))
    flog.flush()

def parseOptions(config_file):
    with open(config_file) as json_data:
        d = json.load(json_data)
        return d

def extract_dataset(net_message):
    if config.image_type == 'png':
        source = net_message.layer[0].dense_image_data_param.source
    else:
        source = net_message.layer[0].dense_tiff_data_param.source
    with open(source) as f:
        data = f.read().split()

    return len(data[::2])


def make_testable(train_model_path):
    # load the train net prototxt as a protobuf message
    with open(train_model_path) as f:
        train_str = f.read()
    train_net = caffe_pb2.NetParameter()
    text_format.Merge(train_str, train_net)

    # add the mean, var top blobs to all BN layers
    for layer in train_net.layer:
        if layer.type == "BN" and len(layer.top) == 1:
            layer.top.append(layer.top[0] + "-mean")
            layer.top.append(layer.top[0] + "-var")

    # remove the test data layer if present
    if train_net.layer[1].name == "data" and train_net.layer[1].include:
        train_net.layer.remove(train_net.layer[1])
        if train_net.layer[0].include:
            # remove the 'include {phase: TRAIN}' layer param
            train_net.layer[0].include.remove(train_net.layer[0].include[0])
    return train_net


def make_test_files(testable_net_path, train_weights_path, num_iterations,
                    in_h, in_w):
    # load the train net prototxt as a protobuf message
    with open(testable_net_path) as f:
        testable_str = f.read()
    testable_msg = caffe_pb2.NetParameter()
    text_format.Merge(testable_str, testable_msg)
    
    bn_layers = [l.name for l in testable_msg.layer if l.type == "BN"]
    bn_blobs = [l.top[0] for l in testable_msg.layer if l.type == "BN"]
    bn_means = [l.top[1] for l in testable_msg.layer if l.type == "BN"]
    bn_vars = [l.top[2] for l in testable_msg.layer if l.type == "BN"]

    net = caffe.Net(testable_net_path, train_weights_path, caffe.TEST)
    
    # init our blob stores with the first forward pass
    res = net.forward()
    bn_avg_mean = {bn_mean: np.squeeze(res[bn_mean]).copy() for bn_mean in bn_means}
    bn_avg_var = {bn_var: np.squeeze(res[bn_var]).copy() for bn_var in bn_vars}

    # iterate over the rest of the training set
    for i in xrange(1, num_iterations):
        res = net.forward()
        for bn_mean in bn_means:
            bn_avg_mean[bn_mean] += np.squeeze(res[bn_mean])
        for bn_var in bn_vars:
            bn_avg_var[bn_var] += np.squeeze(res[bn_var])
        print 'progress: {}/{}'.format(i, num_iterations)

    # compute average means and vars
    for bn_mean in bn_means:
        bn_avg_mean[bn_mean] /= num_iterations
    for bn_var in bn_vars:
        bn_avg_var[bn_var] /= num_iterations

    for bn_blob, bn_var in zip(bn_blobs, bn_vars):
        m = np.prod(net.blobs[bn_blob].data.shape) / np.prod(bn_avg_var[bn_var].shape)
        bn_avg_var[bn_var] *= (m / (m - 1))

    # calculate the new scale and shift blobs for all the BN layers
    scale_data = {bn_layer: np.squeeze(net.params[bn_layer][0].data)
                  for bn_layer in bn_layers}
    shift_data = {bn_layer: np.squeeze(net.params[bn_layer][1].data)
                  for bn_layer in bn_layers}

    var_eps = 1e-9
    new_scale_data = {}
    new_shift_data = {}
    for bn_layer, bn_mean, bn_var in zip(bn_layers, bn_means, bn_vars):
        gamma = scale_data[bn_layer]
        beta = shift_data[bn_layer]
        Ex = bn_avg_mean[bn_mean]
        Varx = bn_avg_var[bn_var]
        new_gamma = gamma / np.sqrt(Varx + var_eps)
        new_beta = beta - (gamma * Ex / np.sqrt(Varx + var_eps))

        new_scale_data[bn_layer] = new_gamma
        new_shift_data[bn_layer] = new_beta
    print "New data:"
    print new_scale_data.keys()
    print new_shift_data.keys()

    # assign computed new scale and shift values to net.params
    for bn_layer in bn_layers:
        net.params[bn_layer][0].data[...] = new_scale_data[bn_layer].reshape(
            net.params[bn_layer][0].data.shape
        )
        net.params[bn_layer][1].data[...] = new_shift_data[bn_layer].reshape(
            net.params[bn_layer][1].data.shape
        )
        
    # build a test net prototxt
    test_msg = testable_msg
    # replace data layers with 'input' net param
    data_layers = [l for l in test_msg.layer if l.type.endswith("Data")]
    for data_layer in data_layers:
        test_msg.layer.remove(data_layer)
    test_msg.input.append("data")
    test_msg.input_dim.append(1)
    test_msg.input_dim.append(3)
    test_msg.input_dim.append(in_h)
    test_msg.input_dim.append(in_w)
    # Set BN layers to INFERENCE so they use the new stat blobs
    # and remove mean, var top blobs.
    for l in test_msg.layer:
        if l.type == "BN":
            if len(l.top) > 1:
                dead_tops = l.top[1:]
                for dl in dead_tops:
                    l.top.remove(dl)
            l.bn_param.bn_mode = caffe_pb2.BNParameter.INFERENCE
    # replace output loss, accuracy layers with a softmax
    dead_outputs = [l for l in test_msg.layer if l.type in ["SoftmaxWithLoss", "Accuracy"]]
    out_bottom = dead_outputs[0].bottom[0]
    for dead in dead_outputs:
        test_msg.layer.remove(dead)
    test_msg.layer.add(
        name="prob", type="Softmax", bottom=[out_bottom], top=['prob']
    )
    return net, test_msg


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

    if config.use_gpu:
        caffe.set_mode_gpu()
        caffe.set_device(config.gpu)
    else:
        caffe.set_mode_cpu()
    
    out_dir = str(config.test_dir)
    train_model = str(config.train_net)
    weights = str(config.trained_weights)
    print(out_dir, train_model, weights)

    log(flog, 'building testing net from %s %s to %s' % (train_model, weights, out_dir))

    # build and save testable net
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    print "Building BN calc net..."
    testable_msg = make_testable(train_model)
    BN_calc_path = os.path.join(
        out_dir, '__for_calculating_BN_stats_' + os.path.basename(train_model)
    )
    with open(BN_calc_path, 'w') as f:
        f.write(text_format.MessageToString(testable_msg))

    # use testable net to calculate BN layer stats
    print "Calculate BN stats..."
    train_size = extract_dataset(testable_msg)
    if config.image_type == 'png':
        minibatch_size = testable_msg.layer[0].dense_image_data_param.batch_size
    else:
        minibatch_size = testable_msg.layer[0].dense_tiff_data_param.batch_size
    num_iterations = train_size // minibatch_size + train_size % minibatch_size
    in_h, in_w =(config.image_dim, config.image_dim)

    test_net, test_msg = make_test_files(BN_calc_path, weights, num_iterations,in_h, in_w)
    
    # save deploy prototxt
    print "Saving deployment prototext file..."
    test_path = os.path.join(out_dir, "deploy.prototxt")
    with open(test_path, 'w') as f:
       f.write(text_format.MessageToString(test_msg))
    
    print "Saving test net weights..."
    test_net.save(os.path.join(out_dir, "test_weights.caffemodel"))
    print "done"

