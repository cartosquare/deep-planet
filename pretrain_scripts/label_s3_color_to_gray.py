# -*- coding: utf-8 -*-
import os
from skimage import color
from skimage import io
import shutil
import numpy
import sys
import config

color_dir = config.valid_overlay_tiles_dir
gray_dir = config.labels_dir

if not os.path.exists(gray_dir):
    print 'saving to ' + gray_dir
    os.mkdir(gray_dir)

classes = config.label_colours

label_flags = []
for i in range(0, config.classes):
    label_flags.append(0)

def color_map(img):
    gray_img = color.rgb2gray(img)
    #cnt = 0
    for x in range(0, 256):
        for y in range(0, 256):
            find_label = False
            for k in classes:
                label_color = k['color']
                if img[x][y][0] == label_color[0] and img[x][y][1] == label_color[1] and img[x][y][2] == label_color[2]:
                    label = k['label']
                    gray_img[x][y] = label

                    find_label = True
                    if label_flags[label] == 0:
                        #print('find label: ', gray_img[x][y])
                        label_flags[label] = 1
                    break

            if not find_label:
                if config.ignore_class is not None:
                    gray_img[x][y] = config.ignore_class
                else:
                    print('error not find label, ', gray_img[x][y])
                    print(img[x][y])
                #cnt = cnt + 1
    
    #print(cnt / float(256 * 256))
    return gray_img.astype(int)

def is_png(tile):
    items = tile.split('.')
    if len(items) == 2 and items[1] == 'png':
        return True
    else:
        return False

def main():
    tiles = os.listdir(color_dir)
    total_files = len(tiles)
    cnt = 0
    for tile in tiles:
        if not is_png(tile):
            print('not png: ' + tile)
            continue

        tile_file = os.path.join(color_dir, tile)
        new_tile_file = os.path.join(gray_dir, tile)

        if not os.path.exists(new_tile_file):
            img = io.imread(tile_file)
            if (type(img[0][0]) == numpy.uint8):
                print('invalid tile: ' + tile_file)
                continue
            print(type(img[0][0]))
            gray_img = color_map(img)

            io.imsave(new_tile_file, gray_img)

        cnt = cnt + 1
        if cnt % 10000 == 0:
            print(float(cnt) / total_files)

main()

print(label_flags)