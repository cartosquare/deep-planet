import os
import os.path
import config

if config.image_type == 'tif':
	working_dir = config.tifs_3857
else:
	working_dir = config.png_tile_dir

for parent, dirnames, filenames in os.walk(working_dir):
	for file in filenames:
		print "process file: " + os.path.join(parent, file)
		
		filename, file_extension = os.path.splitext(file)
		if file_extension != '.tif':
			print 'unsupport file extension', file_extension
			continue

		command = "gdaladdo -r gauss -ro %s 2 4 8 16" % (os.path.join(parent, file))
		print command
		os.system(command)
		
