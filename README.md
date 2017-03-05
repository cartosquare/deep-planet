# deep-planet


## 一、影像样本准备
### s0. 下载影像到根目录下的tifs文件夹

### s1. 影像重投影到EPSG:3857坐标系
可以使用下面的脚本进行重投影。注意，可能需要根据你的数据修改 s_src 和 srcnodata 这两个参数
```bash
#!/bin/bash

for file in tifs/*.tif
do 
    echo processing_$file

    # this is right
    gdalwarp -s_srs EPSG:32649 -t_srs EPSG:3857 -r bilinear -srcnodata 0 -dstnodata 0 $file proj_$file
done
```

### s2. 建立金字塔
```python
$ python build_overview.py
```

### s3. 合并影像
```
$ gdalbuildvrt merge.vrt proj_tifs/*.tif
```
### s4. 切割影像
``` bash
#!/bin/bash

out='tif_tiles'
src='merge.vrt'

# world extent
worldMinx=11779924.71 
worldMiny=3315613.19
worldMaxx=12429394.15
worldMaxy=3728152.58

python dem2tiles.py ${src} ${out} 15 $worldMinx $worldMiny $worldMaxx $worldMaxy
```
注意修改影像范围和切割级别。

### s5. 拷贝有效的影像
拷贝没有nodata的影像作为训练样本
```
$ python raster_s5_copy_valid_tiles.py tif_tiles train
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
$ python label_s3_color_to_gray.py labels_color_sub labels
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