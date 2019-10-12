#!/bin/bash
echo "===================== Start ! ====================="

killProcess(){
    pid=$(ps x | grep $1 | grep -v grep | awk '{print $1}')
    kill -9 $pid
}


nohup python -u repoManager.py > ./log/repoManager.log 2>&1 &
if [ $? -eq 0 ]; then
    echo "repoManager has been started !"
else
    echo "Failed !"
    exit
fi


nohup python -u addCommit.py > ./log/addCommit.log 2>&1 &
if [ $? -eq 0 ]; then
    echo "addCommit has been started !"
else
    echo "Failed !"
    killProcess "repoManager.py"
    exit
fi


nohup python -u updateCommit.py > ./log/updateCommit.log 2>&1 &
if [ $? -eq 0 ]; then
    echo "updateCommit has been started !"
else
    echo "Failed !"
    killProcess "repoManager.py"
    killProcess "addCommit.py"
    exit
fi

nohup python -u bufferManager.py > ./log/bufferManager.log 2>&1 &
if [ $? -eq 0 ]; then
    echo "bufferManager has been started !"
else
    echo "Failed !"
    killProcess "repoManager.py"
    killProcess "addCommit.py"
    killProcess "updateCommit.py"
    exit
fi