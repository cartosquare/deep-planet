#!/bin/bash

exe_name=$1
echo $exe_name
pyinstaller --noconfirm --upx-dir=/home/atlasxu/workspace/upx-3.93-amd64_linux spec/${exe_name}.spec
