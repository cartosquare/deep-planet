# -*- coding: utf-8 -*-
import numpy as np

##########################################
#
# configuration class
#
##########################################

class DeepPlanetConfig:
	def Initialize(self, pobject):
		#********************************   通用参数  **********************************
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

		# 影像投影和nodata值
		if 'src_projection' in pobject:
			self.src_projection = pobject['src_projection']
		else:
			print('warning: no src projection set!')
			return False

		if 'src_nodata' in pobject:
			self.src_nodata = pobject['src_nodata']
		else:
			print('warning: no src_nodata set! default to 0')
			self.src_nodata = '0'

		# 训练的波段
		# rapideye false-color-compose bands: [5, 3, 2]
		# GF false-color compose bands: [4, 3, 2]
		# planetlabs [1, 2, 3]
		if 'analyze_bands' in pobject:
			self.analyze_bands = pobject['analyze_bands']
		else:
			print('warning: no analyze_bands set! default to [1 2 3]')
			self.analyze_bands = [1, 2, 3]

		# 可视化的波段
		if 'visualize_bands' in pobject:
			self.visualize_bands = pobject['visualize_bands']
		else:
			print('warning: no visualize_bands set! default to [1 2 3]')
			self.visualize_bands = [1, 2, 3]

		# 需要分割的类别数
		if 'classes' in pobject:
			self.classes = pobject['classes']
		else:
			print('warning: must specify classes')
			return False

		if 'overlap' in pobject:
			self.overlap = pobject['overlap']
		else:
			self.overlap = 128

		#以及需要忽略的类别（一般是背景）
		#ignore_class = None # 
		if 'ignore_class' in pobject:
			self.ignore_class = pobject['ignore_class']
		else:
			print('warning: no ignore_class set! default to None')
			self.ignore_class = None

		# 数据目录。即处理训练样本的目录所在。执行一个分割任务时，一般在training_set目录下新建一个目录。
		if 'data_name' in pobject:
			self.data_name = pobject['data_name']
		else:
			print('data_name must specified!!!')
			return False
		
		if 'tile_extent' in pobject:
			# 训练样本范围
			# for sanxia
			#tile_extent = [11779924.71, 3315613.19, 12429394.15, 3728152.58]
			# for zhanjiang
			#tile_extent = [12272311.892742, 2403831.52580, 12304619.6025, 2436356.63936]
			self.tile_extent = pobject['tile_extent']
		else:
			print('tile_extent must specified!')
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

		# 类别标签
		if 'label_colours' in pobject:
			self.label_colours = pobject['label_colours']
		else:
			print 'label_colours must specified!!!'
			return False

		# 发布训练样本的目录
		self.deploy_dir = ''
		for i in range(len(self.deploy)):
			if i == (len(self.deploy) - 1):
				self.deploy_dir = self.deploy_dir + self.deploy[i]
			else:
				self.deploy_dir = self.deploy_dir + self.deploy[i] + '_'

		# 处理样本的根目录
		self.data_root = 'training_set/%s' % self.data_name
		# log文件
		self.log_file = '%s/log.txt' % self.data_root

		###################### 地图级别 #########################################
		self.worldOriginalx = -20037508.342787
		self.worldOriginaly = 20037508.342787
		self.zoomReses = [156543.033928,78271.516964,39135.758482,19567.879241,9783.9396205,4891.96981025,2445.984905125,1222.9924525625,611.49622628125,305.748113140625,152.8740565703125,76.43702828515625,38.21851414257813,19.10925707128906,9.55462853564453,4.777314267822266,2.388657133911133,1.194328566955567,0.597164283477783,0.298582141738892,0.14929107086945,0.07464553543473]

		###################### 和训练样本相关的变量 ###############################
		# 训练网络
		self.model_dir = 'models'
		self.solver = '%s/segnet_solver.prototxt' % self.model_dir
		self.train_net_template = 'models/segnet_train.prototxt'
		self.train_net = '%s/segnet_train.prototxt' % self.model_dir

		# 训练好的网络参数
		self.snapshot_dir = '%s/training' % self.model_dir
		self.snapshot_prefix = '%s/dp' % self.snapshot_dir
		self.trained_weights = '%s_iter_%d.caffemodel' % (self.snapshot_prefix, self.snapshot)

		# 测试网络
		self.test_dir = '%s/inference' % self.model_dir
		self.test_weights = '%s/test_weights.caffemodel' % self.test_dir
		self.test_net = '%s/segnet_test.prototxt' % self.model_dir
		self.predict_net = '%s/segnet_predict.prototxt' % self.model_dir
		self.inference_net_template = 'models/segnet_inference.prototxt'

		# 测试数据的输出目录
		self.test_gt_dir = '%s/gt' % self.deploy_dir
		self.test_pd_dir = '%s/pd' % self.deploy_dir

		# 预测数据输出目录
		self.predict_dir = '%s/predict_pd' % self.deploy_dir
		self.predict_tiles_dir = '%s/predict_pd_tiles' % self.deploy_dir
		self.predict_fusion_tiles_dir = '%s/predict_pd_fusion_tiles' % self.deploy_dir
		self.predict_crop_image_dir = '%s/predict_pd_crop_tiles' % self.deploy_dir
		
		# 分类权重
		self.weight_file = '%s/weights.txt' % self.deploy_dir

		#********************************   影像样本准备时涉及的参数  **************************
		# 原始影像所在的目录
		self.src_tifs = '%s/tifs' % self.data_root

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

		#******************************* 标注样本准备涉及的参数 *************************
		# 训练标注，shapefile格式，所在的目录
		self.overlay_dir = '%s/overlay' % self.data_root
		self.style_file = '%s/style.json' % self.data_root
		self.lod_file = '%s/lod.json' % self.data_root
		self.tiler_file = '%s/tiler_config.json' % self.data_root

		# This configure should not be touch!!!
		# because label_color directory is created by another program!!!
		# If you change this, change config.json too!!!
		# 标注切割后所在的目录（rgb）
		self.overlay_tiles_dir = '%s/labels_color' % self.data_root
		# 过滤无效标注后的目录（rgb）
		self.valid_overlay_tiles_dir = '%s/valid_labels_color' % self.data_root
		# rgb标注转换为灰度标注的目录
		self.labels_dir = '%s/labels' % self.data_root

		#********************************* 训练样本输出的参数 ***********************
		# 训练集合测试集文件分布
		self.train_txt = '%s/train.txt' % (self.data_root)
		self.test_txt = '%s/test.txt' % (self.data_root)

		# **************************** 可视化页面 ***************************
		self.visualize_page = '%s/visualize.html' % (self.data_root)
		self.label_page = '%s/label.html' % (self.data_root)
		
		#****************************** cloud configuration[not used] *********************
		self.cloud_dir = '%s/cloud' % self.data_root
		self.cloud_tiles_dir = '%s/cloud_tiles' % self.data_root
		self.valid_cloud_tiles_dir = '%s/valid_cloud_tiles' % self.data_root

		return True


