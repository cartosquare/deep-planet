import math

class OverlapMercatorTile(object):
    def __init__(self, overlap=0, tileSize=256):
        self.tileSize = tileSize
        self.overlap = overlap        
        self.actualTileSize = self.tileSize - self.overlap
        self.initialResolution = 2 * math.pi * 6378137 / self.tileSize
        # 156543.03392804062 for tileSize 256 pixels
        self.originShift = 2 * math.pi * 6378137 / 2.0
		# 20037508.342789244

    def Resolution(self, zoom ):
		"Resolution (meters/pixel) for given zoom level (measured at Equator)"
		
		# return (2 * math.pi * 6378137) / (self.tileSize * 2**zoom)
		return self.initialResolution / (2**zoom)

    
    def MetersToTile(self, mx, my, zoom):
		"Returns tile for given mercator coordinates"
		
		px, py = self.MetersToPixels( mx, my, zoom)
		return self.PixelsToTile( px, py)

    def MetersToPixels(self, mx, my, zoom):
		"Converts EPSG:900913 to pyramid pixel coordinates in given zoom level"
				
		res = self.Resolution( zoom )
		px = (mx + self.originShift) / res
		py = (self.originShift - my) / res
		return px, py

    
    def PixelsToTile(self, px, py):
		"Returns a tile covering region in given pixel coordinates"

		tx = int( math.ceil( px / float(self.actualTileSize) ) - 1 )
		ty = int( math.ceil( py / float(self.actualTileSize) ) - 1 )
		return tx, ty


    def PixelsToMeters(self, px, py, zoom):
		"Converts pixel coordinates in given zoom level of pyramid to EPSG:900913"

		res = self.Resolution( zoom )
		mx = px * res - self.originShift
		my = self.originShift - py * res
		return mx, my


    def TileBounds(self, tx, ty, zoom):
		"Returns bounds of the given tile in EPSG:900913 coordinates"
		
		minx, maxy = self.PixelsToMeters(tx * self.actualTileSize, ty * self.actualTileSize, zoom)
		maxx, miny = self.PixelsToMeters((tx+1) * self.actualTileSize, (ty+1) * self.actualTileSize, zoom)

        # overlap effect
		offset = self.Resolution( zoom ) * self.overlap
		maxx = maxx + offset
		miny = miny - offset
		return ( minx, miny, maxx, maxy )

    