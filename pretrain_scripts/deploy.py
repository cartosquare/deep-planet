import config
import os
import shutil

if not os.path.exists(config.deploy_dir):
    os.mkdir(config.deploy_dir) 

training_dir = '%s/training_set' % (config.deploy_dir)
if not os.path.exists(training_dir):
    os.mkdir(training_dir) 


train_txt = '%s/train.txt' % training_dir
test_txt = '%s/test.txt' % training_dir

ftrain = open(train_txt, 'w')
ftest = open(test_txt, 'w')

for ele in config.deploy:
    print 'process data set ', ele

    data_dir = '%s/training_set/%s' % (config.deploy_dir, ele)
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)

    # train dir
    train_dir = 'training_set/%s/valid_tif_tiles' % (ele)
    new_train_dir = '%s/valid_tif_tiles' % (data_dir)

    shutil.copytree(train_dir, new_train_dir)

    # label dir 
    label_dir = 'training_set/%s/labels' % (ele)
    new_label_dir = '%s/labels' % (data_dir)

    shutil.copytree(label_dir, new_label_dir)

    # train file
    train_file = 'training_set/%s/train.txt' % (ele)
    with open(train_file, 'r') as f:
        for line in f:
            ftrain.write(line)
    
    # test file
    test_file = 'training_set/%s/test.txt' % (ele)
    with open(test_file, 'r') as f:
        for line in f:
            ftest.write(line)

ftrain.close()
ftest.close()