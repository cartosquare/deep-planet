# -*- coding: utf-8 -*-
import os
import shutil
import numpy
import random
import math
import sys
import config

train_dir = config.valid_tif_tiles_dir
label_dir = config.labels_dir

train_file = config.train_txt
test_file = config.test_txt

ftrain = open(train_file, 'w')
ftest = open(test_file, 'w')

tiles = os.listdir(train_dir)
random.shuffle(tiles)

total_files = len(tiles)
cut_line = int(total_files * 0.8)

print('#total tiles: %d, #training tiles: %d, #testing tiles: %d' % (total_files, cut_line, total_files - cut_line))

pow15 = math.pow(2, 15)

for i in range(0, total_files):
    tile_name = tiles[i]

    items = tile_name.split('.')
    if len(items) != 2 or items[1] != 'tif':
        print('not tif file: ' + tile_name)
        continue

    items = items[0].split('_')
    if (len(items) != 3):
        print('illegal filename ' + items)
        continue

    z = items[0]
    x = items[1] 
    y = items[2]

    img_tile = '%s/%s_%s_%s.tif' % (train_dir, z, x, y)
    label_tile = '%s/%s_%s_%s.png' % (label_dir, z, x, y)

    if not os.path.exists(label_tile):
        print('not exists ' + label_tile)
        continue

    if i < cut_line:
        # write train.txt
        ftrain.write('%s %s\n' % (img_tile, label_tile))
    else:
        # write test.txt
        ftest.write('%s %s\n' % (img_tile, label_tile))

ftrain.close()
ftest.close()