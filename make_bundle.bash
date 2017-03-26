#!/bin/bash

if [ $# -ne 1 ]; then
    for file in spec/*
    do
        if [[ -f $file ]]; then
            echo 'bundling tool from file: '$file
            pyinstaller --noconfirm --upx-dir=lib/upx-3.93-amd64_linux $file
        fi
    done
else
    exe_name=$1
    echo 'bundling tool: '$exe_name
    pyinstaller --noconfirm --upx-dir=lib/upx-3.93-amd64_linux spec/${exe_name}.spec
fi