import os
import config

if not os.path.exists(config.src_tifs):
    os.mkdir(config.src_tifs)

files = os.listdir(config.raw_tifs)
for file in files:
    file_path = os.path.join(config.raw_tifs, file)
    fetched_file_path = os.path.join(config.src_tifs, file)

    command = 'gdal_translate %s %s -b 1 -b 2 -b 3' % (file_path, fetched_file_path)
    print command

    os.system(command)
