import os
import config

if not os.path.exists(config.png_tile_dir):
    os.mkdir(config.png_tile_dir)

files = os.listdir(config.tifs_3857)
for file in files:
    file_path = os.path.join(config.tifs_3857, file)
    encoded_file_path = os.path.join(config.png_tile_dir, file)

    filename, file_extension = os.path.splitext(file)
    if file_extension != '.tif':
		print 'unsupport file extension', file_extension
		continue
    
    if config.image_type == 'png':
        command = 'gdal_translate -scale -ot Byte -co COMPRESS=JPEG -co JPEG_QUALITY=100 %s %s' % (file_path, encoded_file_path)
    else:
        band_str = ''
        for band in config.selected_bands:
            band_str = band_str + (' -b %s' % band)
        command = 'gdal_translate -scale %s -ot Byte -co COMPRESS=JPEG -co JPEG_QUALITY=100 %s %s' % (band_str, file_path, encoded_file_path)
    print command

    os.system(command)
