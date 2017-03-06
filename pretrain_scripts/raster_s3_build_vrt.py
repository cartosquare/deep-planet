import config
import os

command = 'gdalbuildvrt %s %s/*.tif' % (config.merged_tifs, config.tifs_3857)
print command
os.system(command)
