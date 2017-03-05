import os

train_dir = 'train'
cloud_index_dir = 'cloud_tiles'
cloud_dir = 'train_cloud'

if not os.path.exists(cloud_dir):
    print 'moving cloud tiles to ' + cloud_dir
    os.mkdir(cloud_dir)


cloud_files = os.listdir(cloud_index_dir)
print('#trains', len(cloud_files))

for cloud in cloud_files:
    items = cloud.split('.')
    if len(items) != 2 or items[1] != 'png':
        print('not tif file: ' + cloud)
        continue

    items = items[0].split('_')
    if (len(items) != 3):
        print('illegal filename ' + items)
        continue

    z = items[0]
    x = items[1]
    y = int(items[2])

    train_file = os.path.join(train, '%s_%s_%d.tif' % (z, x, y))
    train_new_file_path = os.path.join(cloud_dir, '%s_%s_%d.tif' % (z, x, y))

    if not os.path.exists(train_file):
        print 'not exists: ', train_file
        continue

    #print('%s->%s' % (label_old_file_path, label_new_file_path))

    shutil.copyfile(train_file, train_new_file_path)

    os.remove(train_file)