#!/bin/bash

for file in tifs/*.tif
do 
    echo processing_$file

    # this is right
    gdalwarp -s_srs EPSG:32649 -t_srs EPSG:3857 -r bilinear -srcnodata 0 -dstnodata 0 $file proj_$file
done
