from osgeo import gdal
import sys
# this allows GDAL to throw Python Exceptions
gdal.UseExceptions()

import os
import shutil
import multiprocessing 
import config
from progressbar import *


def proces_tif(tif):
    tif_file = os.path.join(tif_dir, tif)
    new_tif_file = os.path.join(new_tif_dir, tif)

    try:
        src_ds = gdal.Open(tif_file)
    except RuntimeError, e:
        #print 'Unable to open', tif_file
        #print e
        return

    #print '[Raster Band Count]: ', src_ds.RasterCount
    nodata = False
    for band in range(src_ds.RasterCount):
        band += 1
        #print '[Getting Band]: ', band
        srcband = src_ds.GetRasterBand(band)
        if srcband is None:
            print '[Band is None]'
            return
        
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
                    #print r, c, dataraster[r][c]
                    nodata = True
                    break
            if nodata:
                break
        if nodata:
            break

    if not nodata:
        #print('%s->%s' % (tif_file, new_tif_file))
        shutil.copyfile(tif_file, new_tif_file)


if __name__ == '__main__': 
    tif_dir = config.tif_tiles_dir
    new_tif_dir = config.valid_tif_tiles_dir
    if not os.path.exists(new_tif_dir):
        os.mkdir(new_tif_dir)

    print 'process tifs in %s' % tif_dir
    print 'saving to %s' % new_tif_dir

    tifs = os.listdir(tif_dir)

    #for tif in tifs:
    #    proces_tif(tif)

    # progress bar
    widgets = [Bar('>'), ' ', Percentage(), ' ', Timer(), ' ', ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=len(tifs)).start()

    nthreads = multiprocessing.cpu_count() * 2
    pool = multiprocessing.Pool(processes=nthreads)

    for i, _ in enumerate(pool.imap_unordered(proces_tif, tifs), 1):
        pbar.update(i)

    pool.close()
    pool.join()
    pbar.finish()