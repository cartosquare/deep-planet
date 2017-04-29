# -*- coding: utf-8 -*-
import os
import sys
import numpy as np

class BandMath:
    """BandMath Class"""
    def __init__(self):
        self.SCALE = 10000

    def compute(self, band_method, band_list):
        if band_method == 'NDVI':
            return self.NDVI(band_list[0], band_list[1])
        if band_method == 'NDWI':
            return self.NDWI(band_list[0], band_list[1])


    def NDVI(self, nir, red):
        mask = np.greater(red + nir, 0)
        ndvi = np.choose(mask, (0, (nir - red) / (nir + red)))
        return (ndvi * self.SCALE).astype(np.uint16)

    def NDWI(self, nir, green):
        mask = np.greater(green + nir, 0)
        ndwi = np.choose(mask, (0, (green - nir) / (nir + green)))
        return (ndwi * self.SCALE).astype(np.uint16)