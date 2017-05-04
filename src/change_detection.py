import numpy as np
from skimage import io
from skimage import filters
import multiprocessing
import os
import json
import cv2
import argparse
import random


def equal_a1_a2(a1,a2):
	for i in range(len(a1)):
		if a1[i] != a2[i]:
			return False
	return True

def set_change_color(former,latter):
	color = []
	class_count = len(class_colors)
	if len == 0:
		color = np.array([255,0,0,255],'uint8')
	else:
		for i in range(0,class_count):
			if equal_a1_a2(former,class_colors[i]):
				for j in range(class_count):
					if equal_a1_a2(latter,class_colors[j]):
						if j<i:
							color = np.array(detect_colors[(i-1)*(class_count-1)+j-1],'uint8')
						if j>i:
							color = np.array(detect_colors[(i-1)*(class_count-1)+j-2],'uint8')

def compare_different(img_former,img_latter,img_Result,filename,noise_size):
	for x in range(len(img_former)):
		for y in range(len(img_former[0])):
			img_Result[x][y] =np.array([255,255,255,0],'uint8')
			if ( equal_a1_a2(img_former[x][y],img_latter[x][y]) == False):
				color = set_change_color(img_former[x][y],img_latter[x][y])
				img_Result[x][y] = color
	Result_save_path = os.path.join(Result_file_list_path,filename)
	print filename
	if noise_size != 0:
		img_Result = cv2.medianBlur(img_Result,noise_size)
	io.imsave(Result_save_path,img_Result)
if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("config_path",help = "the path of config_file")
	args = parser.parse_args()
	global config_file
	with open(args.config_path,'r') as f:
		config_file = json.load(f)
		
		
	Root_Dir = config_file['root_dir']
	img_latter_file_list_path = os.path.join(Root_Dir,'output',config_file['detect_projects'][1],'predict_pd_crop_tiles')
	img_former_file_list_path = os.path.join(Root_Dir,'output',config_file['detect_projects'][0],'predict_pd_crop_tiles')
	img_former_filelist = os.listdir(img_former_file_list_path)
	
	
	
	global class_colors
	class_colors = []
	if 'class_colors' in config_file:
		class_colors = config_file['class_colors']
	else:
		print 'Warning::you should set class_colors'
		os._exit()
	
	
	global Result_file_list_path
	Result_file_list_path = os.path.join(Root_Dir,'output',config_file['detect_projects'][0]+'_To_'+config_file['detect_projects'][1],'compare_Result')
	if (os.path.exists(Result_file_list_path) == False):
		os.makedirs(Result_file_list_path)
	
	
	noise_size = 0
	if config_file.has_key('noise_size'):
		noise_size = config_file['noise_size']
		
		
	classes_count = len(config_file['class_names'])	
	global detect_colors
	if 'detect_colors' in config_file:
		detect_colors = config_file['detect_colors']
	else:
		detect_colors = []
		for i in range(0,(classes_count+1)*classes_count):
			detect_colors.append([random.randint(0,255),random.randint(0,255),random.randint(0,255),255])
	processes = 4
	if config_file.has_key('CPU_processes'):
		processes = config_file['CPU_processes']
	pool = multiprocessing.Pool(processes)
	
	
	
	result = []
	for filename in img_former_filelist:
		img_former_filepath = os.path.join(img_former_file_list_path,filename)
		img_latter_filepath = os.path.join(img_latter_file_list_path,filename)
		img_former = io.imread(img_former_filepath)
		img_latter = io.imread(img_latter_filepath)
		
		a = img_former.shape[0]
		b = img_former.shape[1]
		img_Result = [[0 for x in range(a)] for y in range(b)]
		
		result.append(pool.apply_async(compare_different,(img_former,img_latter,img_Result,filename,noise_size, )))
	pool.close()
	pool.join()
	for res in result:
		print res.get()