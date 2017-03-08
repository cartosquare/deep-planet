import config
import os

if config.image_type == 'tif':
    merge_file = config.merged_tifs
    tif_dir = config.tifs_3857
else:
    merge_file = config.merged_png_tifs
    tif_dir = config.png_tile_dir

command = 'gdalbuildvrt %s %s/*.tif' % (merge_file, tif_dir)
print command
os.system(command)
