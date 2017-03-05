import os;
import sys;
import math;
from subprocess import call;

if __name__=='__main__': 
    if len(sys.argv) < 7:
        print "Need Parameters, list below IN ORDER: ";
        print "1th parameter: Source files that need to be tiled";
        print "2th parameter: Directory which will contains the generated tiles";
        print "3th parameter: which level to process";
        print "4th parameter: min x coordinate";
        print "5th parameter: min y coordinate";
        print "6th parameter: max x coordinate";
        print "7th parameter: max y coordidate";
        exit(0);
    
    # Following parameters will be passed in 
    src = sys.argv[1];
    out = sys.argv[2]
    print "src: ", src;
    print "out: ", out;
    
    # zoom level
    level = int(sys.argv[3]);
    print "level:", level;
    
    # tile extent
    minx = float(sys.argv[4]);
    miny = float(sys.argv[5]);
    maxx = float(sys.argv[6]);
    maxy = float(sys.argv[7]);
    print minx, miny, maxx, maxy;
      
    # mercator parameters
    worldOriginalx = -20037508.342787;
    worldOriginaly = 20037508.342787;

    # tile size
    tileSize = 256;
    
    # resolutions for each level
    zoomReses =[156543.033928,78271.516964,39135.758482,19567.879241,9783.9396205,4891.96981025,2445.984905125,
1222.9924525625,611.49622628125,305.748113140625,152.8740565703125,76.43702828515625,38.21851414257813,
19.10925707128906,9.55462853564453,4.777314267822266,2.388657133911133,1.194328566955567,0.597164283477783,0.298582141738892,0.14929107086945,0.07464553543473];
    
    
    tileExtent = tileSize * zoomReses[level];
    minBundlex = int((minx - worldOriginalx) / tileExtent);
    minBundley = int((worldOriginaly - maxy) / tileExtent);

    maxBundlex = int((maxx - worldOriginalx) / tileExtent);
    maxBundley = int((worldOriginaly - miny) / tileExtent);

    totalBundles = (maxBundlex - minBundlex + 1) * (maxBundley - minBundley + 1);
    print "[Normal] total tiles #%s" % totalBundles;
    
    step = totalBundles / 50 + 1;  
    count = 0;
    maxIdx = 2 ** level - 1;
    print "Max Idx: ", maxIdx;
    sys.stdout.flush();

    for i in range(minBundlex, maxBundlex + 1):
        if i > maxIdx:
            continue;
        for j in range(minBundley, maxBundley + 1):
            if j > maxIdx:
                continue;
                
            tilepath = os.path.join(out, "%s" % (str(level) + "_" + str(i) + "_" + str(j) + ".tif"))
           
            tileMinx = worldOriginalx + i * tileExtent;
            tileMaxx = tileMinx + tileExtent;
            tileMaxy = worldOriginaly - j * tileExtent;
            tileMiny = tileMaxy - tileExtent;
        
            command = "gdalwarp -te %s %s %s %s -ts 256 256 -r near -multi -q %s %s" % (format(tileMinx, '.10f'), format(tileMiny, '.10f'), format(tileMaxx, '.10f'), format(tileMaxy, '.10f'), src, tilepath);
            
            print command;
            os.system(command);
            
            #call(["gdalwarp", "-s_srs", "EPSG:4326", "-t_srs", "EPSG:3857", "-te", format(tileMinx, '.10f'), format(tileMiny, '.10f'), format(tileMaxx, '.10f'), format(tileMaxy, '.10f'), "-ts", "256", "256", "-overwrite", "-r", "near", "-multi", "-q", src, tilepath]);

            count += 1
            # process bar
            if (count % step == 0):
                print "[Normal]level %s current processed: %.2f%%" % (str(level), (count / float(totalBundles) * 100));
		sys.stdout.flush();
                
    
