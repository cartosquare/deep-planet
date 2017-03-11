# -*- coding: utf-8 -*-
import numpy as np

##########################################
#
# configuration options
#
##########################################

#********************************   通用参数  **********************************
# 训练样本大小，目前只支持 256px * 256px
dim_row = 256
dim_col = 256

# 训练样本分辨率（0-19）
tile_level = 15

# 训练样本类型。可以为 'tif' 或是 'png'
image_type = 'tif'

# 使用的波段
selected_bands = [5, 3, 2]

# 可视化的波段
vis_bands = [5, 3, 2]

# 需要分割的类别数
classes = 31
#以及需要忽略的类别（一般是背景）
#ignore_class = None # 
ignore_class = 31

# 数据目录。即处理训练样本的目录所在。执行一个分割任务时，一般在training_set目录下新建一个目录。
data_name = 'sanxia_2012'
data_root = 'training_set/%s' % data_name

# 训练样本范围
# for sanxia
tile_extent = [11779924.71, 3315613.19, 12429394.15, 3728152.58]
# for zhanjiang
#tile_extent = [12272311.892742, 2403831.52580, 12304619.6025, 2436356.63936]

# 需要发布的训练集（名称和数据目录一样，可以指定多个数据目录进行合并）
deploy = ['sanxia_2012']

# 训练和测试网络的
trained_weights = '%s/models/Training/envnet_iter_10000.caffemodel' % data_root
test_weights = '%s/models/inference/test_weights.caffemodel' % data_root

# 测试样本数
test_iter = 191

# 类别标签
label_colours_bk = np.array([{
    	'name': '道路', 'color': [146, 211, 48, 255], 'label': 0
	}, {
    	'name': '背景', 'color': [143, 144, 239, 0], 'label': 1
    }
])
label_colours = np.array([{
    	'name': '常绿阔叶林', 'color': [146, 211, 48], 'label': 0
	}, {
    	'name': '常绿针叶林', 'color': [143, 144, 239], 'label': 1
	}, {
    	'name': '混交林', 'color': [225, 137, 77], 'label': 2
	}, {
    	'name': '落叶阔叶林', 'color': [26, 223, 220], 'label': 3
	}, {
    	'name': '落叶针叶林', 'color': [221, 122, 183], 'label': 4
	}, {
    	'name': '常绿灌木林', 'color': [233, 111, 111], 'label': 5
	}, {
    	'name': '落叶灌木林', 'color': [208, 24, 61], 'label': 6
	}, {
    	'name': '草地', 'color': [114, 202, 132], 'label': 7
	}, {
    	'name': '城市草本绿地', 'color': [224, 203, 118], 'label': 8
	}, {
    	'name': '旱地', 'color': [138, 94, 208], 'label': 9
	}, {
    	'name': '水田', 'color': [117, 168, 240], 'label': 10
	}, {
    	'name': '灌木种植园', 'color': [222, 57, 16], 'label': 11
	}, {
    	'name': '苗圃', 'color': [152, 80, 204], 'label': 12
	}, {
    	'name': '乔木种植园', 'color': [216, 173, 108], 'label': 13
	}, {
    	'name': '采矿场地', 'color': [84, 231, 48], 'label': 14
	}, {
    	'name': '城市居民地', 'color': [195, 226, 70], 'label': 15
	}, {
    	'name': '城市乔灌混合绿地', 'color': [148, 221, 99], 'label': 16
	}, {
    	'name': '城市乔木绿地', 'color': [210, 210, 105], 'label': 17
	}, {
    	'name': '独立工业和商业用地', 'color': [193, 33, 237], 'label': 18
	}, {
    	'name': '基础设施', 'color': [205, 78, 207], 'label': 19
	}, {
    	'name': '垃圾填埋场', 'color': [37, 75, 215], 'label': 20
	}, {
    	'name': '镇村居民地', 'color': [20, 223, 139], 'label': 21
	}, {
    	'name': '河流季节性水面', 'color': [217, 114, 198], 'label': 22
	}, {
    	'name': '湖泊', 'color': [145, 124, 99], 'label': 23
	}, {
    	'name': '坑塘', 'color': [71, 36, 225], 'label': 24
	}, {
    	'name': '水库', 'color': [15, 231, 185], 'label': 25
	}, {
    	'name': '水库季节性水面', 'color': [210, 23, 101], 'label': 26
	}, {
    	'name': '水生植被', 'color': [31, 148, 221], 'label': 27
	}, {
    	'name': '永久河流水面', 'color': [92, 220, 92], 'label': 28
	}, {
    	'name': '坚硬表面', 'color': [66, 240, 133], 'label': 29
	}, {
    	'name': '松散表面', 'color': [114, 209, 230], 'label': 30
	}, {
    	'name': '未标注', 'color': [0, 0, 0], 'label': 31
	}])

#********************************   影像样本准备时涉及的参数  **************************
# 包含原始影像的目录。在该目录中的影像会经过波段提取处理进入src_tifs目录
raw_tifs = '%s/raw_tifs' % data_root

# 从原始影像中提取出需要的波段的目录。在该目录中的影像会经过重投影进入tifs_3857目录
src_tifs = '%s/tifs' % data_root
# 影像投影和nodata值
src_projection = 'EPSG:32649'
src_nodata = '0'

# 投影为 web 墨卡托的影像所在的目录
tifs_3857 = '%s/tifs_3857' % data_root

# 使用JPEG编码的数据目录（为了显示以及切割成png格式）
png_tile_dir = '%s/rendered_tif' % data_root

# 将 tifs_3857 中的影像合并成的虚拟文件（为了下一步的切割）
merged_tifs = '%s/merged.vrt' % data_root

# 将 png_tile_dir 中的影像合并成的虚拟文件（为了下一步的切割）
merged_png_tifs = '%s/merged_png.tif' % data_root

# 切割后的tif瓦片目录
tif_tiles_dir = '%s/tif_tiles' % data_root
# 去除无效的tif瓦片后的目录
valid_tif_tiles_dir = '%s/valid_tif_tiles' % data_root

#******************************* 标注样本准备涉及的参数 *************************
# 训练标注，shapefile格式，所在的目录
overlay_dir = '%s/overlay' % data_root

# This configure should not be touch!!!
# because label_color directory is created by another program!!!
# If you change this, change config.json too!!!
# 标注切割后所在的目录（rgb）
overlay_tiles_dir = '%s/labels_color' % data_root
# 过滤无效标注后的目录（rgb）
valid_overlay_tiles_dir = '%s/valid_labels_color' % data_root
# rgb标注转换为灰度标注的目录
labels_dir = '%s/labels' % data_root

#********************************* 训练样本输出的参数 ***********************
# 训练集合测试集文件分布
train_txt = '%s/train.txt' % (data_root)
test_txt = '%s/test.txt' % (data_root)

# 发布训练样本的目录
deploy_dir = 'deploy-sanxia'

#********************************  测试时需要的参数 ***************************
# 模型所在目录
model_directory = '%s/models/inference' % data_root
# 训练模型
train_model = '%s/models/segnet_train.prototxt' % data_root
# 测试模型
test_model = '%s/models/segnet_inference.prototxt' % data_root
# 分类权重
weight_file = '%s/models/weights.txt' % data_root

# 测试数据的输出目录
test_img_dir = '%s/models/img' % data_root
test_gt_dir = '%s/models/gt' % data_root
test_pd_dir = '%s/models/pd' % data_root

#****************************** cloud configuration *********************
cloud_dir = '%s/cloud' % data_root
cloud_tiles_dir = '%s/cloud_tiles' % data_root
valid_cloud_tiles_dir = '%s/valid_cloud_tiles' % data_root




