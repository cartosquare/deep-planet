# -*- coding: utf-8 -*-
import os
import sys
import json
import datetime

# for pyinstaller dependency ...
from skimage import io
import subprocess

from config import DeepPlanetConfig
from config import caffe_root
import sys
sys.path.insert(0, caffe_root + 'python')
import caffe


def log(file_handle, message):
    current_time = datetime.datetime.now()
    flog.write('[%s] %s\n' % (current_time.strftime('%Y-%m-%d %H:%M:%S'), message))
    flog.flush()

def parseOptions(config_file):
    with open(config_file) as json_data:
        d = json.load(json_data)
        return d

def gen_solver_file():
    log(flog, 'generating solver file %s' % config.solver)
    with open(config.solver, 'w') as f:
        f.write('net: "%s"\n' % (config.train_net))
        f.write('test_iter: 1\n')
        f.write('test_interval: 10000000\n')
        f.write('base_lr: 0.001\n')
        f.write('lr_policy: "step"\n')
        f.write('gamma: 1.0\n')
        f.write('stepsize: 10000000\n')
        f.write('display: 20\n')
        f.write('momentum: 0.9\n')
        f.write('max_iter: %d\n' % (config.max_iter))
        f.write('weight_decay: 0.0005\n')
        f.write('snapshot: %d\n' % (config.snapshot))
        f.write('snapshot_prefix: "%s"\n' % (config.snapshot_prefix))
        if config.use_gpu:
            f.write('solver_mode: GPU\n')
        else:
            f.write('solver_mode: CPU\n')

def gen_train_file():
    log(flog, 'generating train net file %s' % config.train_net)
    ftrain = open(config.train_net, 'w')

    with open(config.train_net_template, 'r') as f:
        for line in f:
            ftrain.write(line)

            items = line.strip().split(':')
            if len(items) == 2 and items[0] == 'name' and items[1] == ' "data"':
                if config.image_type == 'tif':
                    ftrain.write('  type: "DenseTiffData"\n')
                    ftrain.write('  top: "data"\n')
                    ftrain.write('  top: "label"\n')
                    ftrain.write('  dense_tiff_data_param {\n')
                    ftrain.write('    source: "%s/train.txt"\n' % config.deploy_dir)
                    ftrain.write('    batch_size: %d\n' % (config.batch_size))
                    ftrain.write('    shuffle: true\n')
                    ftrain.write('  }\n')
                else:
                    ftrain.write('  type: "DenseImageData"\n')
                    ftrain.write('  top: "data"\n')
                    ftrain.write('  top: "label"\n')
                    ftrain.write('  dense_image_data_param {\n')
                    ftrain.write('    source: "%s/train.txt"\n' % config.deploy_dir)
                    ftrain.write('    batch_size: %d\n' % (config.batch_size))
                    ftrain.write('    shuffle: true\n')
                    ftrain.write('  }\n')
                
                if config.substract_mean:
                    with open(config.mean_file, 'r') as f:
                        ftrain.write('  transform_param {\n')
                        for line in f:
                            mean_values = line.strip().split()
                            for mean_val in mean_values:
                                ftrain.write('    mean_value: %f\n' % float(mean_val))
                        ftrain.write('  }\n')

            if len(items) == 2 and items[0] == 'name' and items[1] == ' "conv1_1_D"':
                ftrain.write('  type: "Convolution"\n')
                ftrain.write('  param {\n')
                ftrain.write('    lr_mult: 1\n')
                ftrain.write('    decay_mult: 1\n')
                ftrain.write('  }\n')
                ftrain.write('  param {\n')
                ftrain.write('    lr_mult: 2\n')
                ftrain.write('    decay_mult: 0\n')
                ftrain.write('  }\n')
                ftrain.write('  convolution_param {\n')
                ftrain.write('    weight_filler {\n')
                ftrain.write('      type: "msra"\n')
                ftrain.write('    }\n')
                ftrain.write('    bias_filler {\n')
                ftrain.write('      type: "constant"\n')
                ftrain.write('    }\n')
                ftrain.write('    num_output: %d\n' % (config.classes))
                ftrain.write('    pad: 1\n')
                ftrain.write('    kernel_size: 3\n')
                ftrain.write('  }\n')
            if len(items) == 2 and items[0] == 'weight_by_label_freqs':
                if config.ignore_background:
                    ftrain.write('    ignore_label: %d\n' % (config.classes))
                with open(config.weight_file, 'r') as wf:
                    for wl in wf:
                        ftrain.write('    %s' % (wl))


def gen_infence_file(mode):
    if mode == 'test':
        log(flog, 'generating test net file %s' % config.test_net)
        ftrain = open(config.test_net, 'w')
    else:
        log(flog, 'generating predict net file %s' % config.predict_net)
        ftrain = open(config.predict_net, 'w')

    with open(config.inference_net_template, 'r') as f:
        for line in f:
            ftrain.write(line)

            items = line.strip().split(':')
            if len(items) == 2 and items[0] == 'name' and items[1] == ' "data"':
                if config.image_type == 'tif':
                    ftrain.write('  type: "DenseTiffData"\n')
                    ftrain.write('  top: "data"\n')
                    ftrain.write('  top: "label"\n')
                    ftrain.write('  dense_tiff_data_param {\n')
                    ftrain.write('    source: "%s/%s.txt"\n' % (config.deploy_dir, mode))
                    ftrain.write('    batch_size: 1\n')
                    ftrain.write('  }\n')
                else:
                    ftrain.write('  type: "DenseImageData"\n')
                    ftrain.write('  top: "data"\n')
                    ftrain.write('  top: "label"\n')
                    ftrain.write('  dense_image_data_param {\n')
                    ftrain.write('    source: "%s/%s.txt"\n' % (config.deploy_dir, mode))
                    ftrain.write('    batch_size: 1\n')
                    ftrain.write('  }\n')

                if config.substract_mean:
                    with open(config.mean_file, 'r') as f:
                        ftrain.write('  transform_param {\n')
                        for line in f:
                            mean_values = line.strip().split()
                            for mean_val in mean_values:
                                ftrain.write('    mean_value: %f\n' % float(mean_val))
                        ftrain.write('  }\n')
                    
            if len(items) == 2 and items[0] == 'name' and items[1] == ' "conv1_1_D"':
                ftrain.write('  type: "Convolution"\n')
                ftrain.write('  param {\n')
                ftrain.write('    lr_mult: 1\n')
                ftrain.write('    decay_mult: 1\n')
                ftrain.write('  }\n')
                ftrain.write('  param {\n')
                ftrain.write('    lr_mult: 2\n')
                ftrain.write('    decay_mult: 0\n')
                ftrain.write('  }\n')
                ftrain.write('  convolution_param {\n')
                ftrain.write('    weight_filler {\n')
                ftrain.write('      type: "msra"\n')
                ftrain.write('    }\n')
                ftrain.write('    bias_filler {\n')
                ftrain.write('      type: "constant"\n')
                ftrain.write('    }\n')
                ftrain.write('    num_output: %d\n' % (config.classes))
                ftrain.write('    pad: 1\n')
                ftrain.write('    kernel_size: 3\n')
                ftrain.write('  }\n')

def execute_system_command(command):
    try:
        retcode = subprocess.call(command, shell=True)
        if retcode < 0:
            print("Child was terminated by signal", -retcode)
            return False
        else:
            print("Child returned", retcode)
            return True
    except OSError as e:
        print("Execution failed:", e)
        return False

def train():
    if config.use_gpu:
        log(flog, 'starting training  using gpu %s' % config.gpu)
        command = '%s train -gpu %s -solver %s' % (caffe_bin, config.gpu, config.solver)
    else:
        log(flog, 'starting training using cpu')
        command = '%s train -solver %s' % (caffe_bin, config.solver)

    if config.weights is not None:
        command = '%s -weights %s' % (command, config.weights)

    if config.restore_snapshot is not None:
        command = '%s -snapshot %s' % (command, config.restore_snapshot)

    print command
    return execute_system_command(command)


if __name__=='__main__': 
    # Parse command line options
    if len(sys.argv) < 2:
        print('need config file!!!\n')
        exit()
    
    config_cmd = parseOptions(sys.argv[1])
    config = DeepPlanetConfig()
    if not config.Initialize(config_cmd):
        print('initialize fail! exist...')
        exit()

    # for pyinstaller
    if getattr(sys, 'frozen', False):
        # we are running in a bundle
        caffe_bin = os.path.join(sys._MEIPASS, 'caffe')
    else:
        # we are running in a normal Python environment
        caffe_bin = '%s/build/tools/caffe' % caffe_root

    # Step 0, Open log file
    flog = open(config.log_file, 'w')
    log(flog, 'training, this may take a long time ...')

    if not os.path.exists(config.model_dir):
        log(flog, 'create model directory %s' % config.model_dir)
        os.mkdir(config.model_dir)

    if not os.path.exists(config.snapshot_dir):
        log(flog, 'create snapshot directory %s' % config.snapshot_dir)
        os.mkdir(config.snapshot_dir)
    
    if not os.path.exists(config.test_dir):
        log(flog, 'create test directory %s' % config.test_dir)
        os.mkdir(config.test_dir)

    if not os.path.exists(config.train_net):
        gen_solver_file()
        gen_train_file()
        gen_infence_file('test')
        gen_infence_file('predict')

    train()
