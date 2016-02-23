#!/bin/bash

datadir=data
modelname=model
iter=1

function usage {
    echo "Parsing helper"
    echo
	echo "usage: $0 [DATADIR] [--name NAME] [--model|-m PATH] [--iter N] [--skip] [--plain] [[--input] FILE] [[--output|-o] FILE] [--] [options to amr_parsing.py...]"
    echo
	echo "--name NAME   choose alternative model name inside DATADIR (default: model)"
	echo "--iter N      select model of Nth iteration (default: $iter)"
	echo "--model PATH  where to save model file (default: DATADIR/model-iter<i>.m.{bz2,gz})"
	echo "--input FILE  specify input filename to parse (default: test inside DATADIR)"
	echo "--output FILE specify parsed output filename (default: test.parsed inside DATADIR)"
	echo "--plain       expect input file in plain format when input set explicitly (sentence per line)"
	echo "--skip        do not run post-process step"
	echo
	echo "For list of amr_parsing.py options see:"
	echo "$ `dirname $0`/amr_parsing.py --help"
	echo
	echo "Default data/model directory: $datadir"
	echo
}

for arg in $@; do
    if [ "$arg" == "--help" ] || [ "$arg" == "-h" ]; then
        usage
        exit 0
    fi
done

default_datadir=1
skip=0
plain=0
reparse=1

while [ $# -gt 0 ]; do
	if [ "$1" == "--" ]; then
		shift
		break
    elif [ "$1" == "--model" ] || [ "$1" == "-m" ]; then
        shift
		model="$1"
        shift
    elif [ "$1" == "--name" ]; then
        shift
		modelname="$1"
		output_tag=".$1"
        shift
    elif [ "$1" == "--iter" ] || [ "$1" == "-i" ]; then
        shift
		iter=$1
        shift
    elif [ "$1" == "--plain" ]; then
        shift
		plain=1
    elif [ "$1" == "--skip" ]; then
        shift
		skip=1
    elif [ "$1" == "--no-reparse" ]; then
        shift
		reparse=0
    elif [ "$1" == "--input" ]; then
        shift
		input="$1"
        shift
    elif [ "$1" == "--output" ] || [ "$1" == "-o" ]; then
        shift
		output="$1"
        shift
	elif [ -d "$1" ] && [ $default_datadir -eq 1 ]; then
		default_datadir=0
		datadir="$1"
		shift
	elif [ -f "$1" ] && [ "$input" == "" ]; then
		input="$1"
		shift
	elif [ ! -d "$1" ] && [ "$input" != "" ] && [ "$output" == "" ]; then
		output="$1"
		shift
	else
		echo "unknown argument: $1"
		exit 1
	fi
done

if [ "$input" == "" ]; then
	input="$datadir/test"
	amrfmt="--amrfmt"
elif [ $plain -ne 1 ]; then
	amrfmt="--amrfmt"
elif [ $plain -eq 1 ]; then
	amrfmt=
fi

if [ "$output" == "" ]; then
	output="$input$output_tag.parsed"
fi

if [ "$model" == "" ]; then
	model="$datadir/$modelname"
	# check if model file exists 
	if [ ! -f "$model" ]; then
		if [ -f "$model.m.bz2" ]; then
			model="$model.m.bz2"
		elif [ -f "$model.m.gz" ]; then
			model="$model.m.gz"
		elif [ -f "$model-iter$iter.m.bz2" ]; then
			model="$model-iter$iter.m.bz2"
		elif [ -f "$model-iter$iter.m.gz" ]; then
			model="$model-iter$iter.m.gz"
		else
			# model file not found
			model=
		fi
	fi
fi

if [ "$model" == "" ]; then
	echo "error: specify valid model"
	exit 1
fi

if [ $reparse -eq 1 ] || [ ! -f "$output" ]; then
	echo "Executing:"
	echo "`dirname $0`/amr_parsing.py --model \"$model\" --mode parse $amrfmt \"$input\" -o \"$output\" -W $@"
	echo
	time `dirname $0`/amr_parsing.py --model "$model" --mode parse $amrfmt "$input" -o "$output" -W $@
	if [ $? -ne 0 ]; then
		echo "Error parsing"
		exit 1
	fi
fi

# Post-processing
if [ $skip -ne 1 ]; then
	final_output="$output.final"
	echo -n "Post-processing $output to $final_output ..."
	`dirname $0`/postprocess.py "$output" > "$final_output" 2> /dev/null
	if [ $? -eq 0 ]; then
		echo "ok"
	else
		echo "error, to see error, try executing manually:"
		echo "$ `dirname $0`/postprocess.py \"$output\" > \"$final_output\""
	fi
fi
