import os
import config
import math
import shutil

if not os.path.exists(config.png_tile_dir):
    os.mkdir(config.png_tile_dir)

if not os.path.exists(config.merged_png_tifs):
    command = 'gdal_merge.py -o %s -n 0 -a_nodata 0 %s/*.tif' % (config.merged_png_tifs, config.png_tile_dir)
    print command
    os.system(command)

command = "gdal2tiles.py -s epsg:3857 -z '10-%s' %s %s" % (config.tile_level, config.merged_png_tifs, config.png_tile_dir)
print command
os.system(command)

if config.image_type != 'png':
    exit()

# copy pngs to tif_tiles directory
if not os.path.exists(config.tif_tiles_dir ):
    os.mkdir(config.tif_tiles_dir)

google_tile_dir = os.path.join(config.png_tile_dir, str(config.tile_level))
xs = os.listdir(google_tile_dir)

ntiles = 2 ** config.tile_level
for x in xs:
    if x == '.DS_Store':
        continue

    x_path = os.path.join(google_tile_dir, x)
    ys = os.listdir(x_path)

    for y_postfix in ys:
        y_items = y_postfix.split('.')
        if len(y_items) != 2 or y_items[1] != 'png':
            continue

        y = y_items[0]
        y_flip = int(ntiles - float(y) - 1)

        old_file = os.path.join(x_path, y_postfix)
        new_file = os.path.join(config.tif_tiles_dir, '%s_%s_%d.png' % (config.tile_level, x, y_flip))
        shutil.copy(old_file, new_file)

