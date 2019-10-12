#!/bin/bash
echo "===================== Stop ! ====================="

killProcess(){
    pid=$(ps x | grep $1 | grep -v grep | awk '{print $1}')
    echo $pid
    kill -9 $pid
}

killProcess "repoManager.py"
killProcess "addCommit.py"
killProcess "updateCommit.py"
killProcess "bufferManager.py"

echo "Stop Completed !"