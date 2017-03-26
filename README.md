# deep-planet
影像分割工具集。特点
* 支持多波段数据训练
* 支持将影像转换为图片训练（消除不同传感器DN值范围不同影响）

## Dependencies
* caffe-segnet
```
sudo apt-get install libprotobuf-dev libleveldb-dev libsnappy-dev libopencv-dev libhdf5-serial-dev protobuf-compiler
sudo apt-get install --no-install-recommends libboost-all-dev
sudo apt-get install libatlas-base-dev
sudo apt-get install python-dev
sudo apt-get install libgflags-dev libgoogle-glog-dev liblmdb-dev
sudo apt-get install python-numpy
sudo apt-get install libgdal-dev gdal-bin python-gdal
```

### build
```
cp Makefile.config.example Makefile.config
make -j 8
make pycaffe
```

### common problems
#### fix compile flag
```
-NVCCFLAGS += -ccbin=$(CXX) -Xcompiler -fPIC $(COMMON_FLAGS)

+NVCCFLAGS += -D_FORCE_INLINES -ccbin=$(CXX) -Xcompiler -fPIC $(COMMON_FLAGS)
```

#### can't find hdf5.h

modify INCLUDE_DIRS in Makefile.config
```
INCLUDE_DIRS := $(PYTHON_INCLUDE) /usr/local/include /usr/include/hdf5/serial
```

create symlinks as instructed here

```
cd /usr/lib/x86_64-linux-gnu
sudo ln -s libhdf5_serial.so.8.0.2 libhdf5.so
sudo ln -s libhdf5_serial_hl.so.8.0.2 libhdf5_hl.so
```

### can't find gdal_priv.h
modify INCLUDE_DIRS in Makefile.config
```
INCLUDE_DIRS := $(PYTHON_INCLUDE) /usr/local/include /usr/include/hdf5/serial /usr/include/gdal
```


### other dependencies
* pip
```
sudo apt-get install python-pip
```

* skimage
```
pip install -U scikit-image
```

* progressbar
```
pip install progressbar
```

* mapnik
```
sudo apt-get install python-mapnik
```

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

## How to Bundle program?
### dependencies
* pyinstaller
```
pip install pyinstaller
```
* [upx](https://github.com/upx/upx/releases/tag/v3.93)
* Crypto

## bundle command
```
pyinstaller --noconfirm --upx-dir=/home/atlasxu/workspace/upx-3.93-amd64_linux spec/pretrain.spec
```

### fix mapnik path problem
change file /usr/lib/python2.7/dist-packages/mapnik/paths.py to following:

```
import os
import sys
import os.path

mapniklibpath = '/usr/lib/mapnik/3.0'
mapniklibpath = os.path.normpath(mapniklibpath)
if getattr(sys, 'frozen', False):
        # we are running in a bundle
        bundle_dir = sys._MEIPASS
        inputpluginspath = os.path.join(bundle_dir,'share/mapnik/input')
else:
        inputpluginspath = os.path.join(mapniklibpath,'input')

fontscollectionpath = os.path.normpath('/usr/share/fonts')
__all__ = [mapniklibpath,inputpluginspath,fontscollectionpath]
```

