# -*- coding: utf-8 -*-

##########################################
#
# configuration options
#
##########################################

data_name = 'sanxia_2012'
data_root = 'training_set/%s' % data_name

train_txt = 'train_%s.txt' % data_name
test_txt = 'test_%s.txt' % data_name

deploy = ['zhanjiang_july', 'zhanjiang_feb', 'zhanjiang_oct']
deploy_dir = 'deploy'

###########################################
classes = 2
ignore_class = None # ignore_class = 31
weight_file = '%s/training_set/weights.txt' % deploy_dir

####################### raster configuration ##################
# original images
raw_tifs = '%s/raw_tifs' % data_root
src_tifs = '%s/tifs' % data_root
src_projection = 'EPSG:32649'
src_nodata = '0'


# images projected to EPSG:3857
tifs_3857 = '%s/tifs_3857' % data_root

# merged virtual file
merged_tifs = '%s/merged.vrt' % data_root

# tif tiles directory
tif_tiles_dir = '%s/tif_tiles' % data_root
valid_tif_tiles_dir = '%s/valid_tif_tiles' % data_root
tile_level = 15
# extent: minx, miny, maxx, maxy

# for sanxia
# tile_extent = [11779924.71, 3315613.19, 12429394.15, 3728152.58]

# for zhanjiang
tile_extent = [12272311.892742, 2403831.52580, 12304619.6025, 2436356.63936]

####################### vector configuration ##################
overlay_dir = '%s/overlay' % data_root

# This configure should not be touch!!!
# because label_color directory is created by another program!!!
# If you change this, change config.json too!!!
overlay_tiles_dir = '%s/labels_color' % data_root
valid_overlay_tiles_dir = '%s/valid_labels_color' % data_root
labels_dir = '%s/labels' % data_root

####################### cloud configuration ############
cloud_dir = '%s/cloud' % data_root
cloud_tiles_dir = '%s/cloud_tiles' % data_root
valid_cloud_tiles_dir = '%s/valid_cloud_tiles' % data_root




