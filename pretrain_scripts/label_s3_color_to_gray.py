# -*- coding: utf-8 -*-
import os
from skimage import color
from skimage import io
import shutil
import numpy
import sys


if len(sys.argv) < 3:
    print('Usage: python label_s3_color_to_gray.py color_dir gray_dir')
    exit()

color_dir = sys.argv[1]
gray_dir = sys.argv[2]

if not os.path.exists(gray_dir):
    print 'saving to ' + gray_dir
    os.mkdir(gray_dir)

classes = [{
    'name': '常绿阔叶林', 'color': [146, 211, 48], 'label': 0
}, {
    'name': '常绿针叶林', 'color': [143, 144, 239], 'label': 1
}, {
    'name': '混交林', 'color': [225, 137, 77], 'label': 2
}, {
    'name': '落叶阔叶林', 'color': [26, 223, 220], 'label': 3
}, {
    'name': '落叶针叶林', 'color': [221, 122, 183], 'label': 4
}, {
    'name': '常绿灌木林', 'color': [233, 111, 111], 'label': 5
}, {
    'name': '落叶灌木林', 'color': [208, 24, 61], 'label': 6
}, {
    'name': '草地', 'color': [114, 202, 132], 'label': 7
}, {
    'name': '城市草本绿地', 'color': [224, 203, 118], 'label': 8
}, {
    'name': '旱地', 'color': [138, 94, 208], 'label': 9
}, {
    'name': '水田', 'color': [117, 168, 240], 'label': 10
}, {
    'name': '灌木种植园', 'color': [222, 57, 16], 'label': 11
}, {
    'name': '苗圃', 'color': [152, 80, 204], 'label': 12
}, {
    'name': '乔木种植园', 'color': [216, 173, 108], 'label': 13
}, {
    'name': '采矿场地', 'color': [84, 231, 48], 'label': 14
}, {
    'name': '城市居民地', 'color': [195, 226, 70], 'label': 15
}, {
    'name': '城市乔灌混合绿地', 'color': [148, 221, 99], 'label': 16
}, {
    'name': '城市乔木绿地', 'color': [210, 210, 105], 'label': 17
}, {
    'name': '独立工业和商业用地', 'color': [193, 33, 237], 'label': 18
}, {
    'name': '基础设施', 'color': [205, 78, 207], 'label': 19
}, {
    'name': '垃圾填埋场', 'color': [37, 75, 215], 'label': 20
}, {
    'name': '镇村居民地', 'color': [20, 223, 139], 'label': 21
}, {
    'name': '河流季节性水面', 'color': [217, 114, 198], 'label': 22
}, {
    'name': '湖泊', 'color': [145, 124, 99], 'label': 23
}, {
    'name': '坑塘', 'color': [71, 36, 225], 'label': 24
}, {
    'name': '水库', 'color': [15, 231, 185], 'label': 25
}, {
    'name': '水库季节性水面', 'color': [210, 23, 101], 'label': 26
}, {
    'name': '水生植被', 'color': [31, 148, 221], 'label': 27
}, {
    'name': '永久河流水面', 'color': [92, 220, 92], 'label': 28
}, {
    'name': '坚硬表面', 'color': [66, 240, 133], 'label': 29
}, {
    'name': '松散表面', 'color': [114, 209, 230], 'label': 30
}
]

label_flags = []
for i in range(0, 31):
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
                #print('not find label, ', gray_img[x][y])
                #print(img[x][y])

                gray_img[x][y] = 31
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

# tile_file = '/Volumes/DataCube/cool_files/sanxia/15_26018_13628_val.png'
# new_tile_file = '/Volumes/DataCube/cool_files/sanxia/15_26018_13628_val_gray.png'

# img = io.imread(tile_file)
# gray_img = color_map(img)

# print('saving...' + new_tile_file)
# io.imsave(new_tile_file, gray_img)

# img = io.imread(new_tile_file)

# for x in range(0, 256):
#     for y in range(0, 256):
#         if img[x][y] > 11:
#             print(img[x][y])