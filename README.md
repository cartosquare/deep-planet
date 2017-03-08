# deep-planet
影像分割涉及到的样本准备、训练、精度评价工具。特点
* 支持多波段数据训练
* 支持将影像转换为图片训练（消除不同传感器DN值范围不同影响）


## 一、影像样本准备
下载影像到 raw_tifs 下
### s0. 提取需要的波段
需要在config.py中指定需要提取哪些波段。如果要使用所有波段，可以直接跳过这一步，直接把影像拷贝到tifs目录下即可。
```
python raster_s0_fetch_band.py
```

### s1. 影像重投影到EPSG:3857坐标系。
需要在config.py中指定源数据的坐标系和源数据的nodata值。
```
python raster_s1_reproj.py
```

### s2. 图片编码转换成 jpeg encoding(optional, if use tif image type)
```
python raster_s1_reproj.py
```

### s2. 建立金字塔(optional，better than not)
```
$ python raster_s2_build_overview.py
```

### s3. 合并影像
```
$ python raster_s3_build_vrt.py
```

### s4. 切割影像
``` 
python raster_s4_tiler.py
```
注意在config文件中修改影像范围和切割级别。

### s5. 拷贝有效的影像
拷贝没有nodata的影像作为训练样本
```
$ python raster_s5_copy_valid_tiles.py
```

## 二、标注样本准备
### s0. 提取标注shapefile文件放入landuse文件夹内。需要有Class_name字段表明要素的类别

### s1. 配置label类别和颜色
```
node label_s1_configure_labels.js
```
注意需要调整文件里面的类别名称和颜色

### s2. 生成标注样本
修改config.json里面的标注生成范围
```
$ mkdir labels_color
$ ./tiler config.json
```

### s3. 根据影像样本过滤出对应的标注样本
```
$ python label_s2_copy_labels.py
```


### s3. 标注样本转为灰度图
```
$ python label_s3_color_to_gray.py
```

## 三、云处理（可选）
### s0. 生成云掩模文件，放入cloud文件夹
### s1. 生成包含云的瓦片
```
$ cd cloud
$ mkdir cloud_tiles
$ ./tiler config.json
```
### s2. 过滤出有效的云瓦片
```bash
$ python cloud_s2_filter_valid.py
```

### s3. 移除包含云的训练样本
```
$ python cloud_s3_remove.py
```

## 四、生成训练和测试样本集
```
$ python split_train_test.py train labels train.txt labels.txt
```

## 五、计算标注的权重
```
$ python calculate_class_weighting.py labels
```

## 六、训练
```
$ ./caffe-segnet/build/tools/caffe train -gpu 0 -solver models/segnet_solver.prototxt
```
或
```
$ ./caffe-segnet/build/tools/caffe train -gpu 0 -solver models/segnet_solver.prototxt  -weights VGG_ILSVRC_16_layers.caffemodel
```

## 七、生成测试网络
```
$ python posttrain_scripts/compute_bn_statistics.py models/segnet_train.prototxt models/Training/envnet_iter_40000.caffemodel models/Inference
```

## 八、精度评价
在octave执行
```
compute_test_results
```