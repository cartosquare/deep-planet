from osgeo import gdal
import sys
# this allows GDAL to throw Python Exceptions
gdal.UseExceptions()

import os
import shutil
import multiprocessing 

def proces_tif(tif):
    tif_file = os.path.join(tif_dir, tif)
    new_tif_file = os.path.join(new_tif_dir, tif)

    try:
        src_ds = gdal.Open(tif_file)
    except RuntimeError, e:
        print 'Unable to open', tif_file
        print e
        continue

    #print '[Raster Band Count]: ', src_ds.RasterCount
    nodata = False
    for band in range(src_ds.RasterCount):
        band += 1
        #print '[Getting Band]: ', band
        srcband = src_ds.GetRasterBand(band)
        if srcband is None:
            print '[Band is None]'
            continue
        
        try:
            stats = srcband.GetStatistics(True, True)
        except RuntimeError, e:
            #print e
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
                    print r, c, dataraster[r][c]
                    nodata = True
                    break
            if nodata:
                break
        if nodata:
            break

    if not nodata:
        print('%s->%s' % (tif_file, new_tif_file))
        shutil.copyfile(tif_file, new_tif_file)


if __name__ == '__main__': 
    if len(sys.argv) < 3:
    print('Usage: python raster_s5_copy_valid_tiles.py tif_tile_dir new_tif_tile_dir')
    exit()

    tif_dir = sys.argv[1]
    new_tif_dir = sys.argv[2]
    if not os.path.exists(new_tif_dir):
        os.mkdir(new_tif_dir)

    tifs = os.listdir(tif_dir)

    pool = multiprocessing.Pool(multiprocessing.cpu_count()) 
    pool.map(proces_tif, tifs)