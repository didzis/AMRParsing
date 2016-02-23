#!/bin/bash

datadir=data
modelname=model

function usage {
    echo "Training helper"
    echo
    echo "usage: $0 [--dev|-d] [DATADIR] [--name NAME] [--model|-m <model path>] [--] [extra options to amr_parsing.py...]"
    echo
	echo "--dev         use development set <data dir>/dev"
	echo "--model PATH  where to save model file (default: <data/model dir>/model-iter<i>.m.{bz2,gz})"
	echo "--name NAME   specify model name inside DATADIR"
	echo
	echo "Some amr_parsing.py options:"
	echo "-iter N       number of iterations to train"
	echo
	echo "For more amr_parsing.py options see:"
	echo "$ `dirname $0`/amr_parsing.py --help"
	echo
	echo "Default DATADIR: $datadir"
	echo
}

for arg in $@; do
    if [ "$arg" == "--help" ] || [ "$arg" == "-h" ]; then
        usage
        exit 0
    fi
done

extra_amr_parsing_options=()
default_datadir=1

while [ $# -gt 0 ]; do
	if [ "$1" == "--" ]; then
		shift
		break
    elif [ "$1" == "--dev" ] || [ "$1" == "-d" ]; then
        shift
		dev=dev
    elif [ "$1" == "--model" ] || [ "$1" == "-m" ]; then
        shift
		model="$1"
        shift
    elif [ "$1" == "--name" ] || [ "$1" == "-m" ]; then
        shift
		modelname="$1"
        shift
	elif [ -d "$1" ] && [ $default_datadir -eq 1 ]; then
		default_datadir=0
		datadir="$1"
		shift
	else
		extra_amr_parsing_options=(${extra_amr_parsing_options[@]} $1)
		shift
	fi
done

if [ "$dev" != "" ]; then
	devopt="--dev $datadir/$dev"	# no quotes for now
fi

if [ "$model" == "" ]; then
	model="$datadir/$modelname"
fi

echo "Executing:"
echo "`dirname $0`/amr_parsing.py --model \"$model\" --mode train --amrfmt $devopt \"$datadir/train\" -W ${extra_amr_parsing_options[@]} $@"
echo
time `dirname $0`/amr_parsing.py --model "$model" --mode train --amrfmt $devopt "$datadir/train" -W ${extra_amr_parsing_options[@]} $@
