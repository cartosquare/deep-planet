# -*- coding: utf-8 -*-
import os
from skimage import color
from skimage import io
import shutil
import numpy
import sys
import config
from progressbar import *
import multiprocessing 

color_dir = config.valid_overlay_tiles_dir
gray_dir = config.labels_dir

if not os.path.exists(gray_dir):
    print 'saving to ' + gray_dir
    os.mkdir(gray_dir)

classes = config.label_colours

def color_map(img):
    gray_img = numpy.zeros((256, 256))
    for x in range(0, 256):
        for y in range(0, 256):
            find_label = False
            for k in classes:
                label_color = k['color']
                if img[x][y][0] == label_color[0] and img[x][y][1] == label_color[1] and img[x][y][2] == label_color[2]:
                    label = k['label']
                    gray_img[x][y] = label
   
                    find_label = True
                    break

            if not find_label:
                if config.ignore_class is not None:
                    gray_img[x][y] = config.ignore_class
                else:
                    print('error not find label, ', gray_img[x][y])
                    print(img[x][y])

    return gray_img.astype(int)

def is_png(tile):
    items = tile.split('.')
    if len(items) == 2 and items[1] == 'png':
        return True
    else:
        return False

def proces_img(tile):
    if not is_png(tile):
        print('not png: ' + tile)
        return

    tile_file = os.path.join(color_dir, tile)
    new_tile_file = os.path.join(gray_dir, tile)

    if not os.path.exists(new_tile_file):
        img = io.imread(tile_file)
        if (type(img[0][0]) == numpy.uint8):
            print('invalid tile: ' + tile_file)
            return

        gray_img = color_map(img)
        io.imsave(new_tile_file, gray_img)


def main():
    tiles = os.listdir(color_dir)

    # progress bar
    widgets = [Bar('>'), ' ', Percentage(), ' ', Timer(), ' ', ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=len(tiles)).start()

    nthreads = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=nthreads)

    for i, _ in enumerate(pool.imap_unordered(proces_img, tiles), 1):
        pbar.update(i)

    pool.close()
    pool.join()
    pbar.finish()

    
main()