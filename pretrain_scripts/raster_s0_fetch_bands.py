import os
import config

# create dest dir if not exists
if not os.path.exists(config.src_tifs):
    os.mkdir(config.src_tifs)

files = os.listdir(config.raw_tifs)
for file in files:
    # process every tif under dir @raw_tifs
    file_path = os.path.join(config.raw_tifs, file)
    fetched_file_path = os.path.join(config.src_tifs, file)

    filename, file_extension = os.path.splitext(file)
	if file_extension != '.tif':
		print 'unsupport file extension', file_extension
		continue

    band_str = ''
    for band in config.selected_bands:
        band_str = band_str + (' -b %s' % band)

    command = 'gdal_translate %s %s %s' % (file_path, fetched_file_path, band_str)
    print command

    os.system(command)
