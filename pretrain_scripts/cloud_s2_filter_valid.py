import os
from skimage import color
from skimage import io
import shutil
import multiprocessing 

cloud_dir = 'cloud_tiles'
really_cloud_dir = 'really_cloud_tiles'
total_pixels = 256 * 256 / 2.0


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
        image_path = os.path.join(label_dir, image)

        img = io.imread(image_path)
        if cloud_covered(img):
            old_file = os.path.join(cloud_dir, image)
            new_file = os.path.join(really_cloud_dir, image)
            
            shutil.copy(old_file, new_file)


if __name__ == '__main__': 
    if not os.path.exists(really_cloud_dir):
        print 'saving to ' + really_cloud_dir
        os.mkdir(really_cloud_dir)

    image_list = os.listdir(cloud_dir)

    pool = multiprocessing.Pool(multiprocessing.cpu_count()) 
    pool.map(process_image, image_list)
