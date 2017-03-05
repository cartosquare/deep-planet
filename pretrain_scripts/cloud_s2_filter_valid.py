import os
from skimage import color
from skimage import io
import shutil
import numpy
import multiprocessing 
import config
from progressbar import *


cloud_dir = config.cloud_tiles_dir
really_cloud_dir = config.valid_cloud_tiles_dir

total_pixels = 256 * 256 / 2.0
#total_pixels = 1

def cloud_covered(img):
    sum = 0
    for x in range(0, 256):
        for y in range(0, 256):
            if img[x][y] != 0:
                sum = sum + 1

    return (sum >= total_pixels)

def process_image(image):
    items = image.split('.')
    if len(items) == 2 and items[1] == 'png':
        image_path = os.path.join(cloud_dir, image)

        img = io.imread(image_path)
        if (type(img[0][0]) != numpy.uint8):
            print('Bad things!')

        if cloud_covered(img):
            old_file = os.path.join(cloud_dir, image)
            new_file = os.path.join(really_cloud_dir, image)
            
            shutil.copy(old_file, new_file)


if __name__ == '__main__': 
    if not os.path.exists(really_cloud_dir):
        print 'saving to ' + really_cloud_dir
        os.mkdir(really_cloud_dir)

    image_list = os.listdir(cloud_dir)

    # progress bar
    widgets = [Bar('>'), ' ', Percentage(), ' ', Timer(), ' ', ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=len(image_list)).start()

    nthreads = multiprocessing.cpu_count() * 2
    pool = multiprocessing.Pool(processes=nthreads)

    for i, _ in enumerate(pool.imap_unordered(process_image, image_list), 1):
        pbar.update(i)

    pool.close()
    pool.join()
    pbar.finish()

