import os
from skimage import color
from skimage import io
import shutil
import math

train_dir = 'train'
label_old_dir = 'labels_color'
label_new_dir = 'labels_color_sub'

if not os.path.exists(label_new_dir):
    print 'saving to ' + label_new_dir
    os.mkdir(label_new_dir)

pow15 = math.pow(2, 15)
train_files = os.listdir(train_dir)
print('#trains', len(train_files))

for train in train_files:
    items = train.split('.')
    if len(items) != 2 or items[1] != 'tif':
        print('not tif file: ' + train)
        continue

    items = items[0].split('_')
    if (len(items) != 3):
        print('illegal filename ' + items)
        continue
        
    z = items[0]
    x = items[1]
    y = int(items[2])

    label_old_file_path = os.path.join(label_old_dir, '%s_%s_%d.png' % (z, x, y))
    label_new_file_path = os.path.join(label_new_dir, '%s_%s_%d.png' % (z, x, y))

    if not os.path.exists(label_old_file_path):
        print 'not exists: ', label_old_file_path
        continue
    

    #print('%s->%s' % (label_old_file_path, label_new_file_path))

    shutil.copyfile(label_old_file_path, label_new_file_path)