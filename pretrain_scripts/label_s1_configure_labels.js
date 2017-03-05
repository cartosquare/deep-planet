var fs = require('fs');
var def = {
    "data_sources": {
        "data": {
            "source": "landuse/",
            "type": "shapefile"
        }
    },
    "background_color": [0, 0, 0],
    "background_opacity": 1.0,
    "layers": {
    }
}

//var layers = ['badong_2014', 'wanzhou_2014', 'banan_2014', 'wulong_2014', 'changshou_2014', 'wushan_2014', 'chongqing_2014', 'wuxi_2014', 'fengdu_2014', 'xingshan_2014', 'fengjie_2014', 'yiling_2014', 'fuling_2014', 'yubei_2014', 'jiangjin_2014', 'yunyang_2014', 'kaixian_2014', 'zhongxian_2014', 'shizhu_2014', 'zigui_2014']

var layers = ['BaDong_2012', 'WanZhou_2012', 'BaNan_2012', 'WuLong_2012', 'ChangShou_2012', 'WuShan_2012', 'ChongQing_2012', 'WuXi_2012', 'FengDu_2012', 'XingShan_2012', 'FengJie_2012', 'YiLing_2012', 'FuLing_2012', 'YuBei_2012', 'JiangJin_2012', 'YunYang_2012', 'KaiXIan_2012', 'ZhongXian_2012', 'ShiZhu_2012', 'ZiGui_2012']

var classes = [{
    'name': '常绿阔叶林', 'color': [146, 211, 48]
}, {
    'name': '常绿针叶林', 'color': [143, 144, 239]
}, {
    'name': '混交林', 'color': [225, 137, 77]
}, {
    'name': '落叶阔叶林', 'color': [26, 223, 220]
}, {
    'name': '落叶针叶林', 'color': [221, 122, 183]
}, {
    'name': '常绿灌木林', 'color': [233, 111, 111]
}, {
    'name': '落叶灌木林', 'color': [208, 24, 61]
}, {
    'name': '草地', 'color': [114, 202, 132]
}, {
    'name': '城市草本绿地', 'color': [224, 203, 118]
}, {
    'name': '旱地', 'color': [138, 94, 208]
}, {
    'name': '水田', 'color': [117, 168, 240]
}, {
    'name': '灌木种植园', 'color': [222, 57, 16]
}, {
    'name': '苗圃', 'color': [152, 80, 204]
}, {
    'name': '乔木种植园', 'color': [216, 173, 108]
}, {
    'name': '采矿场地', 'color': [84, 231, 48]
}, {
    'name': '城市居民地', 'color': [195, 226, 70]
}, {
    'name': '城市乔灌混合绿地', 'color': [148, 221, 99]
}, {
    'name': '城市乔木绿地', 'color': [210, 210, 105]
}, {
    'name': '独立工业和商业用地', 'color': [193, 33, 237]
}, {
    'name': '基础设施', 'color': [205, 78, 207]
}, {
    'name': '垃圾填埋场', 'color': [37, 75, 215]
}, {
    'name': '镇村居民地', 'color': [20, 223, 139]
}, {
    'name': '河流季节性水面', 'color': [217, 114, 198]
}, {
    'name': '湖泊', 'color': [145, 124, 99]
}, {
    'name': '坑塘', 'color': [71, 36, 225]
}, {
    'name': '水库', 'color': [15, 231, 185]
}, {
    'name': '水库季节性水面', 'color': [210, 23, 101]
}, {
    'name': '水生植被', 'color': [31, 148, 221]
}, {
    'name': '永久河流水面', 'color': [92, 220, 92]
}, {
    'name': '坚硬表面', 'color': [66, 240, 133]
}, {
    'name': '松散表面', 'color': [114, 209, 230]
}
]

console.log('#classes: ' + classes.length);
console.log('#layers: ' + layers.length);

for (var c = 0; c < classes.length; ++c) {
    for (var i = 0; i < layers.length; ++i) {
        layerObj = {
            "data_source": "data",
            "data_name": layers[i],
            "encode": "utf-8",
            "visible": "true",
            "rules": [
                {
                    "res_min": 0,
                    "res_max": 156544,
                    "symbol_type": "fill",
                    "data_filter": "Class_name=\"" + classes[c]['name'] + "\"",
                    "fill_color": classes[c]['color']
                }
            ]
        }

        def.layers[c + '_' + i] = layerObj;
    }
}

fs.writeFileSync('tile_color.json', JSON.stringify(def, null, 4));




