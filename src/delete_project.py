import shutil
import os
import sys
import json
from config import DeepPlanetConfig


def log(file_handle, message):
    current_time = datetime.datetime.now()
    flog.write('[%s] %s\n' % (current_time.strftime('%Y-%m-%d %H:%M:%S'), message))
    flog.flush()

def parseOptions(config_file):
    with open(config_file) as json_data:
        d = json.load(json_data)
        return d

if __name__ == '__main__':
    # Parse command line options
    if len(sys.argv) < 2:
        print('need config file!!!\n')
        exit()

    config_cmd = parseOptions(sys.argv[1])
    config = DeepPlanetConfig()
    if not config.Initialize(config_cmd):
        print('initialize fail! exist...')
        exit()

    if os.path.exists(config.deploy_dir):
        shutil.rmtree(config.deploy_dir)

    files = os.listdir(config.data_root)
    for file in files:
        file_path = os.path.join(config.data_root, file)
        if os.path.isdir(file_path):
            if file_path != config.src_tifs and file_path != config.overlay_dir:
                shutil.rmtree(file_path)
        if os.path.isfile(file_path):
            os.unlink(file_path)