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
		# when train, tiles with nodata value will be remove
		# when predict, tiles with nodata will be keep remain
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
		self.dim_row = 256
		self.dim_col = 256

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
		#src_projection = 'EPSG:32649'
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
		#rapideye false-color-compose bands: [5, 3, 2]
		# FG false-color compose bands: [4, 3, 2]
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

		# 测试样本数
		if 'test_iter' in pobject:
			self.test_iter = pobject['test_iter']
		else:
			self.test_iter = 1
		

		# 类别标签
		if 'label_colours' in pobject:
			self.label_colours = pobject['label_colours']
		else:
			print 'label_colours must specified!!!'
			return False


		# 发布训练样本的目录
		self.deploy_dir = 'deploy-sanxia'

		self.data_root = 'training_set/%s' % self.data_name


		# 训练和测试网络的
		self.trained_weights = '%s/models/Training/envnet_iter_10000.caffemodel' % self.data_root
		self.test_weights = '%s/models/inference/test_weights.caffemodel' % self.data_root

		self.log_file = '%s/log.txt' % self.data_root

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

		# 切割后的训练瓦片目录
		self.visualize_tiles_dir = '%s/visualize_tiles' % self.data_root

		#******************************* 标注样本准备涉及的参数 *************************
		# 训练标注，shapefile格式，所在的目录
		self.overlay_dir = '%s/overlay' % self.data_root

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
		self.predict_txt = '%s/predict.txt' % (self.data_root)

		#********************************  测试时需要的参数 ***************************
		# 模型所在目录
		self.model_directory = '%s/models/inference' % self.data_root
		# 训练模型
		self.train_model = '%s/models/segnet_train.prototxt' % self.data_root
		# 测试模型
		self.test_model = '%s/models/segnet_inference.prototxt' % self.data_root
		# 分类权重
		self.weight_file = '%s/models/weights.txt' % self.data_root

		# 测试数据的输出目录
		self.test_img_dir = '%s/models/img' % self.data_root
		self.test_gt_dir = '%s/models/gt' % self.data_root
		self.test_pd_dir = '%s/models/pd' % self.data_root

		#****************************** cloud configuration *********************
		self.cloud_dir = '%s/cloud' % self.data_root
		self.cloud_tiles_dir = '%s/cloud_tiles' % self.data_root
		self.valid_cloud_tiles_dir = '%s/valid_cloud_tiles' % self.data_root

		#***************************** test configuration ****************
		self.predict_tif = '%s/predict_area.tif' % self.data_root


		# predict tiles dir
		self.predict_image_dir = '%s/pd' % self.data_root
		self.predict_tiles_dir = '%s/predict_tiles' % self.data_root

		self.predict_confidence_image_dir = '%s/pd_prob' % self.data_root
		self.predict_confidence_dir = '%s/predict_prob' % self.data_root

		self.predict_merged_image_dir = '%s/predict_merged_tiles' % self.data_root

		return True


