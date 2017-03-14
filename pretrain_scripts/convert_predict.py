import os
import shutil
import config
from skimage import io
import random

def color_equal(a, b):
    return (a[0] == b[0] and a[1] == b[1] and a[2] == b[2])


if not os.path.exists(config.predict_tiles_dir):
    os.mkdir(config.predict_tiles_dir)

if not os.path.exists(config.predict_confidence_dir):
    os.mkdir(config.predict_confidence_dir)

if not os.path.exists(config.predict_merged_image_dir):
    os.mkdir(config.predict_merged_image_dir)
"""
with open(config.predict_txt) as f:
    count = 0
    for line in f:
        newline = line.strip().split()
        filename, file_extension = os.path.splitext(newline[0])
        items = filename.split('/')

        old_file = os.path.join(config.predict_image_dir, '%d.png' % count)
        new_file = os.path.join(config.predict_tiles_dir, '%s.png' % items[len(items) - 1])
        print '%s -> %s' % (old_file, new_file)

        shutil.copy(old_file, new_file)

        old_prob_file = os.path.join(config.predict_confidence_image_dir, '%d.png' % count)
        new_prob_file = os.path.join(config.predict_confidence_dir, '%s.png' % items[len(items) - 1])
        print '%s -> %s' % (old_prob_file, new_prob_file)

        shutil.copy(old_prob_file, new_prob_file)

        count = count + 1
"""

# smooth boundary
count = 0
tiles = os.listdir(config.predict_tiles_dir)
for tile in tiles:
    filename, file_extension = os.path.splitext(tile)
    if file_extension != '.png':
        print 'not png file', tile
        continue
    items = filename.split('_')
    if len(items) != 3:
        print('not target file', tile)
        continue

    #print('process file %s' % (tile))
    tile_path = os.path.join(config.predict_tiles_dir, tile)
    tile_prob_path = os.path.join(config.predict_confidence_dir, tile)
    img = io.imread(tile_path)
    img_label = io.imread(tile_prob_path)

    new_image_path = os.path.join(config.predict_merged_image_dir, tile)
    new_img = img.copy()

    z = int(items[0])
    x = int(items[1])
    y = int(items[2])

    left = '%d_%d_%d.png' % (z, x - 1, y)
    right = '%d_%d_%d.png' % (z, x + 1, y)
    top = '%d_%d_%d.png' % (z, x, y - 1)
    bottom = '%d_%d_%d.png' % (z, x, y + 1)

    #print('near tiles %s|%s|%s|%s' % (left_top, right_top, left_bottom, right_bottom))

    left_file = os.path.join(config.predict_tiles_dir, left)
    right_file = os.path.join(config.predict_tiles_dir, right)
    top_file = os.path.join(config.predict_tiles_dir, top)
    bottom_file = os.path.join(config.predict_tiles_dir, bottom)

    left_prob_file = os.path.join(config.predict_confidence_dir, left)
    right_prob_file = os.path.join(config.predict_confidence_dir, right)
    top_prob_file = os.path.join(config.predict_confidence_dir, top)
    bottom_prob_file = os.path.join(config.predict_confidence_dir, bottom)

    if os.path.exists(left_file) and os.path.exists(left_prob_file):
        left_img = io.imread(left_file)
        left_prob_img = io.imread(left_prob_file)
        # process left
        for x in range(0, 256):
            t0 = img[x][0]
            t1 = left_img[x][255]
            if color_equal(t0, t1):
                continue

            sum0 = 0
            sum1 = 0
            continue_cnt = 0
            steps = int(random.random() * 10)
            for i in range(0, steps):
                if color_equal(img[x][i], t0):
                    sum0 = sum0 + img_label[x][i]
                else:
                    break
            for i in range(0, steps):
                if color_equal(left_img[x][256 - i - 1], t1):
                    sum1 = sum1 + left_prob_img[x][256 - i - 1]
                    continue_cnt = continue_cnt + 1
                else:
                    break
            if sum0 < sum1:
                for i in range(0, continue_cnt):
                    new_img[x][i] = t1
    
    if os.path.exists(right_file) and os.path.exists(right_prob_file):
        right_img = io.imread(right_file)
        right_prob_img = io.imread(right_prob_file)

        # process right
        for x in range(0, 256):
            t0 = img[x][255]
            t1 = right_img[x][0]
            if color_equal(t0, t1):
                continue

            sum0 = 0
            sum1 = 0
            continue_cnt = 0
            steps = int(random.random() * 10)
            for i in range(0, steps):
                if color_equal(img[x][256 - i - 1], t0):
                    sum0 = sum0 + img_label[x][256 - i - 1]
                else:
                    break
            for i in range(0, steps):
                if color_equal(right_img[x][i], t1):
                    sum1 = sum1 + right_prob_img[x][i]
                    continue_cnt = continue_cnt + 1
                else:
                    break
            if sum0 < sum1:
                for i in range(0, continue_cnt):
                    new_img[x][256 - i - 1] = t1

    if os.path.exists(top_file) and os.path.exists(top_prob_file):
        top_img = io.imread(top_file)
        top_prob_img = io.imread(top_prob_file)

        # process top
        for y in range(0, 256):
            t0 = img[0][y]
            t1 = top_img[255][y]
            if color_equal(t0, t1):
                continue

            sum0 = 0
            sum1 = 0
            continue_cnt = 0
            steps = int(random.random() * 10)
            for i in range(0, steps):
                if color_equal(img[i][y], t0):
                    sum0 = sum0 + img_label[i][y]
                else:
                    break
            for i in range(0, steps):
                if color_equal(top_img[256 - i - 1][y], t1):
                    sum1 = sum1 + top_prob_img[256 - i - 1][y]
                    continue_cnt = continue_cnt + 1
                else:
                    break
            if sum0 < sum1:
                for i in range(0, continue_cnt):
                    new_img[i][y] = t1

    if os.path.exists(bottom_file) and os.path.exists(bottom_prob_file):
        bottom_img = io.imread(bottom_file)
        bottom_prob_img = io.imread(bottom_prob_file)

        # process bottom
        for y in range(0, 256):
            t0 = img[255][y]
            t1 = bottom_img[0][y]
            if color_equal(t0, t1):
                continue

            sum0 = 0
            sum1 = 0
            continue_cnt = 0
            steps = int(random.random() * 10)
            for i in range(0, steps):
                if color_equal(img[256 - i - 1][y], t0):
                    sum0 = sum0 + img_label[256 - i - 1][y]
                else:
                    break
            for i in range(0, steps):
                if color_equal(bottom_img[i][y], t1):
                    sum1 = sum1 + bottom_prob_img[i][y]
                    continue_cnt = continue_cnt + 1
                else:
                    break
            if sum0 < sum1:
                for i in range(0, continue_cnt):
                    new_img[256 - i - 1][y] = t1
    # saving
    io.imsave(new_image_path, new_img)
    count = count + 1
    if count % 100 == 0:
        print('%d of %d' % (count, len(tiles)))

"""
# merge with high probility
count = 0
tiles = os.listdir(config.predict_tiles_dir)
for tile in tiles:
    filename, file_extension = os.path.splitext(tile)
    if file_extension != '.png':
        print 'not png file', tile
        continue
    items = filename.split('_')
    if len(items) != 3:
        print('not target file', tile)
        continue

    print('process file %s' % (tile))
    tile_path = os.path.join(config.predict_tiles_dir, tile)
    tile_prob_path = os.path.join(config.predict_confidence_dir, tile)
    img = io.imread(tile_path)
    img_label = io.imread(tile_prob_path)

    new_image_path = os.path.join(config.predict_merged_image_dir, tile)
    new_img = img.copy()

    z = int(items[0])
    x = int(items[1])
    y = int(items[2])

    left_top = 'overlap_%d_%d_%d.png' % (z, x - 1, y - 1)
    right_top = 'overlap_%d_%d_%d.png' % (z, x, y - 1)
    left_bottom = 'overlap_%d_%d_%d.png' % (z, x - 1, y)
    right_bottom = 'overlap_%d_%d_%d.png' % (z, x, y)

    print('near tiles %s|%s|%s|%s' % (left_top, right_top, left_bottom, right_bottom))

    left_top_file = os.path.join(config.predict_tiles_dir, left_top)
    right_top_file = os.path.join(config.predict_tiles_dir, right_top)
    left_bottom_file = os.path.join(config.predict_tiles_dir, left_bottom)
    right_bottom_file = os.path.join(config.predict_tiles_dir, right_bottom)

    left_top_prob_file = os.path.join(config.predict_confidence_dir, left_top)
    right_top_prob_file = os.path.join(config.predict_confidence_dir, right_top)
    left_bottom_prob_file = os.path.join(config.predict_confidence_dir, left_bottom)
    right_bottom_prob_file = os.path.join(config.predict_confidence_dir, right_bottom)

    if os.path.exists(left_top_file) and os.path.exists(left_top_prob_file):
        print('merging %s' % left_top_file)
        left_top_img = io.imread(left_top_file)
        left_top_prob_img = io.imread(left_top_prob_file)
        # process left top
        ox = 128
        oy = 128
        for x in range(0, 128):
            for y in range(0, 128):
                if left_top_prob_img[x + ox][y + oy] > img_label[x][y]:
                    new_img[x][y] = left_top_img[x + ox][y + oy]

    
    if os.path.exists(right_top_file) and os.path.exists(right_top_prob_file):
        print('merging %s' % right_top_file)
        right_top_img = io.imread(right_top_file)
        right_top_prob_img = io.imread(right_top_prob_file)
        # process right top
        ox = 128
        oy = 0
        for x in range(0, 128):
            for y in range(128, 256):
                if right_top_prob_img[x + ox][y + oy] > img_label[x][y]:
                    new_img[x][y] = right_top_img[x + ox][y + oy]

    if os.path.exists(left_bottom_file) and os.path.exists(left_bottom_prob_file):
        print('merging %s' % left_bottom_file)
        left_bottom_img = io.imread(left_bottom_file)
        left_bottom_prob_img = io.imread(left_bottom_prob_file)
        # process left bottom
        ox = 0
        oy = 128
        for x in range(128, 256):
            for y in range(0, 128):
                if left_bottom_prob_img[x + ox][y + oy] > img_label[x][y]:
                    new_img[x][y] = left_bottom_img[x + ox][y + oy]

    if os.path.exists(right_bottom_file) and os.path.exists(right_bottom_prob_file):
        print('merging %s' % right_bottom_file)
        right_bottom_img = io.imread(right_bottom_file)
        right_bottom_prob_img = io.imread(right_bottom_prob_file)
        # process right bottom
        ox = 0
        oy = 0
        for x in range(128, 256):
            for y in range(128, 256):
                if right_bottom_prob_img[x + ox][y + oy] > img_label[x][y]:
                    new_img[x][y] = right_bottom_img[x + ox][y + oy]

    
    # saving
    io.imsave(new_image_path, new_img)
    count = count + 1
    if count % 100 == 0:
        print('%d of %d' % (count, len(tiles)))
"""