# -*- coding: utf-8 -*-
from osgeo import gdal
from osgeo import osr
from osgeo import ogr
gdal.UseExceptions()
from gdal2tiles import GDAL2Tiles
import gdal_merge
import mapnik

import os
import shutil
import sys
import math
import numpy
import random
import datetime
from PIL import Image
import multiprocessing 
from progressbar import *
from skimage import io
import json
import globalmaptiles
import subprocess
from vector_layer import VectorLayer
from band_math import BandMath
from config import DeepPlanetConfig

import warnings
warnings.filterwarnings("ignore")

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
    return (file_extension == '.tif' or file_extension == '.TIF')

def is_png(file):
    filename, file_extension = os.path.splitext(file)
    return (file_extension == '.png' or file_extension == '.PNG')

def tiff_count(src_dir):
    files = os.listdir(src_dir)
    count = 0
    tif_file = ''
    for file in files:
        file_path = os.path.join(src_dir, file)
        if is_tiff(file_path):
            count = count + 1
            tif_file = file_path
    return (count, tif_file)

def get_epsg(src_dir):
    log(flog, 'fetch epsg code from %s'% src_dir)

    files = os.listdir(src_dir)
    epsg_code = None
    for file in files:
        if is_tiff(file):
            file_path = os.path.join(src_dir, file)
            try:
                dataset = gdal.Open(str(file_path), gdal.GA_ReadOnly)

                srs = osr.SpatialReference()
                srs.ImportFromESRI([dataset.GetProjection()])

                srs.AutoIdentifyEPSG()
            except Exception as identifier:
                log(flog, 'exception %s' % (identifier))
                return None
            
            if epsg_code is None:
                epsg_code = srs.GetAuthorityCode(None)
                log(flog, 'find epsg code %s' % str(epsg_code))
            else:
                if epsg_code != srs.GetAuthorityCode(None):
                    log(flog, '%s contains mulity SpatialReference %s' % (file_path, str(srs.GetAuthorityCode(None))))
                    return None
    return epsg_code


def convert_nodata(src_dir):
    log(flog, 'convert nodata from %s to %s' % (src_dir, config.samenodata_dir))
    if not os.path.exists(config.samenodata_dir):
        os.mkdir(config.samenodata_dir)

    files = os.listdir(src_dir)
    for file in files:
        if is_tiff(file):
            file_path = os.path.join(src_dir, file)

            # check nodata value
            dataset = gdal.Open(str(file_path), gdal.GA_ReadOnly)
            band_num = dataset.RasterCount
            for i in range(1, band_num + 1):
                band = dataset.GetRasterBand(i)
                if band.GetNoDataValue() is None:
                    log(flog, 'warning, source tifs nodata not set, treat 0 as nodata!')
                    break

            new_file_path = os.path.join(config.samenodata_dir, file)
            command = '%s -dstnodata %d %s %s' % (os.path.join(bundle_dir, 'gdalwarp'), config.nodata,file_path, new_file_path)
            print command
            if not execute_system_command(command):
                return False
    return True

def get_bands(src_dir):
    log(flog, 'fetch band information from %s'% src_dir)
    files = os.listdir(src_dir)
    band_num = None
    for file in files:
        if is_tiff(file):
            file_path = os.path.join(src_dir, file)
            dataset = gdal.Open(str(file_path), gdal.GA_ReadOnly)
            if band_num is None:
                band_num = dataset.RasterCount
                log(flog, 'find #bands %s' % str(band_num))
            else:
                if band_num != dataset.RasterCount:
                    log(flog, '#bands must keep same in %s, old %d, new %d' % (src_dir, band_num, dataset.RasterCount))
                    return None
    return band_num

def reproj(src_dir, src_proj, dest_dir):
    log(flog, 'projecting files from %s with projection %s to %s ...' % (src_dir, src_proj, dest_dir))
    create_directory_if_not_exist(dest_dir)

    files = os.listdir(src_dir)
    for file in files:
        file_path = os.path.join(src_dir, file)
        projected_file_path = os.path.join(dest_dir, file)

        if not is_tiff(file):
		    #print 'unsupport file ', file
		    continue

        command = '%s -s_srs EPSG:%s -t_srs EPSG:3857 -r bilinear %s %s' % (os.path.join(bundle_dir, 'gdalwarp'), src_proj, file_path, projected_file_path)
        print(command)
        if not execute_system_command(command):
            log(flog, 'command %s fail!' % command)
            return False
    return True


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
            command = '%s -ot UInt16 %s %s %s' % (os.path.join(bundle_dir, 'gdal_translate'), file_path, fetched_file_path, band_str)
        else:
            # visualize or analyze but using png
            command = '%s -scale -ot Byte -co COMPRESS=JPEG -co JPEG_QUALITY=100 %s %s %s' % (os.path.join(bundle_dir, 'gdal_translate'), file_path, fetched_file_path, band_str)
        print command
        if not execute_system_command(command):
            log(flog, 'command %s fail' % command)
            return False
    return True

def execute_system_command(command):
    try:
        retcode = subprocess.call(command, env=env, shell=True)
        if retcode < 0:
            print("Child was terminated by signal", -retcode)
            return False
        else:
            return True
    except OSError as e:
        print("Execution failed:", e)
        return False

def build_overview(work_dir):
    log(flog, 'building overview for files under %s' % work_dir)

    for parent, dirnames, filenames in os.walk(work_dir):
	    for file in filenames:
		    if not is_tiff(file):
			    print 'unsupport file ', file
			    continue

		    command = "%s -r gauss -ro %s 2 4 8 16" % (os.path.join(bundle_dir, 'gdaladdo'), os.path.join(parent, file))
		    print command
		    status = execute_system_command(command)
            if not status:
                return False
    return True


def build_file_overview(file):
    log(flog, 'building overview for %s' % (file))

    command = "%s -r gauss -ro %s 2 4 8 16" % (os.path.join(bundle_dir, 'gdaladdo'), file)
    print command
    return execute_system_command(command)


def merge_as_virtual_dataset(src_dir, merged_file):
    log(flog, 'merging virtual dataset from files under %s to %s ...' % (src_dir, merged_file))

    command = '%s %s %s/*.tif' % (os.path.join(bundle_dir, 'gdalbuildvrt'), merged_file, src_dir)
    print command
    return execute_system_command(command)

def merge(src_dir, merged_file):
    log(flog, 'merging files under %s to %s ...' % (src_dir, merged_file))

    command = 'gdal_merge.py -o %s %s/*.tif' % (merged_file, src_dir)
    print command
    gdal_merge.main(command.split())
    return True

def get_raster_extent(src):
    dataset = gdal.Open(str(src), gdal.GA_ReadOnly)
    if dataset is None:
        print('dataset is null', src)
        return None

    geotransform = dataset.GetGeoTransform()
    if not geotransform is None:
        map_minx = geotransform[0]
        map_maxy = geotransform[3]
        map_maxx = map_minx + geotransform[1] * dataset.RasterXSize
        map_miny = map_maxy + geotransform[5] * dataset.RasterYSize
    else:
        print('no geotransform find', src)
        return None
    log(flog, 'raster extent %f, %f, %f, %f' % (map_minx, map_miny, map_maxx, map_maxy))
    return (map_minx, map_miny, map_maxx, map_maxy)


def tiler_tif(src, out): 
    log(flog, 'tilering level %s, from %s to %s ...' % (config.tile_level, src, out))
    create_directory_if_not_exist(out)
    
    mercator = globalmaptiles.GlobalMercator()
    tz = int(config.tile_level)
    tminx, tminy = mercator.MetersToTile(raster_extent[0], raster_extent[1], tz)
    tmaxx, tmaxy = mercator.MetersToTile(raster_extent[2], raster_extent[3], tz)

    if config.mode == "train":
        # extent tile index extent for overlap, otherwise, the tiles will not cover whole extent
        overlap_perent = float(config.overlap) / float(config.image_dim)

        original_count_x = tmaxx - tminx + 1
        original_count_y = tmaxy - tminy + 1

        new_count_x = int(math.ceil(original_count_x / (1 - overlap_perent)))
        new_count_y = int(math.ceil(original_count_y / (1 - overlap_perent)))

        print('x from %d - %d' % (tminx, tmaxx))
        tmaxx = tminx + new_count_x - 1
        print('to %d - %d' % (tminx, tmaxx))
        
        print('y from %d - %d' % (tminy, tmaxy))
        tmaxy = tminy + new_count_y - 1
        print('to %d - %d' % (tminy, tmaxy))


    total_tiles = (tmaxx - tminx + 1) * (tmaxy - tminy + 1)
    # progress bar
    widgets = [Bar('>'), ' ', Percentage(), ' ', Timer(), ' ', ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=total_tiles).start()
    count = 0
    for ty in range(tminy, tmaxy + 1):
        for tx in range(tminx, tmaxx + 1):
            count = count + 1
            pbar.update(count)

            ymax = 1 << tz
            invert_ty = ymax - ty - 1
            # ty for TMS bottom origin, invert_ty Use top origin tile scheme (like OSM or GMaps)
            tilepath = os.path.join(out, "%d_%d_%d.tif" % (tz, tx, invert_ty))

            (minx, miny, maxx, maxy) = mercator.TileBounds(tx, ty, tz)

            if config.mode == "train":
                tile_size = config.image_dim
                # overlap alone horizontal
                offsetx = mercator.Resolution(tz) * config.overlap * (tx - tminx)
                minx = minx - offsetx
                maxx = maxx - offsetx
                
                # overlap along vertical
                offsety = mercator.Resolution(tz) * config.overlap * (ty - tminy)
                miny = miny + offsety
                maxy = maxy + offsety
            else:
                # predict mode, extent on left and top
                minx = minx - mercator.Resolution(tz) * config.overlap
                maxy = maxy + mercator.Resolution(tz) * config.overlap
                tile_size = config.image_dim + config.overlap

            if not os.path.exists(tilepath):
                command = "%s -of GTiff -te %s %s %s %s -ts %d %d -r near -multi -q %s %s" % (os.path.join(bundle_dir, 'gdalwarp'), format(minx, '.10f'), format(miny, '.10f'), format(maxx, '.10f'), format(maxy, '.10f'), tile_size, tile_size, src, tilepath)
            
                #print command
                status  = execute_system_command(command)
                if not status:
                    log('process %s fail!' % (tilepath))
                    # not break the whole time consuming process !!!
                    #return False
    return True
                

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
    command = "gdal2tiles.py -s epsg:3857 -a %s -e -w none -z %s %s %s" % (str(config.nodata), level, src, out)
    print command
    argv = gdal.GeneralCmdLineProcessor(command.split())
    gdal2tiles = GDAL2Tiles(argv[1:])
    gdal2tiles.process()

    level_arr = level.split('-')
    if len(level_arr) == 1:
        flatten_google_dir(out, int(level_arr[0]))
    else:
        for i in range(int(level_arr[0]), int(level_arr[1]) + 1):
            flatten_google_dir(out, i)
    return True


def add_extra_bands():
    tiles = os.listdir(config.analyze_tiles_dir)
    output_dir = config.analyze_tiles_dir + '_extra'
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    
    log(flog, 'adding extra bands, from %s to %s ...' % (config.analyze_tiles_dir, output_dir))

    band_math_op = BandMath()
    for tile in tiles:
        if not is_tiff(tile):
            print 'unsupport file ', tile
            continue

        tile_file = os.path.join(config.analyze_tiles_dir, tile)
        new_tile_file = os.path.join(output_dir, tile)

        dataset = gdal.Open(tile_file)
        newdataset = gdal.GetDriverByName('MEM').CreateCopy(' ', dataset, 0)
        
        for band_method in config.extra_bands:
            band_list = []
            for iband in config.extra_bands[band_method]:
                band_list.append(dataset.GetRasterBand(iband).ReadAsArray().astype(numpy.float16))
            newband = band_math_op.compute(band_method, band_list)

            newdataset.AddBand(gdal.GDT_UInt16)
            newdataset.GetRasterBand(newdataset.RasterCount).WriteArray(newband)

        dst_ds = gdal.GetDriverByName('GTiff').CreateCopy(new_tile_file, newdataset, 0)
        del dst_ds

    config.analyze_tiles_dir = output_dir


def proces_analyze_img(image_file):
    if is_png(image_file):
        img = io.imread(image_file)
        for x in range(0, config.image_dim):
            for y in range(0, config.image_dim):
                if img[x][y][0] == dst_nodata and img[x][y][1] == dst_nodata and img[x][y][2] == dst_nodata:
                    os.unlink(image_file)
                    return 

def proces_predict_img(image_file):
    if is_png(image_file):
        img = io.imread(image_file)
        for x in range(0, config.image_dim):
            for y in range(0, config.image_dim):
                if img[x][y][0] != dst_nodata or img[x][y][1] != dst_nodata or img[x][y][2] != dst_nodata:
                    return 
        os.unlink(image_file)


def proces_tif(tif_file):
    if not is_tiff(tif_file):
        os.unlink(tif_file)
        return

    try:
        src_ds = gdal.Open(str(tif_file))
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
                if dataraster[r][c] == dst_nodata or dataraster[r][c] is None:
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
        src_ds = gdal.Open(str(tif_file))
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


def rm_cloud_tiles():
    log(flog, 'remove cloud tiles ...')
    if not os.path.exists(config.cloud_tiles_dir):
        os.mkdir(config.cloud_tiles_dir)
    
    cloud_file = config.cloud_file
    clouddata = VectorLayer()
    if not clouddata.open(cloud_file, 0, 'ESRI Shapefile'):
        log(flog, 'open cloud file fail!')
        return
    
    mercator = globalmaptiles.GlobalMercator()
    files = os.listdir(config.analyze_tiles_dir)
    tz = int(config.tile_level)
    ymax = 1 << tz
    for i in range(len(files)):
        if not is_tiff(files[i]):
            continue
        filename = files[i].split('/')[-1]
        items = filename.split('.')[0].split('_')
        z = int(items[0])
        tx = int(items[1])
        ty = int(items[2])
        invert_ty = ymax - ty - 1
        bounds = mercator.TileBounds(tx, invert_ty, tz)
        #print(bounds)

        layer = clouddata.spatialQuery(bounds)
        if layer.GetFeatureCount() > 0:
            old_file = os.path.join(config.analyze_tiles_dir, files[i])
            new_file = os.path.join(config.cloud_tiles_dir, files[i])
            print('move cloud file from %s to %s' % (old_file, new_file))
            shutil.move(old_file, new_file)


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
            # mode == 'predict'
            for i, _ in enumerate(pool.imap_unordered(proces_predict_img, files), 1):
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

def create_overlap_predict_tiles(work_dir, new_dir, overlap):
    if not os.path.exists(new_dir):
        os.mkdir(new_dir)

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

        left = '%d_%d_%d.png' % (z, x - 1, y)
        top = '%d_%d_%d.png' % (z, x, y - 1)
        left_top = '%d_%d_%d.png' % (z, x - 1, y - 1)

        left_file = os.path.join(work_dir, left)
        top_file = os.path.join(work_dir, top)
        left_top_file = os.path.join(work_dir, left_top)

        if os.path.exists(left_file):
            extent_left = True
        else:
            extent_left = False
        if os.path.exists(top_file):
            extent_top = True
        else:
            extent_top = False
        
        extent_left_and_top_corner = False
        if extent_left and extent_top:
            if not os.path.exists(left_top_file):
                print('Warning: not exist left top file %s' % (left_top_file))  
            else:
                extent_left_and_top_corner = True
        width = config.image_dim + overlap
        height = config.image_dim + overlap

        #print('extent image %s to %d %d' % (file, width, height))
        new_im = Image.new('RGB', (width, height))
        center_image = Image.open(os.path.join(work_dir, file))
        new_im.paste(center_image, (overlap, overlap))

        if extent_left:
            deltx = -(config.image_dim - overlap)
            delty = overlap
            print('paste image %s at %d %d' % (left_file, deltx, delty))
            left_image = Image.open(left_file)
            new_im.paste(left_image, (deltx, delty))
        if extent_top:
            deltx = overlap
            delty = -(config.image_dim - overlap)
            print('paste image %s at %d %d' % (top_file, deltx, delty))
            top_image = Image.open(top_file)
            new_im.paste(top_image, (deltx, delty))

        if extent_left and extent_top and extent_left_and_top_corner:
            deltx = -(config.image_dim - overlap)
            delty = -(config.image_dim - overlap)
            print('paste image %s at %d %d' % (left_top_file, deltx, delty))
            left_top_image = Image.open(left_top_file)
            new_im.paste(left_top_image, (deltx, delty))

        new_im_file = os.path.join(new_dir, '%d_%d_%d.png' % (z, x, y))
        print('saving to %s' % (new_im_file))
        new_im.save(new_im_file, "PNG")


def write_predict_txt(work_dir, file_path, image_type):
    image_size = config.image_dim + config.overlap

    with open(file_path, 'w') as f:
        files = os.listdir(work_dir)
        for file in files:
            file_path = os.path.join(work_dir, file)
            if image_type == 'tif':
                if is_tiff(file_path):
                    f.write('%s %s\n' % (file_path, file_path))
            else:
                if is_png(file_path):
                    img = io.imread(file_path)
                    if (img.shape[0] == image_size and img.shape[1] == image_size):
                        f.write('%s %s\n' % (file_path, file_path))
                    else:
                        print img.shape


def grid2image():
    log(flog, 'generate image from %s into %s ...' % (config.overlay_tiles_dir, config.labels_dir))
    if not os.path.exists(config.labels_dir):
        os.mkdir(config.labels_dir)
        
    train_files = os.listdir(config.analyze_tiles_dir)

    # progress bar
    widgets = [Bar('>'), ' ', Percentage(), ' ', Timer(), ' ', ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=len(train_files)).start()

    nthreads = multiprocessing.cpu_count() * 2
    pool = multiprocessing.Pool(processes=nthreads)

    for i, _ in enumerate(pool.imap_unordered(proces_label_img, train_files), 1):
        pbar.update(i)

    pool.close()
    pool.join()
    pbar.finish()


def create_utfgrids():
    if not os.path.exists(config.overlay_tiles_dir):
        os.mkdir(config.overlay_tiles_dir)
    
    for label_dir_name in config.label_dirs:
        label_dir = os.path.join(config.overlay_tiles_dir, label_dir_name)
        if not os.path.exists(label_dir):
            os.mkdir(label_dir)
        print('generating grids to %s' % label_dir)

        mercator = globalmaptiles.GlobalMercator()
        # map
        m = mapnik.Map(config.image_dim, config.image_dim)

        # Since grids are `rendered` they need a style
        s = mapnik.Style()
        r = mapnik.Rule()

        polygon_symbolizer = mapnik.PolygonSymbolizer()
        polygon_symbolizer.fill = mapnik.Color('#f2eff9')
        r.symbols.append(polygon_symbolizer)

        s.rules.append(r)
        m.append_style('My Style',s)

        shppath = os.path.join(config.overlay_dir, label_dir_name + '.shp')
        ds = ogr.Open(shppath)
        layer = ds.GetLayer(0)
        bbox = layer.GetExtent()

        minx = bbox[0]
        miny = bbox[2]
        maxx = bbox[1]
        maxy = bbox[3]
            
        print('create layer', label_dir_name)
        mlayer = mapnik.Layer(str(label_dir_name))
        mlayer.datasource = mapnik.Shapefile(file=shppath)
        mlayer.styles.append('My Style')

        # check field
        all_fields = mlayer.datasource.fields()
        find_field = False
        for fd in all_fields:
            if fd == config.class_field:
                find_field = True
        if not find_field:
            print('not exist class field', config.class_field)
            return

        m.layers.append(mlayer)

        print(minx, miny, maxx, maxy)

        tz = int(config.tile_level)
        print " * Processing Zoom Level %s" % tz

        tminx, tminy = mercator.MetersToTile(minx, miny, tz)
        tmaxx, tmaxy = mercator.MetersToTile(maxx, maxy, tz)
        total_tiles = (tmaxx - tminx + 1) * (tmaxy - tminy + 1)
        # progress bar
        widgets = [Bar('>'), ' ', Percentage(), ' ', Timer(), ' ', ETA()]
        pbar = ProgressBar(widgets=widgets, maxval=total_tiles).start()
        count = 0
        for ty in range(tminy, tmaxy+1):
            for tx in range(tminx, tmaxx+1):
                count = count + 1
                pbar.update(count)

                ymax = 1 << tz
                invert_ty = ymax - ty - 1

                tilefilename = os.path.join(label_dir, "%d_%d_%d.json" % (tz, tx, invert_ty))
                tilebounds = mercator.TileBounds(tx, ty, tz)

                box = mapnik.Box2d(*tilebounds)
                m.zoom_to_box(box)
                grid = mapnik.Grid(m.width, m.height)
                mapnik.render_layer(m, grid, layer=0, fields=[str(config.class_field)])
                utfgrid = grid.encode('utf', resolution=1)
                with open(tilefilename, 'w') as file:
                    file.write(json.dumps(utfgrid))


def decode_id(codepoint):
    codepoint = ord(codepoint)
    if codepoint >= 93:
        codepoint-=1
    if codepoint >= 35:
        codepoint-=1
    codepoint -= 32
    return codepoint


def resolve(grid, row, col):
    """ Resolve the attributes for a given pixel in a grid.
    """
    row = grid['grid'][row]
    utf_val = row[col]
    codepoint = decode_id(utf_val)
    key = grid['keys'][codepoint]
    return grid['data'].get(key)  


def proces_label_img(tile):
    # check file type
    filename, extension = os.path.splitext(tile)
    if extension != ('.%s' % (config.image_type)):
        print('not %s file: %s' % (config.image_type, tile))
        return

    new_tile_file = os.path.join(config.labels_dir, filename + '.png')
    img = numpy.zeros((config.image_dim, config.image_dim))
    # initial set to background
    img = img + config.background_class
    img = img.astype(int)

    is_img_empty = True
    for label_dir_name in config.label_dirs:
        tile_file = os.path.join(config.overlay_tiles_dir, label_dir_name, filename + '.json')
        if not os.path.exists(tile_file):
            continue

        # load grids
        with open(tile_file) as json_data:
            try:
                grid = json.load(json_data)
            except Exception as identifier:
                log(flog, 'open %s fail!' % (tile_file))
                continue
    
        for row in range(0, config.image_dim):
            for col in range(0, config.image_dim):
                # only try to update if this pixel is background 
                if img[row][col] != config.background_class:
                    continue

                key_val = resolve(grid, row, col)
                if key_val is not None:
                    val = key_val[config.class_field]
                    for k in range(0, len(config.class_names)):
                        if val == config.class_names[k]:
                            # update pixel label
                            img[row][col] = k
                            is_img_empty = False
                            break
    
    if not is_img_empty:
        io.imsave(new_tile_file, img)


def split_train_test(train_dir, label_dir, train_file, test_file):
    log(flog, 'split train test from %s | %s ...' % (train_dir, label_dir))
    
    ftrain = open(train_file, 'w')
    ftest = open(test_file, 'w')

    tiles = os.listdir(train_dir)
    random.shuffle(tiles)

    total_files = len(tiles)
    cut_line = int(total_files * 0.8)

    print('#total tiles: %d, #training tiles: %d, #testing tiles: %d' % (total_files, cut_line, total_files - cut_line))

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

    images = []
    train_txt = '%s/train.txt' % config.deploy_dir
    test_txt = '%s/test.txt' % config.deploy_dir
    with open(train_txt, 'r') as f:
        for line in f:
            items = line.strip().split()
            images.append(items[1])
    with open(test_txt, 'r') as f:
        for line in f:
            items = line.strip().split()
            images.append(items[1])

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

        class_in_file = []
        for i in range(0, nclass):
            class_in_file.append(False)

        img = io.imread(img)
        for i in range(0, config.image_dim):
            for j in range(0, config.image_dim): 
                if config.ignore_background and img[i][j] == nclass:
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
        # f(class) = frequency(class) / (image_count(class) * config.image_dim * config.image_dim)
        freq = float(class_info[i]['pixels']) / float(class_info[i]['files'] * config.image_dim * config.image_dim)
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


def deploy_stack():
    log(flog, 'deploy dataset %s to %s ...' % (str(config.deploy), config.deploy_dir))
    if len(config.deploy) < 2:
        print('Error, deploy mode set to stack really need two or more deploy datasets')
        return

    if not os.path.exists(config.deploy_dir):
        os.mkdir(config.deploy_dir) 
    if not os.path.exists(config.stack_dir):
        os.mkdir(config.stack_dir)

    # stack images
    items = config.analyze_tiles_dir.split('/')
    analyze_tiles_dir_name = items[len(items) - 1]

    tiles_dir = '%s/%s/%s' % (config.project_dir, config.deploy[0], analyze_tiles_dir_name)
    print('tiles_dir', tiles_dir)
    tiles_list = os.listdir(tiles_dir)
    for tile in tiles_list:
        tile_file = os.path.join(tiles_dir, tile)
        if is_tiff(tile_file):
            has_corres_file = True
            tile_str = tile_file
            for i in range(1, len(config.deploy)):
                corres_tile = '%s/%s/%s/%s' % (config.project_dir, config.deploy[i], analyze_tiles_dir_name, tile)
                if not os.path.exists(corres_tile):
                    has_corres_file = False
                tile_str = '%s %s' % (tile_str, corres_tile)

            if has_corres_file:
                # stack
                output_file = os.path.join(config.stack_dir, tile)
                #delete if already exist
                if os.path.exists(output_file):
                    os.unlink(output_file)
                
                command = 'gdal_merge.py -separate %s -o %s' % (tile_str, output_file)
                gdal_merge.main(command.split())


def deploy_predict_append():
    log(flog, 'deploy predict dataset %s to %s ...' % (str(config.deploy), config.deploy_dir))

    if not os.path.exists(config.deploy_dir):
        #shutil.rmtree(config.deploy_dir)
        os.mkdir(config.deploy_dir) 

    predict_dir = config.deploy_dir
    predict_txt = '%s/predict.txt' % predict_dir
    fpredict = open(predict_txt, 'w')

    for ele in config.deploy:
        print 'process data set ', ele
        # test file
        test_file = '%s/%s/test.txt' % (config.project_dir, ele)
        with open(test_file, 'r') as f:
            for line in f:
                fpredict.write(line)
    fpredict.close()


def deploy():
    log(flog, 'deploy dataset %s to %s ...' % (str(config.deploy), config.deploy_dir))

    if not os.path.exists(config.deploy_dir):
        #shutil.rmtree(config.deploy_dir)
        os.mkdir(config.deploy_dir) 

    training_dir = config.deploy_dir

    train_txt = '%s/train.txt' % training_dir
    test_txt = '%s/test.txt' % training_dir

    ftrain = open(train_txt, 'w')
    ftest = open(test_txt, 'w')

    for ele in config.deploy:
        print 'process data set ', ele
        # train file
        train_file = '%s/%s/train.txt' % (config.project_dir, ele)
        with open(train_file, 'r') as f:
            for line in f:
                ftrain.write(line)
    
        # test file
        test_file = '%s/%s/test.txt' % (config.project_dir, ele)
        with open(test_file, 'r') as f:
            for line in f:
                ftest.write(line)

    ftrain.close()
    ftest.close()


def compute_mean():
    train_txt = '%s/train.txt' % config.deploy_dir
    test_txt = '%s/test.txt' % config.deploy_dir

    data_sum = []
    for i in range(0, len(config.analyze_bands)):
        data_sum.append(0.0)

    cnt = 0
    with open(train_txt, 'r') as f:
        for line in f:
            file_path = line.strip().split()[0]
            dataset = gdal.Open(str(file_path), gdal.GA_ReadOnly)
            band_num = dataset.RasterCount
            for i in range(1, band_num + 1):
                band = dataset.GetRasterBand(i)
                data = band.ReadAsArray()
                data_sum[i - 1] = numpy.average(data) + data_sum[i - 1]
            cnt = cnt + 1

    with open(test_txt, 'r') as f:
        for line in f:
            file_path = line.strip().split()[0]
            dataset = gdal.Open(str(file_path), gdal.GA_ReadOnly)
            band_num = dataset.RasterCount
            for i in range(1, band_num + 1):
                band = dataset.GetRasterBand(i)
                data = band.ReadAsArray()
                data_sum[i - 1] = numpy.average(data) + data_sum[i - 1]
            cnt = cnt + 1

    for i in range(0, len(data_sum)):
        data_sum[i] = float(data_sum[i]) / float(cnt)

    print data_sum
    with open(config.mean_file, 'w') as f:
        for i in range(0, len(data_sum)):
            if i != 0:
                f.write('\t')
            f.write('%f' % data_sum[i])


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


def generate_pages(type):
    page_template = '''
    <!DOCTYPE html>
    <html>
    <head>
    <title>{title}</title>
    <meta charset="utf-8" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.0.3/dist/leaflet.css" />
	    <script src="https://unpkg.com/leaflet@1.0.3/dist/leaflet.js"></script>
        <script src="js/jquery.min.js"></script>
    </head>

    <body style="margin: 0; padding:0; width: 100%; height: 100%; position: absolute; background-color: #9d9d9d">
    <div id="map" style="width: 100%; height: 100%; position: absolute;"></div>
    <script>
        var center = L.Projection.SphericalMercator.unproject(L.point({x}, {y}))
        var mymap = L.map('map').setView(center, {level});

        L.tileLayer('{osm_url}').addTo(mymap);
        L.tileLayer('{layer_url}').addTo(mymap);

    </script>
    </body>
    </html>
    '''
    cx = (raster_extent[0] + raster_extent[2]) / 2.0
    cy = (raster_extent[1] + raster_extent[3]) / 2.0
    
    if type == 'visualize':
        log(flog, 'generate tile viewer page %s serving %s' % (config.visualize_page, config.visualize_tiles_dir))
        visualize_str = page_template.format(title=config.data_name, x=cx, y=cy, 
        level=config.tile_level, osm_url='http://a.tile.osm.org/{z}/{x}/{y}.png',
        layer_url='/%s/{z}_{x}_{y}.png' % (config.visualize_tiles_dir)
        )
        with open(config.visualize_page, 'w') as f:
            f.write(visualize_str)

    if type == 'analyze' and config.mode == 'train':
        log(flog, 'generate tile viewer page %s serving %s' % (config.label_page, config.visualize_tiles_dir))

        label_str = page_template.format(title=config.data_name, x=cx, y=cy, 
        level=config.tile_level, osm_url='http://a.tile.osm.org/{z}/{x}/{y}.png',
        layer_url='/%s/{z}_{x}_{y}.png' % (config.labels_dir)
        )
        with open(config.label_page, 'w') as f:
            f.write(label_str)


if __name__=='__main__': 
    # Parse command line options
    if len(sys.argv) < 2:
        print('need config file!!!\n')
        sys.exit()
    
    config_cmd = parseOptions(sys.argv[1])
    # Global configure object
    config = DeepPlanetConfig()
    if not config.Initialize(config_cmd):
        print('initialize fail! exist...')
        sys.exit()

    # Open log file
    flog = open(config.log_file, 'w')
    log(flog, 'tiler raster begins, this may take a while, go to drink a cup of coffee ...')

    # for pyinstaller
    env = dict(os.environ)  # make a copy of the environment
    if getattr(sys, 'frozen', False):
        # we are running in a bundle
        bundle_dir = sys._MEIPASS
        env['GDAL_DATA'] = os.path.join(sys._MEIPASS, 'share/gdal/1.11/')
    else:
        # we are running in a normal Python environment
        bundle_dir = os.path.dirname(os.path.abspath(__file__))

    # get information from source tifs
    ## get projection from source tifs
    src_projection = get_epsg(config.src_tifs)
    if src_projection is None:
        log(flog, 'source tifs has no projection find! exist ...')
        sys.exit()

    ## convert nodata value from source tifs
    if not os.path.exists(config.samenodata_dir):
        status = convert_nodata(config.src_tifs)
        if not status:
            log(flog, 'convert nodata fail, exit ...')
            sys.exit()
    
    # because source nodata is always 0!!!
    dst_nodata = 0

    # change working directory
    config.src_tifs = config.samenodata_dir

    ## get bands info
    bands = get_bands(config.src_tifs)
    print('src projection: %s, #bands: %d' % (src_projection, bands))

    # Reprojection if needed 
    if src_projection != '3857':
        if not os.path.exists(config.tifs_3857):
            if not reproj(config.src_tifs, src_projection, config.tifs_3857):
                log(flog, 'reprojection fail, exit ...')
                sys.exit()
        else:
            log(flog, 'skip reprojtion progress ...')
        projected_dir = config.tifs_3857
    else:
        log(flog, 'no projection progress need.')
        projected_dir = config.src_tifs
    
    if config.process_analyze:
        # Fetch bands for analyze
        if len(config.analyze_bands) == 0:
            ## use all bands for analyze
            log(flog, 'use all bands for analyze')
            for i in range(0, bands):
                config.analyze_bands.append(i + 1)
        # check band validation
        for bd in config.analyze_bands:
            if bd > bands:
                print('band out of range! %d exceed %d' % (bd, bands))
                sys.exit()

        # fetch bands and do necessary datatype convation
        if not os.path.exists(config.analyze_tifs_dir):
            if not fetch_bands(projected_dir, config.analyze_tifs_dir, config.analyze_bands, 'analyze', config.image_type):
                log(flog, 'fetch band fail, exit ...')
                sys.exit()
        else:
            log(flog, 'skip fetch bands progress ...')
        analyze_dir = config.analyze_tifs_dir
        
        # Build overview for analyze datas
        if need_build_overview(analyze_dir):
            if not build_overview(analyze_dir):
                log(flog, 'build overview fail, exit ...')
                sys.exit()
        else:
            log(flog, 'skip build overview progress ...')

        # Merge tifs
        ## for training, as virtual dataset is efficient
        tif_count, tif_file = tiff_count(analyze_dir)
        print tif_count, tif_file
        if tif_count > 1:
            if not os.path.exists(config.merged_analyze_file):
                if config.virtual_dataset:
                    if not merge_as_virtual_dataset(analyze_dir, config.merged_analyze_file):
                        log(flog, 'merge virtual dataset fail, exit ...')
                        sys.exit()
                else:
                    if not merge(analyze_dir, config.merged_analyze_file):
                        log(flog, 'merge fail, exit ...')
                        sys.exit()
                    if not build_file_overview(config.merged_analyze_file):
                        log(flog, 'build file overview fail, exit ...')
                        sys.exit()
            else:
                log(flog, 'skip merge and build overview progress ...')
        else:
            config.merged_analyze_file = tif_file
            log(flog, 'no need to merge only one file: %s' % (config.merged_analyze_file))
        
        # Cut into tiles
        ## get extent
        raster_extent = get_raster_extent(config.merged_analyze_file)
        if raster_extent is None:
            log(flog, 'get raster extent fail, exist ...')
            sys.exit()

        ## generate html pages to visualize tiles
        generate_pages('analyze')

        ## tiler
        if not os.path.exists(config.analyze_tiles_dir):
            if config.image_type == 'tif':
                if not tiler_tif(config.merged_analyze_file, config.analyze_tiles_dir):
                    log(flog, 'tiler tif fail, exit ...')
                    sys.exit()
            else:
                if not tiler_png(config.merged_analyze_file, config.analyze_tiles_dir, str(config.tile_level)):
                    log(flog, 'tiler png fail, exit ...')
                    sys.exit()
        
            if config.rm_incomplete_tile:
                # Delete invalid training tiles
                rm_invalid_tiles(config.analyze_tiles_dir, config.image_type, config.mode)

        # remove cloud tiles
        if os.path.exists(config.cloud_file):
            rm_cloud_tiles()
        else:
            log(flog, 'skip rm clouds %s' % (config.cloud_file))

        # add extra bands if specified
        if config.extra_bands is not None:
            add_extra_bands()
    else:
        log(flog, 'skip analyze progress ...')


    if config.process_visualize:
        if len(config.visualize_bands) == 0:
            # use first 3 bands for visualize
            if bands < 3:
                print('not enough bands to visualize')
                sys.exit()
            config.visualize_bands = [1, 2, 3]
        # check band validation
        for bd in config.visualize_bands:
            if bd > bands:
                print('band out of range! %d exceed %d' % (bd, bands))
                sys.exit()
        # fetch bands and do necessary datatype convertation
        if not os.path.exists(config.visualize_tifs_dir):
            if not fetch_bands(projected_dir, config.visualize_tifs_dir, config.visualize_bands, 'visualize', config.image_type):
                log(flog, 'fetch bands fail, exit ...')
                sys.exit()
        else:
            log(flog, 'skip fetch bands progress ...')
        visualize_dir = config.visualize_tifs_dir

        # Build overview if needed
        if need_build_overview(visualize_dir):
            if not build_overview(visualize_dir):
                log(flog, 'build overview fail, exit ...')
                sys.exit()
        else:
            log(flog, 'skip build overview progress ...')
        
        # For visualize, better do really merge
        tif_count, tif_file = tiff_count(visualize_dir)
        if tif_count > 1:
            if not os.path.exists(config.merged_visualize_file):
                if config.virtual_dataset:
                    if not merge_as_virtual_dataset(visualize_dir, config.merged_visualize_file):
                        log(flog, 'merge virtual dataset fail, exit ...')
                        sys.exit()
                else:
                    if not merge(visualize_dir, config.merged_visualize_file):
                        log(flog, 'merge fail, exit ...')
                        sys.exit()
                    if not build_file_overview(config.merged_visualize_file):
                        log(flog, 'build file overview fail, exit ...')
                        sys.exit()
            else:
                log(flog, 'skip merge and build overview progress ...')
        else:
            config.merged_visualize_file = tif_file
        
        # Tiler visualize tiles
        ## get extent
        raster_extent = get_raster_extent(config.merged_visualize_file)
        if raster_extent is None:
            log(flog, 'get raster extent fail, exist ...')
            sys.exit()

        ## generate html pages to visualize tiles
        generate_pages('visualize')
        # tiler
        if not tiler_png(config.merged_visualize_file, config.visualize_tiles_dir, str(config.visualize_level)):
            log(flog, 'tiler png fail, exit ...')
            sys.exit()

    if config.mode == 'predict':
        if config.image_type == 'tif':
            # already doing overlap, just direct to the folder
            config.analyze_tiles_overlap_dir = config.analyze_tiles_dir
        else:
            create_overlap_predict_tiles(config.analyze_tiles_dir, config.analyze_tiles_overlap_dir, config.overlap)

        write_predict_txt(config.analyze_tiles_overlap_dir, config.test_txt, config.image_type)

        # consider more ... about ... merge two or more datasets?
        if (len(config.deploy) > 1):
            if config.deploy_mode == 'append':
                deploy_predict_append()
            else:
                deploy_stack()
        else:
            shutil.copy(config.test_txt, '%s/predict.txt' % config.deploy_dir)
        log(flog, 'finished!')
        sys.exit()

    ######### vector labels ###########
    if config.process_label and not os.path.exists(config.labels_dir):
        if not os.path.exists(config.overlay_tiles_dir):
            create_utfgrids()
        else:
            log(flog, 'skip tiler_overlay progress ...')

        if not os.path.exists(config.labels_dir):
            grid2image()
        else:
            log(flog, 'skip grid2image progress ...')
    else:
        log(flog, 'skip tiler vector tiles, copy labels and grid2image progress ...')

    if config.process_label and config.process_analyze:
        ######## split train test ##########
        split_train_test(config.analyze_tiles_dir, config.labels_dir, config.train_txt, config.test_txt)

    ######## deploy ####################
    if len(config.deploy) >= 1:
        if config.deploy_mode == 'append':
            deploy()
        else:
            # config.deploy_mode == 'stack'
            if not os.path.exists(config.stack_dir):
                deploy_stack()
                
            # generate train test list
            train_txt = '%s/train.txt' % config.deploy_dir
            test_txt = '%s/test.txt' % config.deploy_dir
            split_train_test(config.stack_dir, config.labels_dir, train_txt, test_txt)
        
        ######## calculate weights ##########
        if not os.path.exists(config.weight_file):
            calculate_weights()
            
        if config.substract_mean and not os.path.exists(config.mean_file):
            compute_mean()
    else:
        log(flog, 'skip deploy and calculating weights progress ...')

    log(flog, 'finished!')


