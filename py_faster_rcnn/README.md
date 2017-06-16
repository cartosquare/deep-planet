### Disclaimer
方法参考了https://github.com/rbgirshick/py-faster-rcnn的代码
以及http://blog.csdn.net/sinat_30071459/article/details/51332084的教程。

1.训练烟囱探测样本：
删除output文件夹，py-faster-rcnn/data/cache中的文件和py-faster-rcnn/data/VOCdevkit2007/annotations_cache中的文件。
执行./experiments/scripts/faster_rcnn_alt_opt.sh 0 VGG16 pascal_voc开始烟囱探测模型的训练。
将训练得到的py-faster-rcnn\output\faster_rcnn_alt_opt\***_trainval中的caffemodel拷贝至py-faster-rcnn\data\faster_rcnn_models。
执行python tools/demo.py
得到的标记结果存放于chimney文件夹下。
2.训练自己的数据集：
在data/VOCdevkit2007/VOC2007文件夹下：将图片存放在JPEGImages文件夹中，将XML标签文件存放于Annotations文件夹中，在ImageSets/Main文件夹中配置训练，验证和测试文件。
按http://blog.csdn.net/sinat_30071459/article/details/51332084中的教程配置网络结构和其他参数，训练自己的网络。