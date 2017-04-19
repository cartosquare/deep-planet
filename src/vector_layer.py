# -*- coding: utf-8 -*-

"""
/***************************************************************************
 vector_layer
                                 vector layer
 operation about vector layers
                              -------------------
        begin                : 2016-11-4
        copyright            : (C) 2016 by GeoHey
        email                : xux@geohey.com
 ***************************************************************************/
"""

import os
import sys
import json
from osgeo import ogr


class VectorLayer:
    """VectorLayer Class"""
    def __init__(self):
        self.success = False

    def __del__(self):
        # clean
        self.datasource.Destroy()

    def open(self, src, ilayer, format, filter=None):
        # open vector layer
        self.driver = ogr.GetDriverByName(format)
        if self.driver is None:
            print "%s driver not available.\n" % format
            self.success = False
            return self.success

        # open data file read-only
        self.datasource = self.driver.Open(src, 0)
        if self.datasource is None:
            print 'could not open %s' % (src)
            self.success = False
            return self.success

        self.layer = self.datasource.GetLayer(ilayer)
        if filter is not None:
            self.layer.SetAttributeFilter(filter)

        self.feature_count = self.layer.GetFeatureCount()
        print "number of features in %s: %d" % (os.path.basename(src), self.feature_count)

        self.name = self.layer.GetName()

        # fetch layer extent
        self.extent = self.layer.GetExtent()
        print "layer[%s] extent minx: %f, maxx: %f, miny: %f, maxy: %f" % (self.name, self.extent[0], self.extent[1], self.extent[2], self.extent[3])

        self.success = True
        return self.success

    def spatialQuery(self, extent):
        if not self.success:
            print('layer is not opened correctly')
            return None

        minx = extent[0]
        miny = extent[1]
        maxx = extent[2]
        maxy = extent[3]

        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(minx, miny)
        ring.AddPoint(maxx, miny)
        ring.AddPoint(maxx, maxy)
        ring.AddPoint(minx, maxy)
        ring.AddPoint(minx, miny)
        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(ring)
        
        self.layer.SetSpatialFilter(None)
        self.layer.SetSpatialFilter(poly)
        return self.layer
    
    def feature_count(self):
        return self.layer.GetFeatureCount()