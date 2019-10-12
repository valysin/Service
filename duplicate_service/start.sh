#!/bin/bash

nohup python -u ss.py > ./log/ss.log 2>&1 &
if [ $? -eq 0 ]; then
    echo "ss has been started !"
else
    echo "Failed !"
    exit
fi