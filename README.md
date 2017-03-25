# deep-planet
影像分割工具集。特点
* 支持多波段数据训练
* 支持将影像转换为图片训练（消除不同传感器DN值范围不同影响）

## Dependencies
* gdal
* skimage
* progressbar
* mapnik

## Usage


## 成果
## 湛江市道路分割
### rapideye卫星 rgb波段 tif
Global acc = 0.98796 Class average acc = 0.72592 Mean Int over Union = 0.64794

## 北京市道路分割
### rapideye卫星 rgb波段 缩放png
Global acc = 0.98006 Class average acc = 0.83417 Mean Int over Union = 0.6132

## 生态分割
### 高分二号卫星 4 3 2假彩色合成 缩放png
Global acc = 0.781321, Class average acc = 0.913746, Mean Int over Union = 0.748480

## TODO
* 支持指定多个tif源
* 添加波段计算图层，如NDVI层等

## Performance
### under 31 classes
test:
predict:
evaluate: 184 images/min