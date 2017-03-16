# -*- coding: utf-8 -*-

import os
import shutil
import sys
import math
import numpy
import random
import datetime
from PIL import Image
from osgeo import gdal
# this allows GDAL to throw Python Exceptions
gdal.UseExceptions()
import multiprocessing 
from progressbar import *
from skimage import io
import json

##########################################
#
# configuration class
#
##########################################

class DeepPlanetConfig:
	def Initialize(self, pobject):
		#********************************   通用参数  **********************************
		# could be train or predict
		# when train, tiles with nodata value will be remove
		# when predict, tiles with nodata will be keep remain
		if 'mode' in pobject:
			self.mode = pobject['mode']
		else:
			self.mode = 'train'
		
		if 'process_visualize' in pobject:
			self.process_visualize =  pobject['process_visualize']
		else:
			self.process_visualize = False

		if 'process_analyze' in pobject:
			self.process_analyze =  pobject['process_analyze']
		else:
			self.process_analyze = True

		# 训练样本大小，目前只支持 256px * 256px
		self.dim_row = 256
		self.dim_col = 256

		# 训练样本分辨率（0-19）
		if 'tile_level' in pobject:
			self.tile_level = pobject['tile_level']
		else:
			self.tile_level = '15'

		if 'visualize_level' in pobject:
			self.visualize_level = pobject['visualize_level']
		else:
			self.visualize_level = '10-15'

		# 训练样本类型。可以为 'tif' 或是 'png'
		if 'image_type' in pobject:
			self.image_type = pobject['image_type']
		else:
			self.image_type = 'tif'

		# 影像投影和nodata值
		#src_projection = 'EPSG:32649'
		if 'src_projection' in pobject:
			self.src_projection = pobject['src_projection']
		else:
			print('warning: no src projection set!')
			return False

		if 'src_nodata' in pobject:
			self.src_nodata = pobject['src_nodata']
		else:
			print('warning: no src_nodata set! default to 0')
			self.src_nodata = '0'

		# 训练的波段
		#rapideye false-color-compose bands: [5, 3, 2]
		# FG false-color compose bands: [4, 3, 2]
		# planetlabs [1, 2, 3]
		if 'analyze_bands' in pobject:
			self.analyze_bands = pobject['analyze_bands']
		else:
			print('warning: no analyze_bands set! default to [1 2 3]')
			self.analyze_bands = [1, 2, 3]

		# 可视化的波段
		if 'visualize_bands' in pobject:
			self.visualize_bands = pobject['visualize_bands']
		else:
			print('warning: no visualize_bands set! default to [1 2 3]')
			self.visualize_bands = [1, 2, 3]

		# 需要分割的类别数
		if 'classes' in pobject:
			self.classes = pobject['classes']
		else:
			print('warning: must specify classes')
			return False

		#以及需要忽略的类别（一般是背景）
		#ignore_class = None # 
		if 'ignore_class' in pobject:
			self.ignore_class = pobject['ignore_class']
		else:
			print('warning: no ignore_class set! default to None')
			self.ignore_class = None

		# 数据目录。即处理训练样本的目录所在。执行一个分割任务时，一般在training_set目录下新建一个目录。
		if 'data_name' in pobject:
			self.data_name = pobject['data_name']
		else:
			print('data_name must specified!!!')
			return False
		
		if 'tile_extent' in pobject:
			# 训练样本范围
			# for sanxia
			#tile_extent = [11779924.71, 3315613.19, 12429394.15, 3728152.58]
			# for zhanjiang
			#tile_extent = [12272311.892742, 2403831.52580, 12304619.6025, 2436356.63936]
			self.tile_extent = pobject['tile_extent']
		else:
			print('tile_extent must specified!')
			return False

		if 'deploy' in pobject:
			# 需要发布的训练集（名称和数据目录一样，可以指定多个数据目录进行合并）
			self.deploy = pobject['deploy']
		else:
			self.deploy = [self.data_name]

		# 测试样本数
		if 'test_iter' in pobject:
			self.test_iter = pobject['test_iter']
		else:
			self.test_iter = 1


		# 类别标签
		if 'label_colours' in pobject:
			self.label_colours = pobject['label_colours']
		else:
			print 'label_colours must specified!!!'
			return False


		# 发布训练样本的目录
		self.deploy_dir = 'deploy'

		self.data_root = 'training_set/%s' % self.data_name


		# 训练和测试网络的
		self.trained_weights = '%s/models/Training/envnet_iter_10000.caffemodel' % self.data_root
		self.test_weights = '%s/models/inference/test_weights.caffemodel' % self.data_root

		self.log_file = '%s/log.txt' % self.data_root

		#********************************   影像样本准备时涉及的参数  **************************
		# 原始影像所在的目录
		self.src_tifs = '%s/tifs' % self.data_root

		# 投影为 web 墨卡托的影像所在的目录
		self.tifs_3857 = '%s/tifs_3857' % self.data_root

		# 用于分析的影像目录
		self.analyze_tifs_dir = '%s/analyze_tif' % self.data_root

		# 用于可视化的影像目录
		self.visualize_tifs_dir = '%s/visualize_tif' % self.data_root

		# 将 tifs_3857 中的影像合并成的虚拟文件（为了下一步的切割）
		self.merged_analyze_file = '%s/merged_analyze.tif' % self.data_root

		# 将 png_tile_dir 中的影像合并成的虚拟文件（为了下一步的切割）
		self.merged_visualize_file = '%s/merged_visualize.tif' % self.data_root

		# 切割后的训练瓦片目录
		self.analyze_tiles_dir = '%s/analyze_tiles' % self.data_root

		# 切割后的训练瓦片目录
		self.visualize_tiles_dir = '%s/visualize_tiles' % self.data_root

		#******************************* 标注样本准备涉及的参数 *************************
		# 训练标注，shapefile格式，所在的目录
		self.overlay_dir = '%s/overlay' % self.data_root
		self.style_file = '%s/style.json' % self.data_root
		self.lod_file = '%s/lod.json' % self.data_root
		self.tiler_file = '%s/tiler_config.json' % self.data_root

		# This configure should not be touch!!!
		# because label_color directory is created by another program!!!
		# If you change this, change config.json too!!!
		# 标注切割后所在的目录（rgb）
		self.overlay_tiles_dir = '%s/labels_color' % self.data_root
		# 过滤无效标注后的目录（rgb）
		self.valid_overlay_tiles_dir = '%s/valid_labels_color' % self.data_root
		# rgb标注转换为灰度标注的目录
		self.labels_dir = '%s/labels' % self.data_root

		#********************************* 训练样本输出的参数 ***********************
		# 训练集合测试集文件分布
		self.train_txt = '%s/train.txt' % (self.data_root)
		self.test_txt = '%s/test.txt' % (self.data_root)
		self.predict_txt = '%s/predict.txt' % (self.data_root)

		#********************************  测试时需要的参数 ***************************
		# 模型所在目录
		self.model_directory = '%s/models/inference' % self.data_root
		# 训练模型
		self.train_model = '%s/models/segnet_train.prototxt' % self.data_root
		# 测试模型
		self.test_model = '%s/models/segnet_inference.prototxt' % self.data_root
		# 分类权重
		self.weight_file = '%s/weights.txt' % self.deploy_dir

		# 测试数据的输出目录
		self.test_img_dir = '%s/models/img' % self.data_root
		self.test_gt_dir = '%s/models/gt' % self.data_root
		self.test_pd_dir = '%s/models/pd' % self.data_root

		#****************************** cloud configuration *********************
		self.cloud_dir = '%s/cloud' % self.data_root
		self.cloud_tiles_dir = '%s/cloud_tiles' % self.data_root
		self.valid_cloud_tiles_dir = '%s/valid_cloud_tiles' % self.data_root

		#***************************** test configuration ****************
		self.predict_tif = '%s/predict_area.tif' % self.data_root


		# predict tiles dir
		self.predict_image_dir = '%s/pd' % self.data_root
		self.predict_tiles_dir = '%s/predict_tiles' % self.data_root

		self.predict_confidence_image_dir = '%s/pd_prob' % self.data_root
		self.predict_confidence_dir = '%s/predict_prob' % self.data_root

		self.predict_merged_image_dir = '%s/predict_merged_tiles' % self.data_root

		return True



################################## Functions ########################
def log(file_handle, message):
    current_time = datetime.datetime.now()
    flog.write('[%s] %s\n' % (current_time.strftime('%Y-%m-%d %H:%M:%S'), message))
    flog.flush()

def create_directory_if_not_exist(dir):
    if not os.path.exists(dir):
        os.mkdir(dir)

def is_tiff(file):
    filename, file_extension = os.path.splitext(file)
    return (file_extension == '.tif')

def is_png(file):
    filename, file_extension = os.path.splitext(file)
    return (file_extension == '.png')

def tiff_count(src_dir):
    files = os.listdir(src_dir)
    count = 0
    
    for file in files:
        file_path = os.path.join(src_dir, file)
        if is_tiff(file_path):
            count = count + 1
            tif_file = file_path
    return (count, tif_file)

def reproj(src_dir, src_proj, src_nodata, dest_dir):
    log(flog, 'projecting files from %s with projection %s and nodata value %s to %s ...' % (src_dir, src_proj, src_nodata, dest_dir))
    create_directory_if_not_exist(dest_dir)

    files = os.listdir(src_dir)
    for file in files:
        file_path = os.path.join(src_dir, file)
        projected_file_path = os.path.join(dest_dir, file)

        if not is_tiff(file):
		    print 'unsupport file ', file
		    continue

        command = 'gdalwarp -s_srs %s -t_srs EPSG:3857 -r bilinear -srcnodata %s -dstnodata 0 %s %s' % (src_proj, src_nodata, file_path, projected_file_path)
        print command

        os.system(command)


def fetch_bands(src_dir, dest_dir, band_list, encode_type, image_type):
    log(flog, 'fetch bands %s from %s to %s for %s' % (str(band_list), src_dir, dest_dir, encode_type))
    create_directory_if_not_exist(dest_dir)

    files = os.listdir(src_dir)
    for file in files:
        file_path = os.path.join(src_dir, file)
        fetched_file_path = os.path.join(dest_dir, file)

        if not is_tiff(file):
		    print 'unsupport file ', file
		    continue

        band_str = ''
        for band in band_list:
            band_str = band_str + (' -b %s' % band)

        if encode_type == 'analyze' and image_type == 'tif':
            command = 'gdal_translate -ot UInt16 %s %s %s' % (file_path, fetched_file_path, band_str)
        else:
            # visualize or analyze but using png
            command = 'gdal_translate -scale -ot Byte -co COMPRESS=JPEG -co JPEG_QUALITY=100 %s %s %s' % (file_path, fetched_file_path, band_str)
        print command

        os.system(command)

def build_overview(work_dir):
    log(flog, 'building overview for files under %s' % work_dir)

    for parent, dirnames, filenames in os.walk(work_dir):
	    for file in filenames:
		    if not is_tiff(file):
			    print 'unsupport file ', file
			    continue

		    command = "gdaladdo -r gauss -ro %s 2 4 8 16" % (os.path.join(parent, file))
		    print command
		    os.system(command)


def build_file_overview(file):
    log(flog, 'building overview for %s' % (file))

    command = "gdaladdo -r gauss -ro %s 2 4 8 16" % (file)
    print command
    os.system(command)


def merge_as_virtual_dataset(src_dir, merged_file):
    log(flog, 'merging virtual dataset from files under %s to %s ...' % (src_dir, merged_file))

    command = 'gdalbuildvrt %s %s/*.tif' % (merged_file, src_dir)
    print command
    os.system(command)

def merge(src_dir, merged_file):
    log(flog, 'merging files under %s to %s ...' % (src_dir, merged_file))

    command = 'gdal_merge.py -o %s -n 0 -a_nodata 0 %s/*.tif' % (merged_file, src_dir)
    print command
    os.system(command)

def tiler_tif(src, out, level, extent): 
    log(flog, 'tilering level %d, extent %s, from %s to %s ...' % (level, str(extent), src, out))
    create_directory_if_not_exist(out)

    out_format = 'GTiff'
    
    # tile extent
    minx = extent[0]
    miny = extent[1]
    maxx = extent[2]
    maxy = extent[3]
    print minx, miny, maxx, maxy
      
    # mercator parameters
    worldOriginalx = -20037508.342787
    worldOriginaly = 20037508.342787

    # tile size
    tileSize = 256
    
    # resolutions for each level
    zoomReses =[156543.033928,78271.516964,39135.758482,19567.879241,9783.9396205,4891.96981025,2445.984905125,1222.9924525625,611.49622628125,305.748113140625,152.8740565703125,76.43702828515625,38.21851414257813,19.10925707128906,9.55462853564453,4.777314267822266,2.388657133911133,1.194328566955567,0.597164283477783,0.298582141738892,0.14929107086945,0.07464553543473];
    
    tileExtent = tileSize * zoomReses[level]
    minBundlex = int((minx - worldOriginalx) / tileExtent)
    minBundley = int((worldOriginaly - maxy) / tileExtent)

    maxBundlex = int((maxx - worldOriginalx) / tileExtent)
    maxBundley = int((worldOriginaly - miny) / tileExtent)

    totalBundles = (maxBundlex - minBundlex + 1) * (maxBundley - minBundley + 1)
    print "[Normal] total tiles #%s" % totalBundles
    
    step = totalBundles / 50 + 1  
    count = 0
    maxIdx = 2 ** level - 1
    print "Max Idx: ", maxIdx
    sys.stdout.flush()

    for i in range(minBundlex, maxBundlex + 1):
        if i > maxIdx:
            continue
        for j in range(minBundley, maxBundley + 1):
            if j > maxIdx:
                continue
                
            tilepath = os.path.join(out, "%s" % (str(level) + "_" + str(i) + "_" + str(j) + ".tif"))
           
            tileMinx = worldOriginalx + i * tileExtent
            tileMaxx = tileMinx + tileExtent
            tileMaxy = worldOriginaly - j * tileExtent
            tileMiny = tileMaxy - tileExtent
        
            command = "gdalwarp -of %s -te %s %s %s %s -ts 256 256 -r near -multi -q %s %s" % (out_format, format(tileMinx, '.10f'), format(tileMiny, '.10f'), format(tileMaxx, '.10f'), format(tileMaxy, '.10f'), src, tilepath)
            
            #print command
            os.system(command)
            
            count += 1
            # process bar
            if (count % step == 0):
                print "[Normal]level %s current processed: %.2f%%" % (str(level), (count / float(totalBundles) * 100))
		sys.stdout.flush()
                

def flatten_google_dir(out, level):
    # reorganize files
    google_tile_dir = os.path.join(out, str(level))
    xs = os.listdir(google_tile_dir)

    ntiles = 2 ** int(level)
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
            new_file = os.path.join(out, '%s_%s_%d.png' % (level, x, y_flip))
            shutil.copy(old_file, new_file)
    #os.rmdir(google_tile_dir)
    shutil.rmtree(google_tile_dir)

def tiler_png(src, out, level):
    log(flog, 'tilering png level %s, from %s to %s ...' % (str(level), src, out))
    create_directory_if_not_exist(out)

    command = "gdal2tiles.py -s epsg:3857 -a 0 -z '%s' %s %s" % (level, src, out)
    print command
    os.system(command)

    level_arr = level.split('-')
    if len(level_arr) == 1:
        flatten_google_dir(out, int(level_arr[0]))
    else:
        for i in range(int(level_arr[0]), int(level_arr[1]) + 1):
            flatten_google_dir(out, i)

def proces_analyze_img(image_file):
    if is_png(image_file):
        img = io.imread(image_file)
        for x in range(0, 256):
            for y in range(0, 256):
                #if img[x][y][0] == 0 and img[x][y][1] == 0 and img[x][y][2] == 0 and img[x][y][3] == 0:
                if img[x][y][0] == 0 and img[x][y][1] == 0 and img[x][y][2] == 0:
                    os.unlink(image_file)
                    return 

def proces_predict_img(image_file):
    if is_png(image_file):
        img = io.imread(image_file)
        pixels = numpy.sum(img[0])
        print pixels
        if pixels == 0:
            os.unlink(image_file)

def proces_tif(tif_file):
    if not is_tiff(tif_file):
        os.unlink(tif_file)
        return

    try:
        src_ds = gdal.Open(tif_file)
    except RuntimeError, e:
        os.unlink(tif_file)
        return

    nodata = False
    for band in range(src_ds.RasterCount):
        band += 1
        srcband = src_ds.GetRasterBand(band)
        if srcband is None:
            nodata = True
            break
        
        try:
            stats = srcband.GetStatistics(True, True)
        except RuntimeError, e:
            nodata = True
            break

        if stats is None:
            nodata = True
            break

        dataraster = srcband.ReadAsArray()
        row = len(dataraster)
        col = len(dataraster[1])

        for r in range(row):
            for c in range(col):
                if dataraster[r][c] == 0 or dataraster[r][c] is None:
                    #print r, c, dataraster[r][c]
                    nodata = True
                    break
            if nodata:
                break
        if nodata:
            break

    if nodata:
        os.unlink(tif_file)


def proces_predict_tif(tif_file):
    if not is_tiff(tif_file):
        os.unlink(tif_file)
        return

    try:
        src_ds = gdal.Open(tif_file)
    except RuntimeError, e:
        os.unlink(tif_file)
        return

    nodata = False
    for band in range(src_ds.RasterCount):
        band += 1
        srcband = src_ds.GetRasterBand(band)
        if srcband is None:
            nodata = True
            break
        
        try:
            stats = srcband.GetStatistics(True, True)
        except RuntimeError, e:
            nodata = True
            break

        if stats is None:
            nodata = True
            break

    if nodata:
        os.unlink(tif_file)


def rm_invalid_tiles(src_dir, image_type, mode):
    log(flog, 'deleting invalid %s tiles from %s ...' % (image_type, src_dir))

    files = os.listdir(src_dir)
    for i in range(len(files)):
        filename = files[i].split('/')[-1]
        files[i] = os.path.join(src_dir, files[i])

    # progress bar
    widgets = [Bar('>'), ' ', Percentage(), ' ', Timer(), ' ', ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=len(files)).start()

    nthreads = multiprocessing.cpu_count() * 2
    pool = multiprocessing.Pool(processes=nthreads)

    if image_type == 'tif':
        if mode == 'train':
            for i, _ in enumerate(pool.imap_unordered(proces_tif, files), 1):
                pbar.update(i)
        else:
            # mode == 'predict'
            for i, _ in enumerate(pool.imap_unordered(proces_predict_tif, files), 1):
                pbar.update(i)
    else:
        if mode == 'train':
            for i, _ in enumerate(pool.imap_unordered(proces_analyze_img, files), 1):
                pbar.update(i)
        else:
            for i, _ in enumerate(pool.imap_unordered(proces_analyze_img, files), 1):
                pbar.update(i)

    pool.close()
    pool.join()
    pbar.finish()

    # remove not tif/png files
    files = os.listdir(src_dir)
    for i in range(len(files)):
        file_path = os.path.join(src_dir, files[i])
        if image_type == 'tif':
            if not is_tiff(file_path):
                os.unlink(file_path)
        else:
            if not is_png(file_path):
                os.unlink(file_path)

def create_overlap_predict_tiles(work_dir):
    files = os.listdir(work_dir)
    for file in files:
        if not is_png(file):
            print('not png file %s' % file)
            continue

        items = file.split('.')[0].split('_')
        if (len(items) != 3):
            print('bad file %s' % file)
            continue

        z = int(items[0])
        x = int(items[1])
        y = int(items[2])

        left_top = '%d_%d_%d.png' % (z, x, y)
        right_top = '%d_%d_%d.png' % (z, x + 1, y)
        left_bottom = '%d_%d_%d.png' % (z, x, y + 1)
        right_bottom = '%d_%d_%d.png' % (z, x + 1, y + 1)

        left_top_file = os.path.join(work_dir, left_top)
        right_top_file = os.path.join(work_dir, right_top)
        left_bottom_file = os.path.join(work_dir, left_bottom)
        right_bottom_file = os.path.join(work_dir, right_bottom)

        if os.path.exists(right_top_file) and os.path.exists(left_bottom_file) and os.path.exists(right_bottom_file):
            left_top_image = Image.open(left_top_file)
            right_top_image = Image.open(right_top_file)
            left_bottom_image = Image.open(left_bottom_file)
            right_bottom_image = Image.open(right_bottom_file)

            new_im = Image.new('RGB', (256, 256))
            new_im.paste(left_top_image, (-128, -128))
            new_im.paste(right_top_image, (128, -128))
            new_im.paste(left_bottom_image, (-128, 128))
            new_im.paste(right_bottom_image, (128, 128))

            new_im_file = os.path.join(work_dir, 'overlap_%d_%d_%d.png' % (z, x, y))
            #print('from %s|%s|%s|%s to %s' % (left_top, right_top, left_bottom, right_bottom, new_im_file))
            new_im.save(new_im_file, "PNG")


def write_predict_txt(work_dir, file_path, image_type):
    with open(file_path, 'w') as f:
        files = os.listdir(work_dir)
        for file in files:
            file_path = os.path.join(work_dir, file)
            if image_type == 'tif':
                if is_tiff(file_path):
                    f.write('%s %s\n' % (file_path, file_path))
            else:
                if is_png(file_path):
                    f.write('%s %s\n' % (file_path, file_path))


def copy_labels():
    log(flog, 'copy valid label from %s into %s ...' % (config.overlay_tiles_dir, config.valid_overlay_tiles_dir))

    train_dir = config.analyze_tiles_dir
    label_old_dir = config.overlay_tiles_dir
    label_new_dir = config.valid_overlay_tiles_dir

    if not os.path.exists(label_new_dir):
        print 'saving to ' + label_new_dir
        os.mkdir(label_new_dir)

    pow15 = math.pow(2, int(config.tile_level))
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

        shutil.copyfile(label_old_file_path, label_new_file_path)


def tiler_overlay():
    log(flog, 'tiler overlay into %s ...' % (config.overlay_tiles_dir))

    config_object = {
        "name": 'DeepPlanet',
        "map": config.data_root,
        "fonts": ".",
        "dest": config.overlay_tiles_dir,
        "lod": config.lod_file,
        "def": config.style_file,
        "save_cloud": 0,
        "levels": [int(config.tile_level)],
        "types": [0],
        "store_backend": "file",
        "boundary": config.tile_extent,
        "overwrite": 1,
        "max_threads": 1,
        "retina": 1,
        "render_label": 0,
        "expand": 0
    }

    with open(config.tiler_file, 'w') as outfile:
        json.dump(config_object, outfile)

    if not os.path.exists(config.overlay_tiles_dir):
        os.mkdir(config.overlay_tiles_dir)

    command = './bin/tiler %s' % (config.tiler_file)
    print command
    os.system(command)


def color_map_2class(gray_img):
    for x in range(0, 256):
        for y in range(0, 256):
            if gray_img[x][y] > 0:
                gray_img[x][y] = 1
                
    return gray_img.astype(int)


def color_map(img):
    gray_img = numpy.zeros((256, 256))
    for x in range(0, 256):
        for y in range(0, 256):
            find_label = False
            for k in config.label_colours:
                label_color = k['color']
                if img[x][y][0] == label_color[0] and img[x][y][1] == label_color[1] and img[x][y][2] == label_color[2]:
                    label = k['label']
                    gray_img[x][y] = label
   
                    find_label = True
                    break

            if not find_label:
                if config.ignore_class is not None:
                    gray_img[x][y] = config.ignore_class
                else:
                    print('error not find label, ', gray_img[x][y])
                    print(img[x][y])

    return gray_img.astype(int)

def proces_label_img(tile):
    if not is_png(tile):
        print('not png: ' + tile)
        return

    tile_file = os.path.join(config.valid_overlay_tiles_dir, tile)
    new_tile_file = os.path.join(config.labels_dir, tile)

    if not os.path.exists(new_tile_file):
        img = io.imread(tile_file)

        if config.classes > 2:
            if (type(img[0][0]) == numpy.uint8):
                print('invalid tile: ' + tile_file)
                return
            gray_img = color_map(img)
        else:
            if (type(img[0][0]) != numpy.uint8):
                print('invalid tile: ' + tile_file)
                return
            gray_img = color_map_2class(img)

        io.imsave(new_tile_file, gray_img)


def color2gray():
    log(flog, 'convert color images from %s into gray iamage %s ...' % (config.valid_overlay_tiles_dir, config.labels_dir))

    color_dir = config.valid_overlay_tiles_dir
    gray_dir = config.labels_dir

    if not os.path.exists(gray_dir):
        print 'saving to ' + gray_dir
        os.mkdir(gray_dir)

    tiles = os.listdir(color_dir)

    # progress bar
    widgets = [Bar('>'), ' ', Percentage(), ' ', Timer(), ' ', ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=len(tiles)).start()

    nthreads = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=nthreads)

    for i, _ in enumerate(pool.imap_unordered(proces_label_img, tiles), 1):
        pbar.update(i)

    pool.close()
    pool.join()
    pbar.finish()


def split_train_test():
    train_dir = config.analyze_tiles_dir
    label_dir = config.labels_dir
    train_file = config.train_txt
    test_file = config.test_txt

    log(flog, 'split train test from %s | %s ...' % (train_dir, label_dir))
    
    ftrain = open(train_file, 'w')
    ftest = open(test_file, 'w')

    tiles = os.listdir(train_dir)
    random.shuffle(tiles)

    total_files = len(tiles)
    cut_line = int(total_files * 0.8)

    print('#total tiles: %d, #training tiles: %d, #testing tiles: %d' % (total_files, cut_line, total_files - cut_line))

    pow15 = math.pow(2, int(config.tile_level))

    for i in range(0, total_files):
        tile_name = tiles[i]

        if config.image_type == 'tif':
            if not is_tiff(tile_name):
                print('not tif file: ' + tile_name)
                continue
        else:
            if not is_png(tile_name):
                print('not png file: ' + tile_name)
                continue

        items = tile_name.split('.')[0].split('_')
        if (len(items) != 3):
            print('illegal filename ' + items)
            continue

        z = items[0]
        x = items[1] 
        y = items[2]

        img_tile = '%s/%s_%s_%s.%s' % (train_dir, z, x, y, config.image_type)
        label_tile = '%s/%s_%s_%s.png' % (label_dir, z, x, y)

        if not os.path.exists(label_tile):
            print('not exists ' + label_tile)
            continue

        if i < cut_line:
            # write train.txt
            ftrain.write('%s %s\n' % (img_tile, label_tile))
        else:
            # write test.txt
            ftest.write('%s %s\n' % (img_tile, label_tile))

    ftrain.close()
    ftest.close()


def calculate_weights():
    log(flog, 'calculating weights to %s ...' % (config.weight_file))

    items = config.labels_dir.split('/')
    label_dir_name = items[len(items) - 1]

    images = []
    for ele in config.deploy:
        img_dir = '%s/training_set/%s/%s' % (config.deploy_dir, ele, label_dir_name)
        imgs = os.listdir(img_dir)

        for i in range(len(imgs)):
            imgs[i] = os.path.join(img_dir, imgs[i])

        images = images + imgs

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


def deploy():
    log(flog, 'deploy dataset %s to %s ...' % (str(config.deploy), config.deploy_dir))

    if not os.path.exists(config.deploy_dir):
        os.mkdir(config.deploy_dir) 

    training_dir = '%s/training_set' % (config.deploy_dir)
    if not os.path.exists(training_dir):
        os.mkdir(training_dir) 

    train_txt = '%s/train.txt' % training_dir
    test_txt = '%s/test.txt' % training_dir

    ftrain = open(train_txt, 'w')
    ftest = open(test_txt, 'w')

    for ele in config.deploy:
        print 'process data set ', ele

        data_dir = '%s/training_set/%s' % (config.deploy_dir, ele)
        if not os.path.exists(data_dir):
            os.mkdir(data_dir)

        # train dir
        items = config.analyze_tiles_dir.split('/')
        analyze_tiles_dir_name = items[len(items) - 1]

        train_dir = 'training_set/%s/%s' % (ele, analyze_tiles_dir_name)
        new_train_dir = '%s/%s' % (data_dir, analyze_tiles_dir_name)

        shutil.copytree(train_dir, new_train_dir)

        # label dir 
        items = config.labels_dir.split('/')
        label_dir_name = items[len(items) - 1]
        label_dir = 'training_set/%s/%s' % (ele, label_dir_name)
        new_label_dir = '%s/%s' % (data_dir, label_dir_name)

        shutil.copytree(label_dir, new_label_dir)

        # train file
        train_file = 'training_set/%s/train.txt' % (ele)
        with open(train_file, 'r') as f:
            for line in f:
                ftrain.write(line)
    
        # test file
        test_file = 'training_set/%s/test.txt' % (ele)
        with open(test_file, 'r') as f:
            for line in f:
                ftest.write(line)

    ftrain.close()
    ftest.close()


def parseOptions(config_file):
    with open(config_file) as json_data:
        d = json.load(json_data)
        return d

def need_build_overview(dir_name):
    files = os.listdir(dir_name)
    for file in files:
        items = file.split('.')
        if items[len(items) - 1] == 'ovr':
            return False
    return True


if __name__=='__main__': 
    # Parse command line options
    if len(sys.argv) < 2:
        print('need config file!!!\n')
        exit()
    
    config_cmd = parseOptions(sys.argv[1])
    config = DeepPlanetConfig()
    if not config.Initialize(config_cmd):
        print('initialize fail! exist...')
        exit()

    # Step 0, Open log file
    flog = open(config.log_file, 'w')
    log(flog, 'tiler raster begins, this may take a while, go to drink a cup of coffee ...')

    # Step 1, Reprojection if needed 
    if config.src_projection != 'EPSG:3857':
        if config.src_nodata is None:
            log(flog, 'src nodata must specify! program exist ...')
            exit()

        if not os.path.exists(config.tifs_3857):
            reproj(config.src_tifs, config.src_projection, config.src_nodata, config.tifs_3857)
        else:
            log(flog, 'skip reprojtion progress ...')
        projected_dir = config.tifs_3857
    else:
        log(flog, 'no projection progress need.')
        projected_dir = config.src_tifs
    
    if config.process_analyze and not os.path.exists(config.analyze_tiles_dir):
        # Step 2, fetch bands for analyze and visualize
        if len(config.analyze_bands) == 0:
            # use all bands for analyze
            log(flog, 'use all bands for analyze')
            analyze_dir = projected_dir
        else:
            if not os.path.exists(config.analyze_tifs_dir):
                fetch_bands(projected_dir, config.analyze_tifs_dir, config.analyze_bands, 'analyze', config.image_type)
            else:
                log(flog, 'skip fetch bands progress ...')
            analyze_dir = config.analyze_tifs_dir
        
        # Step 3, build overview for analyze and visualize datas
        if need_build_overview(analyze_dir):
            build_overview(analyze_dir)
        else:
            log(flog, 'skip build overview progress ...')

        # Step 4, merge tifs
        # for training, as virtual dataset is efficient
        #merge_as_virtual_dataset(analyze_dir, config.merged_analyze_file)
        tif_count, tif_file = tiff_count(analyze_dir)
        print tif_count, tif_file
        if tif_count > 1:
            if not os.path.exists(config.merged_analyze_file):
                merge(analyze_dir, config.merged_analyze_file)
                build_file_overview(config.merged_analyze_file)
            else:
                log(flog, 'skip merge and build overview progress ...')
        else:
            config.merged_analyze_file = tif_file
            log(flog, 'no need to merge only one file: %s' % (config.merged_analyze_file))
        
        # Step 5, cut into tiles
        # for analyze tiles
        if not os.path.exists(config.analyze_tiles_dir):
            if config.image_type == 'tif':
                tiler_tif(config.merged_analyze_file, config.analyze_tiles_dir, int(config.tile_level), config.tile_extent)
            else:
                tiler_png(config.merged_analyze_file, config.analyze_tiles_dir, str(config.tile_level))
        
            # Step 6, rm invalid training tiles
            rm_invalid_tiles(config.analyze_tiles_dir, config.image_type, config.mode)
        else:
            log(flog, 'skip tiler tiles and remove invalid tiles progress ...')
    
        if config.mode == 'predict':
            create_overlap_predict_tiles(config.analyze_tiles_dir)
            write_predict_txt(config.analyze_tiles_dir, config.predict_txt, config.image_type)
    else:
        log(flog, 'skip analyze progress ...')

    if config.process_visualize and not os.path.exists(config.visualize_tiles_dir):
        # Step 2
        if len(config.visualize_bands) == 0:
            # use all bands for visualize
            log(flog, 'use all bands for visualize')
            visualize_dir = projected_dir
        else:
            if not os.path.exists(config.visualize_tifs_dir):
                fetch_bands(projected_dir, config.visualize_tifs_dir, config.visualize_bands, 'visualize', config.image_type)
            else:
                log(flog, 'skip fetch bands progress ...')
            visualize_dir = config.visualize_tifs_dir
        # Step 3
        if need_build_overview(visualize_dir):
            build_overview(visualize_dir)
        else:
            log(flog, 'skip build overview progress ...')
        
        # Step 4 for visualize, better do really merge
        tif_count, tif_file = tiff_count(visualize_dir)
        if tif_count > 1:
            if not os.path.exists(config.merged_visualize_file):
                merge(visualize_dir, config.merged_visualize_file)
                build_file_overview(config.merged_visualize_file)
            else:
                log(flog, 'skip merge and build overview progress ...')
        else:
            config.merged_visualize_file = tif_file
        
        # Step 5 for visualize tiles
        if not os.path.exists(config.visualize_tiles_dir):
            tiler_png(config.merged_visualize_file, config.visualize_tiles_dir, str(config.visualize_level))
        else:
            log(flog, 'skip tiler visualize tiles progress ...')

    
    ######### vector labels ###########
    if not os.path.exists(config.labels_dir):
        if not os.path.exists(config.overlay_tiles_dir):
            tiler_overlay()
        else:
            log(flog, 'skip tiler_overlay progress ...')
        if not os.path.exists(config.valid_overlay_tiles_dir):
            copy_labels()
        else:
            log(flog, 'skip copy_labels progress ...')
        if not os.path.exists(config.labels_dir):
            color2gray()
        else:
            log(flog, 'skip color2gray progress ...')
    else:
        log(flog, 'skip tiler vector tiles, copy labels and color2gray progress ...')
    ######## split train test ##########
    split_train_test()

    ######## deploy ####################
    if len(config.deploy) >= 1:
        deploy()

        ######## calculate weights ##########
        calculate_weights()
    else:
        log(flog, 'skip deploy and calculating weights progress ...')
    log(flog, 'finished!')


