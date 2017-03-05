#!/bin/bash

out='tif_tiles'
src='merge.vrt'

# world extent
worldMinx=11779924.71 
worldMiny=3315613.19
worldMaxx=12429394.15
worldMaxy=3728152.58

python dem2tiles.py ${src} ${out} 15 $worldMinx $worldMiny $worldMaxx $worldMaxy

