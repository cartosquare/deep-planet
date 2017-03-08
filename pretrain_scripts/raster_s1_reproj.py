import os
import config

if not os.path.exists(config.tifs_3857):
    os.mkdir(config.tifs_3857)

files = os.listdir(config.src_tifs)
for file in files:
    file_path = os.path.join(config.src_tifs, file)
    projected_file_path = os.path.join(config.tifs_3857, file)

    filename, file_extension = os.path.splitext(file)
    if file_extension != '.tif':
		print 'unsupport file extension', file_extension
		continue

    command = 'gdalwarp -s_srs %s -t_srs EPSG:3857 -r bilinear -srcnodata %s -dstnodata 0 %s %s' % (config.src_projection, config.src_nodata, file_path, projected_file_path)
    print command

    os.system(command)
