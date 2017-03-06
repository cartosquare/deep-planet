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


def color_map(gray_img):
    for x in range(0, 256):
        for y in range(0, 256):
            if gray_img[x][y] > 0:
                gray_img[x][y] = 1
                
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

            if (type(img[0][0]) != numpy.uint8):
                print('invalid tile: ' + tile_file)
                continue
            
            gray_img = color_map(img)

            io.imsave(new_tile_file, gray_img)

        cnt = cnt + 1
        if cnt % 10000 == 0:
            print(float(cnt) / total_files)

main()