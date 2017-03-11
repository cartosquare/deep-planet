import os
from skimage import color
from skimage import io
import shutil
import math
import config


train_dir = config.valid_tif_tiles_dir
label_old_dir = config.overlay_tiles_dir
label_new_dir = config.valid_overlay_tiles_dir

if not os.path.exists(label_new_dir):
    print 'saving to ' + label_new_dir
    os.mkdir(label_new_dir)

pow15 = math.pow(2, config.tile_level)
train_files = os.listdir(train_dir)

total_files = len(train_files)
step = total_files / 50
print('#trains', len(train_files))

count = 0
for train in train_files:
    count = count + 1
    if count % step == 0:
        print('%d of %d' % (count, total_files))
        
    items = train.split('.')
    if len(items) != 2 or items[1] != config.image_type:
        print('not valid train file: ' + train)
        continue

    items = items[0].split('_')
    if (len(items) != 3):
        print('illegal filename ' + items)
        continue
        
    z = items[0]
    x = items[1]
    y = items[2]

    label_old_file_path = os.path.join(label_old_dir, '%s_%s_%s.png' % (z, x, y))
    label_new_file_path = os.path.join(label_new_dir, '%s_%s_%s.png' % (z, x, y))

    if not os.path.exists(label_old_file_path):
        print 'not exists: ', label_old_file_path
        continue
    

    #print('%s->%s' % (label_old_file_path, label_new_file_path))

    shutil.copyfile(label_old_file_path, label_new_file_path)