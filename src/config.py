# -*- coding: utf-8 -*-
import numpy as np
import os
import random

# Global settings

caffe_root = './caffe-segnet-cudnn5/'
#caffe_root = './caffe-segnet/'

##########################################
#
# configuration class
#
##########################################

class DeepPlanetConfig:
	def Initialize(self, pobject):
		#********************************   通用参数  **********************************
		# 工程根目录（处理数据的工程目录）
		if 'root_dir' in pobject:
			self.root_dir = pobject['root_dir']
		else:
			self.root_dir = '.'

		# could be train or predict
		# when train, tiles with nodata value will be removed
		# when predict, tiles with nodata will be keeped
		if 'mode' in pobject:
			self.mode = pobject['mode']
		else:
			self.mode = 'train'
		
		if 'process_visualize' in pobject:
			self.process_visualize =  pobject['process_visualize']
		else:
			self.process_visualize = False

		if 'process_analyze' in pobject:
			self.process_analyze =  pobject['process_analyze']
		else:
			self.process_analyze = True

		if 'process_label' in pobject:
			self.process_label = pobject['process_label']
		else:
			self.process_label = True

		if 'rm_incomplete_tile' in pobject:
			self.rm_incomplete_tile = pobject['rm_incomplete_tile']
		else:
			self.rm_incomplete_tile = False

		# 训练样本大小，目前只支持 256px * 256px
		self.image_dim = 256

		# 训练样本分辨率（0-19）
		if 'tile_level' in pobject:
			self.tile_level = pobject['tile_level']
		else:
			self.tile_level = '15'

		if 'visualize_level' in pobject:
			self.visualize_level = pobject['visualize_level']
		else:
			self.visualize_level = '10-15'

		# 训练样本类型。可以为 'tif' 或是 'png'
		if 'image_type' in pobject:
			self.image_type = pobject['image_type']
		else:
			self.image_type = 'tif'

		# 训练的波段
		# rapideye false-color-compose bands: [5, 3, 2]
		# GF false-color compose bands: [4, 3, 2]
		# planetlabs [1, 2, 3]
		if 'analyze_bands' in pobject:
			self.analyze_bands = pobject['analyze_bands']
		else:
			print('warning: no analyze_bands set! default all bands')
			self.analyze_bands = []
		
		if 'extra_bands' in pobject:
			self.extra_bands = pobject['extra_bands']
			for band_method in self.extra_bands:
				print(band_method, self.extra_bands[band_method])
		else:
			self.extra_bands = None

		# 可视化的波段
		if 'visualize_bands' in pobject:
			self.visualize_bands = pobject['visualize_bands']
		else:
			print('warning: no visualize_bands set! default to [1 2 3]')
			self.visualize_bands = [1, 2, 3]

		# 合并时是否使用虚拟数据集
		if 'virtual_dataset' in pobject:
			self.virtual_dataset = pobject['virtual_dataset']
		else:
			self.virtual_dataset = False

		if 'overlap' in pobject:
			self.overlap = pobject['overlap']
		else:
			if self.mode == 'train':
				# overlap in train mode is a bit different to the mode of predict
				# and we do not support overlap for png format
				self.overlap = 0
			else:
				self.overlap = 128

		# class filed in shapefile
		if 'class_field' in pobject:
			self.class_field = pobject['class_field']
		else:
			print('warning: must specify class field!')
			return False

		# 数据目录。即处理训练样本的目录所在。执行一个分割任务时，一般在training_set目录下新建一个目录。
		if 'data_name' in pobject:
			self.data_name = pobject['data_name']
		else:
			print('data_name must specified!!!')
			return False

		if 'deploy' in pobject:
			# 需要发布的训练集（名称和数据目录一样，可以指定多个数据目录进行合并）
			self.deploy = pobject['deploy']
		else:
			self.deploy = [self.data_name]

		# 训练参数
		if 'gpu' in pobject:
			self.gpu = pobject['gpu']
		else:
			self.gpu = 0

		if 'use_gpu' in pobject:
			self.use_gpu = pobject['use_gpu']
		else:
			self.use_gpu = False
		
		if 'snapshot' in pobject:
			self.snapshot = pobject['snapshot']
		else:
			self.snapshot = 10000

		if 'use_snapshot' in pobject:
			self.use_snapshot = pobject['use_snapshot']
		else:
			self.use_snapshot = 100000
		
		if 'weights' in pobject:
			self.weights = pobject['weights']
		else:
			self.weights = None

		if 'restore_snapshot' in pobject:
			self.restore_snapshot = pobject['restore_snapshot']
		else:
			self.restore_snapshot = None
			
		if 'batch_size' in pobject:
			self.batch_size = pobject['batch_size']
		else:
			self.batch_size = 6

		if 'max_iter' in pobject:
			self.max_iter = pobject['max_iter']
		else:
			self.max_iter = 400000
			
		# 测试样本数
		if 'test_iter' in pobject:
			self.test_iter = pobject['test_iter']
		else:
			self.test_iter = None

		if 'substract_mean' in pobject:
			self.substract_mean = pobject['substract_mean']
		else:
			self.substract_mean = False
			
		# 类别标签
		if 'class_names' in pobject:
			self.class_names = pobject['class_names']
		else:
			print 'class_names must specified!!!'
			return False

		# background class set to the array index of last class
		self.background_class = len(self.class_names)

		# whether to ignore background
		if 'ignore_background' in pobject:
			self.ignore_background = pobject['ignore_background']
		else:
			if self.background_class == 1:
				# do not ignore background when there are only two classes
				self.ignore_background = False
			else:
				self.ignore_background = True

		# 需要分割的类别数
		self.classes = len(self.class_names)
		if not self.ignore_background:
			# add background_class
			self.classes = self.classes + 1

		if 'class_colors' in pobject:
			self.class_colors = pobject['class_colors']
		else:
			self.class_colors = []
			for i in range(0, self.classes):
				self.class_colors.append([random.randint(0, 255),  random.randint(0, 255), random.randint(0, 255), 255])

		if not self.ignore_background:
			print('#classes: %d, with background_class %d' % (self.classes, self.background_class))
		else:
			print('#classes: %d, without background_class %d' % (self.classes, self.background_class))

		# 发布训练样本的目录
		self.deploy_root = os.path.join(self.root_dir, 'output')
		if not os.path.exists(self.deploy_root):
			os.mkdir(self.deploy_root)
		
		self.deploy_dir = ''
		for i in range(len(self.deploy)):
			if i == (len(self.deploy) - 1):
				self.deploy_dir = self.deploy_dir + self.deploy[i]
			else:
				self.deploy_dir = self.deploy_dir + self.deploy[i] + '_'
		self.deploy_dir = os.path.join(self.deploy_root, self.deploy_dir)

		# 不同数据集的影像结合进行训练的两种方式
		self.deploy_mode = 'append'
		if 'deploy_mode' in pobject:
			# 波段叠加，适合区域相同但是波段不同的数据
			self.deploy_mode = pobject['deploy_mode']
		else:
			# 简单合并，适合于不同年份或是不同区域的数据
			self.deploy_mode = 'append'

		# 处理样本的根目录
		self.project_dir = os.path.join(self.root_dir, 'projects')
		self.data_root = '%s/%s' % (self.project_dir, self.data_name)
		if not os.path.exists(self.data_root):
			print('%s not exist!' % (self.data_root))
			return False

		# log文件
		self.log_file = '%s/log.txt' % self.data_root

		# nodata value 
		# could not less than 0, because our datatype is UInt16
		if 'nodata' in pobject:
			self.nodata = pobject['nodata']
		else:
			self.nodata = 0

 		###################### 和训练样本相关的变量 ###############################
		# 训练网络
		self.model_dir = os.path.join(self.deploy_dir, 'models')
		self.solver = '%s/segnet_solver.prototxt' % self.model_dir
		self.train_net_template = 'models/segnet_train.prototxt'
		self.train_net = '%s/segnet_train.prototxt' % self.model_dir

		# 训练好的网络参数
		self.snapshot_dir = '%s/training' % self.model_dir
		self.snapshot_prefix = '%s/dp' % self.snapshot_dir
		self.trained_weights = '%s_iter_%d.caffemodel' % (self.snapshot_prefix, self.use_snapshot)

		# 测试网络
		self.test_dir = '%s/inference' % self.model_dir
		self.test_weights = '%s/test_weights.caffemodel' % self.test_dir
		self.inference_net = '%s/deploy.prototxt' % self.test_dir

		self.test_net = '%s/segnet_test.prototxt' % self.model_dir
		self.predict_net = '%s/segnet_predict.prototxt' % self.model_dir
		self.inference_net_template = 'models/segnet_inference.prototxt'
		self.deploy_net = '%s/deploy.prototxt' % self.model_dir

		# 测试数据的输出目录
		self.test_gt_dir = '%s/gt' % self.deploy_dir
		self.test_pd_dir = '%s/pd' % self.deploy_dir
		self.test_statistic_file = '%s/acc.txt' % self.deploy_dir

		# 预测数据输出目录
		predict_output_dir = os.path.join(self.root_dir,'output',self.data_name)
		if not os.path.exists(predict_output_dir):
			os.mkdir(predict_output_dir)
		self.predict_dir = '%s/predict_pd' % predict_output_dir
		self.predict_tiles_dir = '%s/predict_pd_tiles' % predict_output_dir
		self.predict_fusion_tiles_dir = '%s/predict_pd_fusion_tiles' % predict_output_dir
		self.predict_crop_image_dir = '%s/predict_pd_crop_tiles' % predict_output_dir
		self.predict_crop_tif_dir = '%s/predict_pd_crop_tifs' % predict_output_dir
		self.predict_crop_vector_dir = '%s/predict_pd_crop_vector' % predict_output_dir
		self.predict_vector_file = '%s/segment.shp' % predict_output_dir
		self.predict_tif_file = '%s/segment.tif' % predict_output_dir
		# 分类权重
		self.weight_file = '%s/weights.txt' % predict_output_dir

		# mean file
		self.mean_file = '%s/means.txt' % self.deploy_dir
		#********************************   影像样本准备时涉及的参数  **************************
		# 原始影像所在的目录
		self.src_tifs = '%s/tifs' % self.data_root

		# 统一nodata值后的目录
		self.samenodata_dir = '%s/samenodata_tifs' % self.data_root

		# 投影为 web 墨卡托的影像所在的目录
		self.tifs_3857 = '%s/tifs_3857' % self.data_root

		# 用于分析的影像目录
		self.analyze_tifs_dir = '%s/analyze_tif' % self.data_root

		# 用于可视化的影像目录
		self.visualize_tifs_dir = '%s/visualize_tif' % self.data_root

		# 将 tifs_3857 中的影像合并成的虚拟文件（为了下一步的切割）
		self.merged_analyze_file = '%s/merged_analyze.tif' % self.data_root

		# 将 png_tile_dir 中的影像合并成的虚拟文件（为了下一步的切割）
		self.merged_visualize_file = '%s/merged_visualize.tif' % self.data_root

		# 切割后的训练瓦片目录
		self.analyze_tiles_dir = '%s/analyze_tiles' % self.data_root
		self.analyze_tiles_overlap_dir = '%s/analyze_tiles_overlap' % self.data_root

		# 切割后的训练瓦片目录
		self.visualize_tiles_dir = '%s/visualize_tiles' % self.data_root

		# 多个影像重叠的目录
		self.stack_dir = '%s/stack_tiles' % self.deploy_dir
		#******************************* 标注样本准备涉及的参数 *************************
		# 训练标注，shapefile格式，所在的目录
		self.overlay_dir = '%s/overlay' % self.data_root
		# label subdirectory list
		self.label_dirs = []
		file_list = os.listdir(self.overlay_dir)
		for file_path in file_list:
			filename, extension = os.path.splitext(file_path)
			if extension == '.shp':
				self.label_dirs.append(filename)

		self.style_file = '%s/style.json' % self.data_root
		self.lod_file = '%s/lod.json' % self.data_root
		self.tiler_file = '%s/tiler_config.json' % self.data_root

		# 标注切割后所在的目录
		self.overlay_tiles_dir = '%s/labels_grid' % self.data_root
		# 标注转换为图片格式所在的目录
		self.labels_dir = '%s/labels' % self.data_root

		#********************************* 训练样本输出的参数 ***********************
		# 训练集合测试集文件分布
		self.train_txt = '%s/train.txt' % (self.data_root)
		self.test_txt = '%s/test.txt' % (self.data_root)

		# **************************** 可视化页面 ***************************
		self.visualize_page = '%s/visualize.html' % (self.data_root)
		self.label_page = '%s/label.html' % (self.data_root)
		
		#****************************** cloud configuration[not used] *********************
		self.cloud_file = '%s/cloud/cloud.shp' % self.data_root
		self.cloud_tiles_dir = '%s/cloud_tiles' % self.data_root
		self.valid_cloud_tiles_dir = '%s/valid_cloud_tiles' % self.data_root

		return True


