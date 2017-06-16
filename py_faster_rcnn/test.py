#!/usr/bin/env python
import os
path='/data2/data/cache/chimney_exploded/L17/'
img=[]
for parent,dirnames,filenames in os.walk(path):
	for filename in filenames:
		#print os.path.join(parent,filename)
		img.append(filename)
print len(img)
