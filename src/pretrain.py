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

from config import DeepPlanetConfig
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
                    log(flog, '%s contains mulity SpatialReference' % src_dir)
                    return None
    return epsg_code


def get_nodata(src_dir):
    log(flog, 'fetch nodata value from %s'% src_dir)
    files = os.listdir(src_dir)
    nodata = None
    for file in files:
        if is_tiff(file):
            file_path = os.path.join(src_dir, file)
            dataset = gdal.Open(str(file_path), gdal.GA_ReadOnly)
            
            band = dataset.GetRasterBand(1)
            if nodata is None:
                nodata = band.GetNoDataValue()
                log(flog, 'find nodata %s' % str(nodata))
            else:
                if nodata != band.GetNoDataValue():
                    log(flog, 'nodata value must keep same in %s, old %s, new %s' % (src_dir, str(nodata), str(band.GetNoDataValue())))
                    # todo convert to keep same

    return nodata

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
        return execute_system_command(command)


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
        return execute_system_command(command)

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
		    return execute_system_command(command)


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
            if config.mode == 'train':
                tile_size = config.image_dim
            else:
                # predict mode, extent on left and top
                minx = minx - mercator.Resolution(tz) * config.overlap
                maxy = maxy + mercator.Resolution(tz) * config.overlap
                tile_size = config.image_dim + config.overlap

            command = "%s -of GTiff -te %s %s %s %s -ts %d %d -r near -multi -q %s %s" % (os.path.join(bundle_dir, 'gdalwarp'), format(minx, '.10f'), format(miny, '.10f'), format(maxx, '.10f'), format(maxy, '.10f'), tile_size, tile_size, src, tilepath)
            
            #print command
            status  = execute_system_command(command)
            if not status:
                return False
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
    if src_nodata is None:
        command = "gdal2tiles.py -s epsg:3857 -z %s %s %s" % (level, src, out)
    else:
        command = "gdal2tiles.py -s epsg:3857 -a %s -z %s %s %s" % (str(src_nodata), level, src, out)
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
            width = config.image_dim + overlap
        else:
            extent_left = False
            width = config.image_dim
        if os.path.exists(top_file):
            extent_top = True
            height = config.image_dim + overlap
        else:
            extent_top = False
            height = config.image_dim
        
        extent_left_and_top_corner = False
        if extent_left and extent_top:
            if not os.path.exists(left_top_file):
                print('Warning: not exist left top file %s' % (left_top_file))  
            else:
                extent_left_and_top_corner = True

        print('extent image %s to %d %d' % (file, width, height))
        new_im = Image.new('RGB', (width, height))
        center_image = Image.open(os.path.join(work_dir, file))
        new_im.paste(center_image, (width - config.image_dim, height - config.image_dim))

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


def copy_labels():
    log(flog, 'copy valid label from %s into %s ...' % (config.overlay_tiles_dir, config.valid_overlay_tiles_dir))

    train_dir = config.analyze_tiles_dir
    label_old_dir = config.overlay_tiles_dir
    label_new_dir = config.valid_overlay_tiles_dir

    if not os.path.exists(label_new_dir):
        print 'saving to ' + label_new_dir
        os.mkdir(label_new_dir)

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

        label_old_file_path = os.path.join(label_old_dir, '%s_%s_%s.json' % (z, x, y))
        label_new_file_path = os.path.join(label_new_dir, '%s_%s_%s.json' % (z, x, y))

        if not os.path.exists(label_old_file_path):
            print 'not exists: ', label_old_file_path
            continue

        shutil.copyfile(label_old_file_path, label_new_file_path)


def create_utfgrids():
    if not os.path.exists(config.overlay_tiles_dir):
        os.mkdir(config.overlay_tiles_dir)

    mercator = globalmaptiles.GlobalMercator()
    # map
    m = mapnik.Map(config.image_dim, config.image_dim)

    # Since grids are `rendered` they need a style
    s = mapnik.Style()
    r = mapnik.Rule()

    polygon_symbolizer = mapnik.PolygonSymbolizer()
    polygon_symbolizer.fill = mapnik.Color('#f2eff9')
    r.symbols.append(polygon_symbolizer)

    # line_symbolizer = mapnik.LineSymbolizer()
    # line_symbolizer.stroke = mapnik.Color('#f2eff9')
    # line_symbolizer.stroke_width = 0.1
    # r.symbols.append(line_symbolizer)

    s.rules.append(r)
    m.append_style('My Style',s)

    # layers
    large_num = 10000000000
    minx = large_num
    maxx = -large_num
    miny = large_num
    maxy = -large_num

    file_list = os.listdir(config.overlay_dir)
    for file in file_list:
        items = file.split('.')
        if items[-1] == 'shp':
            shppath = os.path.join(config.overlay_dir, file)
            ds = ogr.Open(shppath)
            layer = ds.GetLayer(0)
            bbox = layer.GetExtent()

            if minx > bbox[0]:
                minx = bbox[0]
            if miny > bbox[2]:
                miny = bbox[2]
            if maxx < bbox[1]:
                maxx = bbox[1]
            if maxy < bbox[3]:
                maxy = bbox[3]
            
            print('create layer', file)
            mlayer = mapnik.Layer(str(file))
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

            tilefilename = os.path.join(config.overlay_tiles_dir, "%d_%d_%d.json" % (tz, tx, invert_ty))
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
    items = tile.split('.')
    if len(items) != 2 or items[1] != 'json':
        print('not grid file: ', tile)
        return

    tile_file = os.path.join(config.valid_overlay_tiles_dir, tile)
    new_tile_file = os.path.join(config.labels_dir, items[0] + '.png')

    # load grids
    with open(tile_file) as json_data:
        try:
            grid = json.load(json_data)
        except Exception as identifier:
            print identifier
            return
    
    img = numpy.zeros((config.image_dim, config.image_dim))
    for row in range(0, config.image_dim):
        for col in range(0, config.image_dim):
            key_val = resolve(grid, row, col)

            find = False
            if key_val is not None:
                val = key_val[config.class_field]
                for k in range(0, len(config.class_names)):
                    if val == config.class_names[k]:
                        img[row][col] = k
                        find = True
                        break
            if not find:
                # set to backgournd class
                img[row][col] = config.background_class
    
    img = img.astype(int)
    io.imsave(new_tile_file, img)


def grid2image():
    log(flog, 'convert grids from %s into image %s ...' % (config.valid_overlay_tiles_dir, config.labels_dir))

    color_dir = config.valid_overlay_tiles_dir
    gray_dir = config.labels_dir

    if not os.path.exists(gray_dir):
        print 'saving to ' + gray_dir
        os.mkdir(gray_dir)

    tiles = os.listdir(color_dir)

    # progress bar
    widgets = [Bar('>'), ' ', Percentage(), ' ', Timer(), ' ', ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=len(tiles)).start()

    # cnt = 0
    # for tile in tiles:
    #     proces_label_img(tile)
    #     cnt = cnt + 1
    #     pbar.update(cnt)

    nthreads = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=nthreads)

    for i, _ in enumerate(pool.imap_unordered(proces_label_img, tiles), 1):
        pbar.update(i)

    pool.close()
    pool.join()
    pbar.finish()


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

        #img_file = os.path.join(image_dir, img)
        img = io.imread(img)

        class_in_file = []
        for i in range(0, nclass):
            class_in_file.append(False)

        for i in range(0, config.image_dim):
            for j in range(0, config.image_dim): 
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

    # generate train test list
    train_txt = '%s/train.txt' % config.deploy_dir
    test_txt = '%s/test.txt' % config.deploy_dir
    split_train_test(config.stack_dir, config.labels_dir, train_txt, test_txt)


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

    ## get nodata value from source tifs
    src_nodata = get_nodata(config.src_tifs)
    dst_nodata = src_nodata
    if config.image_type == 'png' or src_nodata is None:
        dst_nodata = 0
        
    ## get bands info
    bands = get_bands(config.src_tifs)
    print('src projection: %s, src nodata: %s, #bands: %d' % (src_projection, str(src_nodata), bands))

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
    
    if config.process_analyze and not os.path.exists(config.analyze_tiles_dir):
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
        
            # Delete invalid training tiles
            rm_invalid_tiles(config.analyze_tiles_dir, config.image_type, config.mode)
        else:
            log(flog, 'skip tiler tiles and remove invalid tiles progress ...')
    else:
        log(flog, 'skip analyze progress ...')


    if config.process_visualize and not os.path.exists(config.visualize_tiles_dir):
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
        if not os.path.exists(config.visualize_tiles_dir):
            if not tiler_png(config.merged_visualize_file, config.visualize_tiles_dir, str(config.visualize_level)):
                log(flog, 'tiler png fail, exit ...')
                sys.exit()
        else:
            log(flog, 'skip tiler visualize tiles progress ...')

    
    if config.mode == 'predict':
        if config.image_type == 'tif':
            # already doing overlap, just direct to the folder
            config.analyze_tiles_overlap_dir = config.analyze_tiles_dir
        else:
            create_overlap_predict_tiles(config.analyze_tiles_dir, config.analyze_tiles_overlap_dir, config.overlap)

        write_predict_txt(config.analyze_tiles_overlap_dir, config.test_txt, config.image_type)

        shutil.copy(config.test_txt, '%s/predict.txt' % config.deploy_dir)
        log(flog, 'finished!')
        sys.exit()

    ######### vector labels ###########
    if config.process_label and not os.path.exists(config.labels_dir):
        if not os.path.exists(config.overlay_tiles_dir):
            create_utfgrids()
        else:
            log(flog, 'skip tiler_overlay progress ...')
        if not os.path.exists(config.valid_overlay_tiles_dir):
            copy_labels()
        else:
            log(flog, 'skip copy_labels progress ...')
        if not os.path.exists(config.labels_dir):
            grid2image()
        else:
            log(flog, 'skip grid2image progress ...')
    else:
        log(flog, 'skip tiler vector tiles, copy labels and grid2image progress ...')

    if config.process_label:
        ######## split train test ##########
        split_train_test(config.analyze_tiles_dir, config.labels_dir, config.train_txt, config.test_txt)

        ######## deploy ####################
        if len(config.deploy) >= 1:
            if config.deploy_mode == 'append':
                deploy()
            else:
                # config.deploy_mode == 'stack'
                deploy_stack()

            ######## calculate weights ##########
            calculate_weights()
        else:
            log(flog, 'skip deploy and calculating weights progress ...')
    else:
        log(flog, 'skip split train test and deploy progress ...')

    log(flog, 'finished!')


