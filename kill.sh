#!/bin/bash

args="$@"
if [ $# -le 0 ]; then
	args="python ./rest.py"
fi

# ps -u $USER -o pid,args | grep "${args[@]}"
PS=`ps -u $USER -o pid,args`
PS=`echo "$PS" | grep "${args[@]}"`
echo "$PS"
# PIDS=`ps -u $USER -o pid,args | grep $args | sed 's/^[ ]//g' | cut -d ' ' -f 1`
PIDS=`echo "$PS" | sed 's/^[ ]//g' | cut -d ' ' -f 1`

read -p "Kill processes shown above [y/N] ? " -n 1 -r
echo    # (optional) move to a new line
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
	echo "Won't kill"
	exit 1
fi
echo "Killing $PIDS"

kill -9 $PIDS
