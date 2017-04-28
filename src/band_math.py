# -*- coding: utf-8 -*-
import os
import sys
import numpy as np

SCALE = 10000
def NDVI(nir, red):
    mask = np.greater(red + nir, 0)
    ndvi = np.choose(mask, (0, (nir - red) / (nir + red)))
    return (ndvi * SCALE).astype(np.uint16)

def NDWI(nir, green):
    mask = np.greater(green + nir, 0)
    ndwi = np.choose(mask, (0, (green - nir) / (nir + green)))
    return (ndwi * SCALE).astype(np.uint16)