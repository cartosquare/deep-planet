import os
import os.path


data_dir = "proj_tifs"

for parent, dirnames, filenames in os.walk(data_dir):
	for file in filenames:
		print "process file: " + os.path.join(parent, file)
		
		filename, file_extension = os.path.splitext(file)
		if file_extension != 'tif':
			print 'unsupport file extension', file_extension
			continue

		command = "gdaladdo -r gauss %s 2 4 8 16" %(os.path.join(parent, file))
		print command
        os.system(command); 
		
