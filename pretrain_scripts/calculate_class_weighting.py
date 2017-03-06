# -*- coding: utf-8 -*-

# reference: https://arxiv.org/pdf/1411.4734.pdf

# We train a more class-balanced version of our model by reweighting each class in the cross-entropy loss; we weight each pixel by αc = median freq/freq(c) where freq(c) is the number of pixels of class c divided by the total number of pixels in images where c is present, and median freq is the median of these frequencies.

# formulars:
# f(class) = frequency(class) / (image_count(class) * 256 * 256)
# weight(class) = median_of_f / f(class)

from skimage import io
import os
import numpy
import sys
import config

images = []
for ele in config.deploy:
    img_dir = '%s/training_set/%s/labels' % (config.deploy_dir, ele)
    imgs = os.listdir(img_dir)

    for i in range(len(imgs)):
        imgs[i] = os.path.join(img_dir, imgs[i])

    images = images + imgs

def is_png(tile):
    items = tile.split('.')
    if len(items) == 2 and items[1] == 'png':
        return True
    else:
        return False

# class, pixels, files
nclass = config.classes
class_info = []
for i in range(0, nclass):
    class_info.append({'pixels': 0, 'files': 0})

print '#class', len(class_info)

nimages = len(images)
count = 0
for img in images:
    if not is_png(img):
        count = count + 1
        continue

    #img_file = os.path.join(image_dir, img)
    img = io.imread(img)

    class_in_file = []
    for i in range(0, nclass):
        class_in_file.append(False)

    for i in range(0, 256):
        for j in range(0, 256): 
            if config.ignore_class is not None and img[i][j] == config.ignore_class:
                continue

            class_info[img[i][j]]['pixels'] = class_info[img[i][j]]['pixels'] + 1
            if not class_in_file[img[i][j]]:
                class_info[img[i][j]]['files'] = class_info[img[i][j]]['files'] + 1
                class_in_file[img[i][j]] = True

    count = count + 1
    if count % 1000 == 0:
        print count, float(count) / float(nimages)

print class_info

class_freq = []
for i in range(nclass):
    # f(class) = frequency(class) / (image_count(class) * 256 * 256)
    freq = float(class_info[i]['pixels']) / float(class_info[i]['files'] * 256 * 256)
    class_freq.append(freq)

print class_freq

median_freq = numpy.median(class_freq)
print median_freq

class_weights = []
for i in range(nclass):
    # weight(class) = median_of_f / f(class)
    weight = median_freq / class_freq[i]
    class_weights.append(weight)

print class_weights

# output
with open(config.weight_file, 'w') as f:
    for i in range(nclass):
        f.write('class_weighting: %f\n' % class_weights[i])
f.close()
# [0.38113902279553824, 0.2629976594140529, 1.1216093885997256, 0.47478722311768184, 1.3291472777753466, 0.38988060878278019, 0.39240495297574307, 0.68433058081588127, 0.62226191233152028, 0.25031724482826373, 0.76490255699248866, 1.8868312260936833, 1.1510200018430408, 0.62238631171287151, 1.4272370356387267, 0.20633089484939934, 1.0955709316521187, 1.4756046226848307, 0.61748552266419687, 4.6690302428351744, 0.98898990716977164, 2.7735831885541304, 2.7040509051247454, 0.19027909734716017, 11.110416525848569, 2.9648196525934267, 3.0766953035253177, 3.9147640359873277, 0.39894089492238449, 4.5239849157764169, 1.0]